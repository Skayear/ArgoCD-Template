# azure-workload-identity

Wrapper del chart oficial `azure-workload-identity/workload-identity-webhook` (alias `azure-workload-identity`). Instala el mutating webhook que inyecta las variables de entorno/volumen necesarias para que un pod con `azure.workload.identity/use: "true"` se autentique en Azure AD sin secrets estáticos.

## Cuándo hace falta

Solo en clusters que necesitan autenticarse contra Azure AD (por ejemplo, Argo CD usando OIDC de Entra ID — ver `argocd/values/custom_argo.yaml`, que setea `podLabels.azure.workload.identity/use: "true"` y la annotation `azure.workload.identity/client-id` en su `serviceAccount`). Es el equivalente en Azure de IRSA en AWS.

## Configuración

```yaml
azure-workload-identity:
  azureTenantID: "<AZURE_TENANT_ID>"
```

El `clientID` en sí no lo define este chart: se setea por pod/serviceAccount vía la annotation `azure.workload.identity/client-id`, no acá.
