# APISIX + Argo CD: que cambiamos y por que

Este documento explica los cambios hechos en `basics/apisix-values.yaml`, que significa cada valor importante, como afecta el despliegue y como circula el trafico y la configuracion dentro del stack.

La idea es que te sirva como referencia para entender:

- que hace APISIX
- que hace el `apisix-ingress-controller`
- que hace Argo CD en este despliegue
- por que pasamos de `etcd` a `standalone`
- por que tambien limpiamos los defaults de `externalEtcd`
- por que eso impacta directamente en que la `ApisixRoute` de Argo funcione o no

## 1. Componentes del stack

En este escenario hay 3 piezas principales:

1. `APISIX`
   Es el gateway. Recibe el trafico HTTP externo y decide a que servicio interno lo manda.

2. `apisix-ingress-controller`
   Es el controlador. Mira recursos Kubernetes como `ApisixRoute` y traduce esa intencion a configuracion real para APISIX.

3. `Argo CD`
   Es la aplicacion que queres exponer por web. Vive en su namespace `argocd` y tiene su propio `Service` interno.

## 2. Arquitectura general

### Trafico de usuario

```text
Usuario/Navegador
        |
        v
DNS: argocd.internal.example.com
        |
        v
AWS NLB (Service apisix-gateway)
        |
        v
APISIX Gateway
        |
        v
Regla cargada desde ApisixRoute "argo-route"
        |
        v
Service argocd-server:80
        |
        v
Pods de argocd-server
```

### Flujo de configuracion

```text
Git / Argo CD
        |
        v
Resource: ApisixRoute (argo-route)
        |
        v
apisix-ingress-controller
        |
        v
GatewayProxy / Admin API
        |
        v
APISIX carga la ruta
        |
        v
La ruta queda disponible para trafico real
```

## 3. Problema que habia antes

El problema no era solamente el host o el puerto de Argo.

La causa de fondo era que el stack estaba mezclando dos modelos distintos de configuracion:

- APISIX estaba configurado para trabajar con `etcd`
- el `ingress-controller` estaba usando el flujo nuevo basado en `GatewayProxy` y `ADC`

Esa mezcla hizo que el controller intentara sincronizar rutas hacia un Admin API que no estaba respondiendo como el controller esperaba. El sintoma visible fue:

- `ApisixRoute` con `Accepted=False`
- logs del controller con `AxiosError: Request failed with status code 404`

Dicho simple:

- la ruta `argo-route` existia en Kubernetes
- el controller la leia
- pero no lograba transformarla correctamente en configuracion util dentro de APISIX

## 4. Que cambiamos en `apisix-values.yaml`

Estos son los cambios importantes.

### `service.type: LoadBalancer`

```yaml
service:
  type: LoadBalancer
```

#### Que significa

Le dice a Kubernetes que exponga el servicio principal de APISIX como un LoadBalancer.

#### Para que se usa

Es lo que hace que AWS cree el NLB y te entregue un hostname externo tipo:

```text
k8s-....elb.us-east-1.amazonaws.com
```

#### Impacto en el despliegue

- APISIX deja de ser solo interno al cluster
- ahora puede recibir trafico desde afuera
- DNS despues puede apuntar a ese hostname

### `apisix.deployment.mode: standalone`

```yaml
apisix:
  deployment:
    mode: standalone
```

#### Que significa

Le dice al chart que APISIX se despliegue en modo `standalone`.

#### Para que se usa

Es el modo alineado con el flujo nuevo del `apisix-ingress-controller`, donde el gateway deja de depender de `etcd` como fuente principal de configuracion.

#### Impacto en el despliegue

Hace que el chart renderice la configuracion del gateway para trabajar sin `etcd` en este escenario.

### `apisix.deployment.role: traditional`

```yaml
apisix:
  deployment:
    role: traditional
    role_traditional:
      config_provider: yaml
```

#### Que significa

Le dice a APISIX que actue como plano de datos.

#### Para que se usa

En el chart `2.11.2`, este valor es importante porque mantiene activo el Admin API de APISIX. El controller necesita ese Admin API para poder publicar rutas.

#### Impacto en el despliegue

Este fue el ajuste mas importante.

Antes:

```text
Ingress Controller -> intenta programar APISIX
APISIX -> no queda en el modo compatible correcto
Resultado -> incompatibilidad / 404 / route no aceptada
```

Despues:

```text
Ingress Controller -> programa APISIX en modo compatible
APISIX -> corre en standalone + traditional/yaml
Resultado esperado -> route aceptada
```

## 5. Por que deshabilitamos etcd

```yaml
etcd:
  enabled: false
```

#### Que significa

El chart deja de desplegar el subcomponente `etcd` dentro de esta app.

#### Para que se usa

Si APISIX corre en `standalone`, mantener `etcd` activo agrega complejidad y errores innecesarios.

#### Impacto en el despliegue

- menos componentes
- menos volumenes persistentes
- menos problemas de versionado y downgrade
- menos drift de Argo sobre `StatefulSet`, `PVC`, `Secret` asociados a `etcd`

#### Relacion con el problema real

`etcd` ya te habia quedado con problemas de version de datos y eso complico mucho la recuperacion. Al sacarlo de este flujo, simplificas el stack.

### `externalEtcd.user: ""` y `externalEtcd.host: []`

```yaml
externalEtcd:
  user: ""
  host: []
```

#### Que significa

Aunque `etcd.enabled: false`, el chart `2.11.2` sigue trayendo defaults para `externalEtcd`.

#### Para que se usa

Se usa para limpiar esos defaults y evitar que Helm siga generando restos de una configuracion de etcd externo.

#### Impacto en el despliegue

Sin este override, el chart podia seguir renderizando cosas como:

- `APISIX_ETCD_PASSWORD`
- `Secret etcd-apisix`
- referencias a autenticacion de etcd

Con este override, el render queda realmente alineado con standalone y deja de arrastrar configuracion que no queres usar.

## 6. Cambios del `ingress-controller`

### `ingress-controller.deployment`

```yaml
ingress-controller:
  deployment:
    replicas: 1
    resources:
      requests:
        cpu: 500m
        memory: 256Mi
      limits:
        cpu: 2
        memory: 512Mi
```

#### Que significa

Esto configura el deployment del `apisix-ingress-controller`, no el gateway APISIX.

#### Para que se usa

- `replicas`: cantidad de pods del controller
- `requests`: minimo reservado por scheduler
- `limits`: tope maximo de uso

#### Impacto en el despliegue

No afecta el trafico directo del usuario. Afecta estabilidad y capacidad del controlador para reconciliar rutas.

### `ingress-controller.autoscaling`

```yaml
autoscaling:
  enabled: true
  version: 2
  minReplicas: 1
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 70
```

#### Que significa

Activa un HPA para el `ingress-controller`.

#### Para que se usa

Permite que el controller escale segun carga.

#### Impacto en el despliegue

No cambia como enruta APISIX. Mejora la resiliencia del plano de control cuando hay mas reconciliaciones.

### `ingress-controller.apisix.adminService`

```yaml
apisix:
  adminService:
    name: apisix-admin
    namespace: ingress-apisix
    port: 9180
```

#### Que significa

Le dice al controller cual es el `Service` de APISIX que expone el Admin API.

#### Para que se usa

El controller necesita saber a donde hablar para programar rutas, upstreams, plugins, etc.

#### Impacto en el despliegue

Evita depender de direcciones hardcodeadas menos estables y alinea al controller con el servicio Kubernetes real.

### `ingress-controller.config.provider.type: apisix-standalone`

```yaml
config:
  provider:
    type: apisix-standalone
```

#### Que significa

Le dice al controller que use el flujo compatible con APISIX en modo `yaml` / standalone-like.

#### Para que se usa

Es la otra mitad del cambio. No basta con cambiar APISIX; el controller tambien tiene que hablar el mismo idioma operativo.

#### Impacto en el despliegue

Esto cambia como el controller traduce `ApisixRoute` y como empuja esa configuracion hacia APISIX.

### `ingress-controller.gatewayProxy`

```yaml
gatewayProxy:
  createDefault: true
  provider:
    type: ControlPlane
```

#### Que significa

Hace que el chart cree el `GatewayProxy` default.

#### Para que se usa

El `GatewayProxy` es la pieza que conecta el controller con APISIX.

#### Impacto en el despliegue

Sin esto, el controller puede estar vivo pero no saber donde programar la configuracion.

#### Nota importante sobre el chart `2.11.2`

En esta version del chart, el template del `GatewayProxy` toma el destino real desde:

- `ingress-controller.apisix.adminService.name`
- `ingress-controller.apisix.adminService.port`

O sea: en `2.11.2`, lo importante para el `GatewayProxy` es:

- `gatewayProxy.createDefault: true`
- `apisix.adminService` bien apuntado a `apisix-admin:9180`

## 7. Como queda el flujo despues del cambio

### Antes

```text
ApisixRoute -> ingress-controller
                        |
                        v
                intenta usar flujo nuevo
                        |
                        v
APISIX sigue esperando config por etcd
                        |
                        v
falla la sincronizacion
```

### Despues

```text
ApisixRoute -> ingress-controller
                        |
                        v
              usa provider apisix-standalone
                        |
                        v
GatewayProxy -> Service apisix-admin:9180
                        |
                        v
APISIX en `mode: standalone` + `role: traditional`
                        |
                        v
ruta aceptada y cargada
```

## 8. Como entra una request real

Supongamos que el usuario abre:

```text
http://argocd.internal.example.com/
```

La secuencia es:

1. el DNS resuelve `argocd.internal.example.com`
2. ese DNS apunta al hostname del NLB creado por `apisix-gateway`
3. el NLB manda el trafico al `Service` de APISIX
4. APISIX recibe el request con el header `Host: argocd.internal.example.com`
5. APISIX busca una ruta con ese host
6. si `argo-route` esta aceptada y cargada, reenvia al backend:

```text
Service argocd-server:80
```

7. el `argocd-server` responde al navegador

## 9. Por que el host correcto importa

La `ApisixRoute` que probaste hace match por:

```yaml
hosts:
  - argocd.internal.example.com
```

Eso significa que APISIX no enruta solo por IP o por path. Tambien necesita que el header `Host` coincida.

Por eso estas pruebas son distintas:

```bash
curl http://<NLB>
```

Eso puede no matchear la ruta.

En cambio:

```bash
curl -H 'Host: argocd.internal.example.com' http://<NLB>
```

Eso si prueba la ruta correcta.

## 10. Checks de verificacion despues del sync

Despues de sincronizar `apisix`, estos checks te dicen si el cambio funciono.

### Ver la app en Argo

```bash
kubectl get application -n argocd apisix
```

Esperado:

- `HEALTH` sano
- sin errores repetidos del controller

### Ver el estado de la ruta

```bash
kubectl get apisixroute -n argocd argo-route -o yaml
```

Esperado:

- `status.conditions`
- `type: Accepted`
- `status: "True"`

### Ver los pods principales

```bash
kubectl get pods -n ingress-apisix
```

Esperado:

- `apisix` en `Running`
- `apisix-ingress-controller` en `Running`
- sin `etcd` si quedo deshabilitado

### Ver el LB

```bash
kubectl get svc -n ingress-apisix apisix-gateway -o wide
```

Esperado:

- `EXTERNAL-IP`/hostname presente

### Probar la ruta desde afuera

```bash
curl -H 'Host: argocd.internal.example.com' http://<hostname-del-nlb>
```

## 11. Resumen ejecutivo

La decision principal que tomamos fue esta:

- dejar de mezclar `APISIX + etcd` con un `ingress-controller` que ya estaba operando con el flujo nuevo
- pasar APISIX a `apisix.deployment.mode: standalone`
- usar `apisix.deployment.role: traditional`
- usar `apisix.deployment.role_traditional.config_provider: yaml`
- deshabilitar `etcd`
- limpiar `externalEtcd`
- hacer que el controller use `apisix-standalone`

En otras palabras:

```text
antes: stack mezclado
despues: stack alineado
```

Y esa alineacion es la que deberia permitir que `argo-route` deje de fallar y empiece a publicarse correctamente.

## 12. Nota importante sobre el primer intento

Primero se intento usar este bloque:

```yaml
deployment:
  role: traditional
  role_traditional:
    config_provider: yaml
```

La idea conceptual era correcta, pero para este chart/version no era la ruta de values que el chart estaba consumiendo.

El efecto real fue:

- el chart siguio renderizando APISIX con `config_provider: etcd`
- el pod nuevo de APISIX cayo intentando hablar con `http://etcd.host:2379`

Despues se intento usar `role: data_plane`, pero ahi aparecio otro detalle del chart `2.11.2`:

- cuando `role: data_plane`, el chart deja de renderizar el bloque `admin`
- eso hace que el Admin API en `:9180` no levante
- el `ingress-controller` queda con `ECONNREFUSED` al intentar sincronizar

La correccion final fue mover la configuracion a la jerarquia real del chart, limpiar los defaults de etcd externo y mantener APISIX en standalone con Admin API activo:

```yaml
apisix:
  deployment:
    mode: standalone
    role: traditional
    role_traditional:
      config_provider: yaml

externalEtcd:
  user: ""
  host: []
```

Esto te lo dejo documentado porque es exactamente el tipo de detalle que despues cuesta explicar cuando uno vuelve a mirar el repo.
