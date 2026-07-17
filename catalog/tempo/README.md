# tempo

Wrapper del chart oficial `grafana/tempo-distributed`. Backend de tracing distribuido, consultado desde `catalog/grafana`. Recibe traces vía OTLP (gRPC y HTTP habilitados), pensado como destino de `catalog/opentelemetry-demo` o de cualquier app instrumentada con OpenTelemetry.

## Guardrail de storage

El chart **falla el render** (`templates/validate.yaml`) si el cliente no define `tempo-distributed.storage.trace.backend`, y falla también si ese backend es `local` — la topología distribuida (`ingester`/`distributor`/`compactor`/`querier`/`queryFrontend` como componentes separados) necesita un backend de objetos compartido (S3, Azure Blob, GCS, etc.), no disco local por componente.

## Otras decisiones del wrapper

- `replication_factor: 1` en el ingester — pensado para un volumen de un solo cluster, no para tracing multi-tenant a gran escala.
- `memcached` habilitado como cache compartida entre componentes.
- `minio` y `gateway` apagados — el gateway lo resuelve `catalog/apisix-routes`/`catalog/grafana` en vez del gateway propio del chart.
- `metricsGenerator` apagado — no genera métricas derivadas de spans (RED metrics) hasta que se decida enviarlas a `catalog/prometheus-stack`/`catalog/mimir`.

Cada cliente debe definir el backend de storage y sus credenciales (vía IRSA si es S3, o `ExternalSecret` si no).
