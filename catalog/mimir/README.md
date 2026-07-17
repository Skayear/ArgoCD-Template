# Notas De Mimir

## Resumen

Este chart agrega `Mimir` como backend central de metricas para el cluster
`internal`.

La idea es:

- cada cliente mantiene su `Prometheus` local
- cada cliente hace `remoteWrite` a `Mimir`
- `Grafana` central consulta `Mimir`

Eso evita que `Grafana internal` tenga que hablar directo con un datasource
Prometheus distinto por cliente.

## Criterio De Esta Primera Version

El wrapper deja una base chica y portable:

- `gateway` habilitado
- `minio` apagado
- `kafka` apagado
- `alertmanager` y `ruler` apagados
- storage compartido definido por cliente
- multitenancy habilitada

La topologia elegida para esta primera pasada es la clasica, no la arquitectura
de ingest-storage con Kafka.

## Contrato Del Chart

El `catalog` no define proveedor ni credenciales.

Cada cliente debe definir:

- `mimir-distributed.serviceAccount.name`
- `mimir-distributed.serviceAccount.annotations`
- `mimir-distributed.mimir.structuredConfig.common.storage.backend`
- y el bloque de storage correspondiente

El wrapper falla si:

- no se define el nombre del service account
- no se define el backend de storage
- se intenta usar `filesystem`

## Cliente Internal

En [values.yaml](../../clients/internal/values.yaml)
`internal-mimir` queda configurado con:

- tenant base `internal`
- storage `s3`
- bucket central de metricas
- IRSA
- `gateway` interno para:
  - `remoteWrite`: `/api/v1/push`
  - queries PromQL: `/prometheus`

## Flujo

1. `internal-prometheus-stack` scrapea el cluster `internal`
2. `internal-prometheus-stack` hace `remoteWrite` a `internal-mimir`
3. `internal-grafana` consulta `internal-mimir`

En clientes futuros, el patron es el mismo:

1. `Prometheus` local scrapea
2. `remoteWrite` a `internal-mimir`
3. `Grafana internal` consulta `Mimir`
