# dew-secret-provider

Chart de recursos K8s directos: provisiona un `SecretProviderClass` (provider `cce`, via el Secrets Store CSI driver) y el `ServiceAccount` asociado para que pods en Huawei Cloud CCE monten secrets desde **DEW/CSMS** (el equivalente en Huawei Cloud a AWS Secrets Manager / Azure Key Vault).

Es el análogo, para clusters en Huawei Cloud, de lo que `catalog/external-secrets-aws` hace para AWS — aunque con un mecanismo distinto (CSI driver + volumen montado, en vez de operador + `ExternalSecret` sincronizando a un `Secret` nativo).

## Piezas

- `SecretProviderClass`: lista `csmsObjects` (qué secrets de CSMS traer) y opcionalmente `secretObjects` (para además espejarlos a un `Secret` nativo de K8s)
- `ServiceAccount`: con la annotation `cce.io/dew-resource` que autoriza qué secrets de CSMS puede leer
- `bootstrap-deployment` (opcional, `imagePullSecret.enabled`): un pod dummy que solo existe para forzar el montaje del volumen CSI y materializar un `imagePullSecret` antes de que otros workloads lo necesiten

## Ejemplo

```yaml
serviceAccount:
  name: my-app
  csmsSecrets:
    - my-app/db-password

csmsObjects:
  - objectName: my-app/db-password
    objectAlias: db-password

secretObjects:
  - secretName: my-app-db
    data:
      - objectName: db-password
        key: password
```
