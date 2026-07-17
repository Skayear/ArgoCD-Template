# cert-manager

Wrapper del chart oficial `jetstack/cert-manager`. Instala el controller que emite y renueva certificados TLS (`Certificate`, `ClusterIssuer`/`Issuer`, CRDs incluidas con `crds.keep: true` para que sobrevivan un `helm uninstall`).

Deshabilitado por defecto (`enabled: false`) — cada cluster lo prende explícitamente.

## Requiere

- `serviceAccount.annotations["eks.amazonaws.com/role-arn"]`: rol IAM con permiso sobre Route53 (`route53:ChangeResourceRecordSets`, etc.) para el solver DNS-01 — el mismo rol que después referencia `catalog/clusterissuers` en `iamRole`.
- Resolvers DNS recursivos propios (`1.1.1.1`, `8.8.8.8`) para el challenge DNS-01, evitando depender del DNS interno del cluster mientras el registro TXT todavía no propagó.

## Con qué se usa junto

1. `cert-manager` (este chart) → instala el controller
2. `catalog/clusterissuers` → declara el `ClusterIssuer` (Let's Encrypt + Route53/Azure DNS)
3. `catalog/certificates` → pide certificados concretos contra ese `ClusterIssuer`
