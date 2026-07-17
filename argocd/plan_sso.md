# Plan SSO Argo CD con Microsoft Entra ID en EKS

## Objetivo

Habilitar SSO en la instalación nueva de Argo CD ubicada en `argocd/`, manteniendo a APISIX como punto de entrada externo y usando Microsoft Entra ID como proveedor de identidad.

## Alcance

Este plan aplica solo a la instalación nueva de Argo CD:

- `argocd/values/custom_argo.yaml`

## Arquitectura objetivo

```text
[ Usuario ]
    |
    v
[ Entra ID ]
    ^
    | OIDC
    v
[ APISIX HTTPS ]
    |
    v
[ argocd-server ]
    |
    v
[ Argo CD en EKS ]
```

Para autenticación de usuarios:

- Entra ID actúa como IdP OIDC
- Argo CD usa OIDC directo
- APISIX publica `https://argocd.internal.example.com`

Para autenticación de Argo contra Entra sin `client secret`:

- se usa Workload Identity Federation
- EKS emite tokens OIDC del service account
- Entra confía en esos tokens mediante una Federated Credential


## Fases del trabajo

## Fase 1: Preparar EKS e instalar la base de federación

Esta fase cubre la parte del lado clúster.

El objetivo no es todavía configurar Argo CD ni Microsoft Entra, sino dejar lista la base técnica que hace posible la federación:

- obtener el issuer OIDC de EKS
- validar que ese issuer sea accesible
- instalar en el clúster el componente que permite a los pods usar Workload Identity

En otras palabras, esta fase instala la base de identidad federada del lado de Kubernetes.

### Paso 1. Obtener el issuer OIDC del clúster

```bash
aws eks describe-cluster \
  --name <EKS_CLUSTER_NAME> \
  --query "cluster.identity.oidc.issuer" \
  --output text
```

Ese valor será el `issuer` que Microsoft Entra debe confiar.

### Paso 2. Verificar que el issuer sea accesible


Hay que probar:

- `<ISSUER>/.well-known/openid-configuration`
- `<ISSUER>/keys` o el JWKS que indique el discovery document

Ejemplo:

```bash
ISSUER=$(aws eks describe-cluster \
  --name <EKS_CLUSTER_NAME> \
  --query "cluster.identity.oidc.issuer" \
  --output text)

curl -s "${ISSUER}/.well-known/openid-configuration" | jq
```

Luego, del JSON de salida, revisar el campo `jwks_uri` y probarlo:

```bash
curl -s "<JWKS_URI>" | jq
```

### Qué significa este paso

Microsoft Entra necesita poder:

- descubrir la metadata OIDC del issuer
- obtener las claves públicas con las que Kubernetes firma los tokens

Si eso no responde correctamente, la federación no va a funcionar aunque el YAML de Argo esté perfecto.


### Paso 3. Instalar el webhook de Azure Workload Identity con Argo CD

En EKS este paso sí es necesario si se quiere usar Workload Identity con Azure.

Este webhook:

- observa pods etiquetados con `azure.workload.identity/use: "true"`
- inyecta la configuración necesaria
- proyecta el token federado para que el SDK de Azure pueda autenticarse


Se deja un `Application` dentro del chart de Argo CD. dedicado, por ejemplo:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: azure-workload-identity
  namespace: argocd
spec:
  project: default
  destination:
    namespace: azure-workload-identity-system
    server: https://kubernetes.default.svc
  source:
    repoURL: https://azure.github.io/azure-workload-identity/charts
    chart: workload-identity-webhook
    targetRevision: <CHART_VERSION>
    helm:
      values: |
        azureTenantID: <AZURE_TENANT_ID>
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

El resultado esperado es:

- namespace `azure-workload-identity-system`
- webhook desplegado y sano
- Argo CD lo administra como cualquier otro componente base

## Fase 2: Preparar Entra ID

### Paso 4. Crear App Registration

En Microsoft Entra ID:

1. `App registrations`
2. `New registration`
3. Redirect URI web:

```text
https://argocd.internal.example.com/auth/callback
```

### Paso 5. Agregar redirect URI para CLI

```text
http://localhost:8085/auth/callback
```

### Paso 6. Configurar permisos y claims

Agregar:

- `User.Read`
- `groups` claim en el token

### Paso 7. Crear Federated Credential

En la App Registration:

1. `Certificates & secrets`
2. `Federated credentials`
3. `Add credential`
4. `Kubernetes Accessing Azure resources`

Datos necesarios:

- Cluster issuer URL: issuer OIDC de EKS
- Namespace: `argocd`
- Service account: `argocd-server`

### Note:
Se deja la App registration creada Argocd https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/11111111-1111-1111-1111-111111111111/isMSAApp~/false

 En el cual se le da acceso de owner a todos los integrantes hasta el momento del grupo devops

## Fase 3: Configurar Argo CD

Archivo objetivo:

- `argocd/values/custom_argo.yaml`


## Fase 4: Validación

### Paso 8. Desplegar

Sincronizar Argo CD con los cambios en `argocd/`.

### Paso 9. Verificar inyección de identidad

Validar en el pod de `argocd-server`:

- label `azure.workload.identity/use: "true"`
- service account annotation correcta
- variables/archivos proyectados por el webhook

### Paso 10. Probar login

- UI: botón SSO
- CLI: `argocd login ... --sso`


## Fuentes oficiales

- Argo CD Microsoft / OIDC: https://argo-cd.readthedocs.io/en/release-3.0/operator-manual/user-management/microsoft/
- Azure Workload Identity: https://azure.github.io/azure-workload-identity/docs/
- AWS EKS OIDC issuer: https://docs.aws.amazon.com/eks/latest/APIReference/API_OIDC.html
