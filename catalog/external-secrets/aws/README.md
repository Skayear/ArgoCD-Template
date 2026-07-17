# external-secrets (aws)

Chart de recursos K8s directos, alternativo a `catalog/external-secrets-aws`: además del `SecretStore`/`ClusterSecretStore` de AWS, también genera él mismo los objetos `ExternalSecret` a partir de una lista declarativa en `values.yaml`, en vez de dejar que cada app defina el suyo.

## Diferencia con `catalog/external-secrets-aws`

| | `external-secrets-aws` | `external-secrets/aws` (este) |
|---|---|---|
| Crea el Store | Sí | Sí |
| Crea los `ExternalSecret` | No (cada app define el suyo) | Sí (`aws.externalSecrets[]`) |
| Usado por los clientes de ejemplo | Sí | No |

## Ejemplo

```yaml
aws:
  kind: SecretStore
  service: SecretsManager
  region: us-east-1
  secretStoreName: my-secret-store
  namespace: my-namespace
  serviceAccount:
    name: external-secrets-aws
    roleArn: arn:aws:iam::<AWS_ACCOUNT_ID>:role/<role>
  externalSecrets:
    - name: my-app-db
      refreshInterval: 1h
      creationPolicy: Owner
      remoteRef: my-app/db
      entries:
        - key: password
          property: password
```

Se mantiene en el catálogo como referencia de un diseño alternativo (centralizar todos los `ExternalSecret` de un namespace en un solo `values.yaml`), útil cuando no querés que cada chart de app tenga que declarar su propio `externalsecret.tpl`.
