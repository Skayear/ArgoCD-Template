# Troubleshooting Argo CD

Este documento resume los problemas más comunes encontrados durante la integración de Argo CD con:

- APISIX
- Microsoft Entra ID (OIDC)
- Azure Workload Identity
- RBAC por grupos

La idea es tener una guía corta y operativa para verificar primero el estado real del cluster antes de volver a desplegar Argo CD.

## 1. No soy admin aunque pertenezco al grupo en Entra ID

### Síntoma

- el usuario puede iniciar sesión
- pero no puede hacer `sync`
- o aparece como `readonly`

### Causa probable

Argo CD no usa "todos los grupos que existen en Entra", sino solamente los grupos que realmente llegan en el token OIDC.

Puede pasar que:

- el grupo exista en Entra ID
- el usuario pertenezca a ese grupo
- pero ese grupo no llegue en el token que Argo CD recibe

### Qué revisar

Dentro de la sesión del usuario en Argo CD:

- `Username`
- `Issuer`
- `Groups`

Lo importante es verificar si el `Object ID` del grupo admin aparece realmente en `Groups`.

### Qué validar en el cluster

```bash
kubectl get cm -n argocd argocd-rbac-cm -o yaml
```

Revisar:

- `policy.default`
- `scopes`
- `policy.csv`

### Regla práctica

El grupo que se usa en RBAC debe ser uno que:

- exista en Entra ID
- y además llegue en el token

## 2. Login correcto en Azure pero error `AZURE_FEDERATED_TOKEN_FILE env variable not found`

### Síntoma

El flujo de login redirige bien a Azure, el usuario se autentica, vuelve a Argo CD y falla con:

```text
failed to generate client assertion: AZURE_FEDERATED_TOKEN_FILE env variable not found
```

### Causa probable

El pod de `argocd-server` no fue mutado por el webhook de Azure Workload Identity.

### Qué revisar

#### ServiceAccount de Argo CD

```bash
kubectl get sa -n argocd argocd-server -o yaml
```

Revisar:

- `azure.workload.identity/client-id`

#### Deployment de Argo CD

```bash
kubectl get deployment -n argocd argocd-server -o yaml
```

Revisar en `spec.template.metadata.labels`:

```yaml
azure.workload.identity/use: "true"
```

#### Variables inyectadas en el pod

```bash
kubectl exec -n argocd deploy/argocd-server -- printenv | grep AZURE
```

Revisar si existen:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_FEDERATED_TOKEN_FILE`

## 3. El webhook de Azure Workload Identity no muta pods

### Síntoma

El pod nuevo falla al crearse con un error parecido a:

```text
failed calling webhook "mutation.azure-workload-identity.io"
```

o

```text
no endpoints available for service "azure-wi-webhook-webhook-service"
```

### Causa probable

El `Service` del webhook no tiene endpoints válidos.

Esto puede pasar si:

- el selector del `Service` no matchea los pods
- los pods del webhook no están `Ready`
- quedaron recursos mezclados de releases distintos

### Qué revisar

```bash
kubectl get pods -n azure-workload-identity-system --show-labels
kubectl get svc -n azure-workload-identity-system
kubectl describe svc -n azure-workload-identity-system azure-wi-webhook-webhook-service
kubectl get endpoints -n azure-workload-identity-system azure-wi-webhook-webhook-service -o yaml
kubectl logs -n azure-workload-identity-system -l app=workload-identity-webhook --tail=200
```

### Qué buscar

- pods `Running`
- `Service` con selector correcto
- `Endpoints` con IPs
- logs del webhook sin errores permanentes

## 4. `ERR_TOO_MANY_REDIRECTS` al entrar a Argo CD

### Síntoma

El navegador muestra:

```text
This page isn’t working
argocd.internal.example.com redirected you too many times
```

O por `curl` se observa un `307` infinito.

### Causa probable

Argo CD quedó detrás de APISIX sin el parámetro:

```yaml
configs:
  params:
    server.insecure: true
```

### Qué revisar

```bash
kubectl get cm -n argocd argocd-cmd-params-cm -o yaml
```

Debe existir:

```yaml
data:
  server.insecure: "true"
```

### Cómo validar el loop

```bash
curl -k -I -L https://argocd.internal.example.com
```

Si hay muchas respuestas `307` a la misma URL, revisar `server.insecure`.

### Qué revisar en Helm

```bash
helm get values -n argocd argocd -a
```

Sirve para confirmar si el release Helm realmente tomó el cambio.

## 5. El release Helm no tomó cambios del repo

### Síntoma

El archivo local `custom_argo.yaml` tiene cambios, pero el cluster no los refleja.

### Causa probable

El workflow desplegó:

- un commit viejo
- una rama distinta
- o un release anterior sin los cambios esperados

### Qué revisar

```bash
helm get values -n argocd argocd -a
kubectl get cm -n argocd argocd-cmd-params-cm -o yaml
kubectl get cm -n argocd argocd-rbac-cm -o yaml
```

Y también confirmar el commit desplegado en GitHub Actions.

## 6. No puedo ver `AppProject` o navegar bien por proyectos

### Síntoma

El usuario ve o sincroniza algunas apps, pero no puede ver correctamente los proyectos.

### Causa probable

Faltan permisos sobre el recurso `projects` en RBAC.

### Ejemplo correcto

```yaml
p, role:admin, projects, *, *, allow
p, role:team-a, projects, get, team-a, allow
p, role:team-b, projects, get, team-b, allow
p, role:team-c, projects, get, team-c, allow
```

## 7. Comandos mínimos de diagnóstico

### Configuración viva de Argo CD

```bash
kubectl get cm -n argocd argocd-cm -o yaml
kubectl get cm -n argocd argocd-cmd-params-cm -o yaml
kubectl get cm -n argocd argocd-rbac-cm -o yaml
```

### Server de Argo CD

```bash
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-server
kubectl describe pod -n argocd -l app.kubernetes.io/name=argocd-server
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server --tail=200
```

### Workload Identity

```bash
kubectl get sa -n argocd argocd-server -o yaml
kubectl get deployment -n argocd argocd-server -o yaml
kubectl exec -n argocd deploy/argocd-server -- printenv | grep AZURE
```

### Webhook de Azure Workload Identity

```bash
kubectl get pods -n azure-workload-identity-system --show-labels
kubectl get svc -n azure-workload-identity-system
kubectl get endpoints -n azure-workload-identity-system azure-wi-webhook-webhook-service -o yaml
kubectl logs -n azure-workload-identity-system -l app=workload-identity-webhook --tail=200
```

### Validación web

```bash
curl -k -I -L https://argocd.internal.example.com
```

## 8. Regla general

Antes de redeployar Argo CD:

1. revisar el `ConfigMap` vivo
2. revisar el release Helm vivo
3. revisar la sesión y los grupos reales que llegaron al token

Muchos de los problemas encontrados no venían del YAML en sí, sino de una diferencia entre:

- lo que estaba en el repo
- lo que realmente quedó desplegado
- y lo que el usuario veía en la sesión activa
