# external-secrets

Wrapper del chart oficial `external-secrets/external-secrets`. Instala el operador (CRDs `ExternalSecret`, `SecretStore`, `ClusterSecretStore`) que sincroniza secrets desde un backend externo (AWS Secrets Manager, Azure Key Vault, etc.) hacia `Secret` nativos de Kubernetes.

Es un prerequisito de `catalog/external-secrets-aws` (y de `catalog/external-secrets/aws`) — ese chart solo declara el `ClusterSecretStore`/`SecretStore`, este instala el controller que lo procesa.

`installCRDs: false` porque las CRDs de ESO se gestionan aparte (evita el problema clásico de Helm no pudiendo actualizar CRDs propias en upgrades).
