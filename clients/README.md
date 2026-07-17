# Clients

Este directorio implementa un patrón **App of Apps** sobre ArgoCD donde cada entorno independiente se modela como un chart Helm bajo `clients/<cliente>/<ambiente>` o como un chart raíz especial como `clients/internal`. Cada entorno declara qué aplicaciones despliega y con qué valores, reutilizando los charts parametrizados del directorio [`/catalog`](../catalog).

---

## Estructura general

```
clients/
├── internal/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       └── applications.yaml
└── example-client/
    ├── dev/
    │   ├── Chart.yaml
    │   ├── values.yaml
    │   └── templates/
    │       └── applications.yaml
    └── qa/
        ├── Chart.yaml
        ├── values.yaml
        └── templates/
            └── applications.yaml
```

---

## Cómo funciona

### 1. Bootstrap — punto de entrada

Un objeto ArgoCD `Application` apunta a un chart bajo `clients/<cliente>/<ambiente>/` o a `clients/internal/`. ArgoCD renderiza ese chart y aplica los recursos resultantes al cluster.

Importante:

- la **app raíz** o **bootstrap app** siempre se crea en el Argo CD del cluster donde vive Argo
- por eso su `destination.server` debe ser `https://kubernetes.default.svc`
- y su `destination.namespace` debe ser `argocd`

Eso no significa que las apps hijas se desplieguen en `internal`.

Significa solo que:

- la app raíz crea objetos `Application` de Argo CD
- y esos objetos `Application` solo existen en el cluster donde corre Argo

Después, cada app hija puede desplegar en el cluster remoto que corresponda.

```yaml
# Ejemplo de bootstrap (aplicado manualmente una sola vez)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: example-client-dev-bootstrap
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/<your-org>/<your-repo>.git
    targetRevision: main
    path: clients/example-client/dev
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  project: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

En este ejemplo:

- la app raíz `example-client-dev-bootstrap` vive en Argo CD
- las apps hijas definidas en `clients/example-client/dev/values.yaml` pueden desplegar al cluster remoto `example-client-dev`

### 2. App of Apps — `clients/<cliente>/<ambiente>/`

El chart del entorno es un **generador de ArgoCD Applications**. Su único template (`templates/applications.yaml`) itera sobre la lista `applications` del `values.yaml` y produce un objeto `Application` por cada entrada.

```
clients/example-client/dev (Helm chart)
  └─ renderiza templates/applications.yaml
       └─ ArgoCD Application: example-client-dev-whoami → path: catalog/whoami
```

### 3. Catalog — charts reutilizables

Cada ArgoCD Application generada apunta a un chart en `/catalog`. Hay dos tipos:

| Tipo | Ejemplos | Descripción |
|------|----------|-------------|
| **Helm dependency** | `apisix`, `cert-manager`, `azure-workload-identity` | Envuelven un chart externo como subchart. ArgoCD descarga la dependencia y despliega directamente. |
| **Recursos K8s directos** | `argocd-projects`, `clusterissuers`, `certificates` | Templates que generan recursos Kubernetes (`AppProject`, `ClusterIssuer`, `Certificate`) sin dependencias externas. |

El flujo final es de **2 niveles** — no hay ArgoCD Applications intermedias:

```
clients/example-client/dev → ArgoCD App: whoami → catalog/whoami → despliega Deployment/Service/Namespace
```

---

## Configurar un cliente

Toda la configuración específica del entorno vive en `values.yaml`. Cada entrada en `applications` puede:

- **No declarar `valuesObject`** → usa todos los defaults del chart en `catalog/`
- **Declarar `valuesObject`** → sobreescribe solo las claves indicadas; el resto hereda del catalog

### Estructura de `values.yaml`

```yaml
config:
  spec:
    destination:
      server: https://<cluster-endpoint>       # API server del cluster destino para las apps hijas
    source:
      repoURL: https://github.com/<your-org>/<your-repo>.git
      targetRevision: main                     # Branch o tag del repo

applications:
  - name: <nombre>                 # Nombre de la ArgoCD Application resultante
    namespace: <namespace>         # Namespace destino en el cluster
    path: catalog/<chart>          # Path al chart en este repo
    project: <project>             # AppProject destino
    releaseName: <release>         # Opcional, por defecto usa el nombre
    syncWave: "0"                  # Opcional, controla el orden de sync
    destinationServer: <server>    # Opcional, override del destination.server solo para esta app
    valuesObject:                  # Opcional, overrides sobre el catalog
      <clave>: <valor>
```

## Convención de nombres recomendada

Para evitar colisiones cuando empiecen a existir `dev`, `qa`, `prod` y varias apps por cliente, conviene que **todas las `Application` incluyan cliente y ambiente en el nombre**.

Patrón recomendado:

- bootstrap app: `<client>-<env>-bootstrap`
- app hija: `<client>-<env>-<app>`
- proyecto Argo: `<client>-<env>`
- namespace Kubernetes: depende de la app; no necesita incluir cliente/ambiente si ya está aislado por cluster

Ejemplos:

- bootstrap app:
  - `example-client-dev-bootstrap`
  - `example-client-qa-bootstrap`
- apps hijas:
  - `example-client-dev-whoami`
  - `example-client-qa-whoami`
  - `example-client-prod-sonar`
- proyectos:
  - `example-client-dev`
  - `example-client-qa`
  - `example-client-prod`

Esto evita terminar con muchos `whoami`, `sonar`, `api`, `frontend` repetidos en el namespace `argocd`.

### Guardrail para `targetRevision`

En PRs hacia `main`, el repo valida que cada `clients/**/values.yaml` use:

```yaml
config:
  spec:
    source:
      targetRevision: main
```

Si de verdad necesitás dejar una rama distinta temporalmente, el override debe ser explicito:

```yaml
ci:
  allowNonMainTargetRevision: true
  allowNonMainTargetRevisionReason: "temporary branch test"
```

La idea es evitar merges accidentales con ramas de prueba en `targetRevision`.

### Ejemplo con overrides

```yaml
applications:
  - name: example-client-dev-whoami
    namespace: whoami-test
    path: catalog/whoami
    project: example-client-dev
    syncWave: "10"
    valuesObject:
      namespace: whoami-test
      replicaCount: 2
      image:
        repository: traefik/whoami
        tag: v1.10.2
```

> La clave raíz dentro de `valuesObject` depende del tipo de catalog. En charts simples como `catalog/whoami`, los valores se pasan directo. En charts con dependencias, la clave coincide con el `name` (o `alias`) declarado en el `Chart.yaml` del catalog.

---

## Orden de despliegue con syncWave

ArgoCD permite controlar el orden de creación de recursos mediante la anotación `argocd.argoproj.io/sync-wave`. El campo `syncWave` de cada entrada en `applications` se traduce directamente a esa anotación en la ArgoCD Application generada.

**Regla:** ArgoCD espera a que todos los recursos de una wave estén en estado `Healthy` antes de iniciar la siguiente.

### Orden usado en este repo

```
Wave -1 ─── argocd-projects    (solo en bootstrap/plataforma como internal)
Wave 0+ ─── apps del entorno   (por ejemplo whoami, sonar, external-secrets)
```

### Configuración en `values.yaml`

```yaml
applications:
  - name: example-client-dev-whoami
    namespace: whoami-test
    path: catalog/whoami
    project: example-client-dev
    syncWave: "10"
```

> `syncWave` es un string numérico (`"0"`, `"1"`, `"2"`). Si se omite, ArgoCD asigna wave `0` por defecto.

---

## Agregar un nuevo cliente o ambiente

1. Crear la carpeta `clients/<cliente>/<environment>`
2. Copiar `Chart.yaml` y `templates/` de otro entorno existente
3. Crear `values.yaml` declarando las aplicaciones y sus overrides específicos
4. Aplicar el bootstrap manualmente apuntando a `clients/<cliente>/<environment>`

```bash
mkdir -p clients/example-client/prod
cp clients/example-client/dev/Chart.yaml clients/example-client/prod/Chart.yaml
cp -r clients/example-client/dev/templates clients/example-client/prod/templates
cp clients/example-client/dev/values.yaml clients/example-client/prod/values.yaml
# Editar clients/example-client/prod/values.yaml con los valores del nuevo entorno
```

## Apps desde otro repo

### Estado actual del template

El template ya soporta overrides por app para el `source`. Si una app no declara nada especial, hereda:

- `config.spec.source.repoURL`
- `config.spec.source.targetRevision`

Si una app necesita otro repo o otra revision, hoy ya puede usar:

- `sourceRepoURL`
- `sourceTargetRevision`
- `sourcePath`
- `sourceType` (`helm`, `directory`, `kustomize`)

Ejemplo:

```yaml
applications:
  - name: example-client-dev-api
    namespace: api
    project: example-client-dev
    destinationServer: https://<example-client-dev-endpoint>
    sourceRepoURL: https://github.com/<your-org>/example-app-deploy.git
    sourceTargetRevision: main
    sourcePath: manifests/dev
    sourceType: directory
```

Notas:

- `path` sigue siendo obligatorio como fallback, pero si definís `sourcePath`, ese valor pisa a `path`
- `destinationServer` sigue definiendo a qué cluster se despliega la app hija
- la app raíz o bootstrap sigue viviendo en el Argo del cluster `internal`

### Modelo recomendado

La separación sana queda así:

- `clients/internal`
  - control plane, proyectos, registro de clusters
- `clients/<cliente>/<ambiente>`
  - bootstrap del entorno del cliente
- repos de apps de cada equipo
  - manifiestos o Helm values de su app

Argo CD sigue siendo centralizado, pero el **source repo** de cada app puede ser distinto porque el template ya soporta esos campos.

---

## Agregar un nuevo chart al catalog

1. Crear `catalog/<nombre>/Chart.yaml` con la dependencia externa (si aplica)
2. Crear `catalog/<nombre>/values.yaml` con los **defaults** del chart
3. Crear `catalog/<nombre>/templates/` con los recursos K8s (si es tipo directo)
4. Ejecutar `helm dependency update catalog/<nombre>/` y commitear el `Chart.lock`
5. Referenciar el nuevo chart en el `values.yaml` del cliente que lo necesite

---

## Dependencias de Helm

Los charts de tipo **Helm dependency** requieren que el `Chart.lock` esté commiteado en el repo para que ArgoCD pueda sincronizarlos sin acceso a red en el momento del deploy. Después de modificar dependencias, ejecutar:

```bash
helm dependency update catalog/apisix
helm dependency update catalog/azure-workload-identity
helm dependency update catalog/cert-manager
```

Y commitear los archivos `Chart.lock` generados.

## Versionado de catalogs

Si un catalog basado en un chart externo necesita una version distinta o una
compatibilidad diferente por cluster, no se recomienda parametrizar la version
por `values.yaml`.

Patron recomendado:

- una version por catalog
- si hace falta otra version incompatible, crear otro folder en `catalog/`

Ejemplo:

- `catalog/aws-load-balancer-controller`
- `catalog/aws-load-balancer-controller-v2-14`

Esto aplica especialmente a charts cloud-specific o a charts que traen CRDs,
porque la version del subchart y la version de los CRDs deben quedar alineadas.
