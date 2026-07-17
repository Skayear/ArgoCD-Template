# loki

Wrapper del chart oficial `grafana/loki`. Backend de logs centralizado, consultado desde `catalog/grafana`.

## Decisiones del wrapper

- `deploymentMode: SingleBinary` con todos los componentes distribuidos (`ingester`, `querier`, `distributor`, etc.) en `replicas: 0` — todo corre en el binario único (`singleBinary`), pensado para el volumen de un solo cluster, no para un Loki multi-tenant a gran escala.
- `minio`, `resultsCache`, `chunksCache`, `lokiCanary`, `test` apagados — no hace falta storage local (`object_store: s3`, ver abajo) ni los componentes de test del chart.
- `schemaConfig` fija `object_store: s3`. **Si el backend no es S3-compatible** (ej. Azure Blob), hay que sobreescribir `loki.loki.schemaConfig.configs[].object_store` desde el cliente — este catálogo no lo asume.

## Lo que cada cliente tiene que definir

El bucket/storage real (`storage_config` para el `object_store` elegido) y las credenciales de acceso (via IRSA si es S3, o `ExternalSecret` si no).
