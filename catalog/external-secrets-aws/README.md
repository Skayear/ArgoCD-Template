# external-secrets-aws

Chart de recursos K8s directos: declara un `SecretStore`/`ClusterSecretStore` (`external-secrets.io`) apuntando a AWS Secrets Manager, autenticado vía IRSA (`serviceAccountRef` + rol IAM, sin credenciales estáticas).

Este es el chart que usan los clientes de ejemplo (`clients/devops`, `clients/internal`) — uno por cada cluster/cuenta AWS que necesite leer secrets. Cada app consumidora (`sonarqube`, `vaultwarden`, `grafana`, etc.) define su propio `ExternalSecret` apuntando por nombre al store que este chart crea.

## Configuración

```yaml
aws:
  kind: ClusterSecretStore   # o SecretStore, si querés que quede namespaced
  service: SecretsManager    # o ParameterStore
  region: us-east-1
  secretStoreName: my-secret-store
  namespace: external-secrets
  serviceAccount:
    name: external-secrets-aws
    roleArn: arn:aws:iam::<AWS_ACCOUNT_ID>:role/<role-con-permiso-a-secretsmanager>
```

Requiere que `catalog/external-secrets/core` (el operador) ya esté instalado en el cluster.

> Nota: existe un chart hermano en `catalog/external-secrets/aws` con un contrato distinto (además del `SecretStore`, genera él mismo los `ExternalSecret` a partir de una lista en `values.yaml`). Ninguno de los clientes de ejemplo lo usa; se mantiene solo como referencia de un diseño alternativo.
