# opentelemetry-demo

Wrapper del chart oficial `open-telemetry/opentelemetry-demo`. No es un componente de plataforma — es la app de demo multi-servicio de OpenTelemetry, usada como generador de tráfico/traces real para probar el pipeline de observabilidad (`catalog/k8s-monitoring` → `catalog/tempo`/`catalog/mimir`/`catalog/loki` → `catalog/grafana`) sin depender de una app de negocio real.

`opentelemetry-collector`, `jaeger`, `grafana`, `prometheus` y `opensearch` propios del chart vienen apagados — la demo exporta al collector centralizado (`OTEL_COLLECTOR_NAME` apunta al receiver de `catalog/k8s-monitoring`) en vez de traer su propio stack de observabilidad aislado.

Útil para probar el pipeline de tracing extremo a extremo antes de conectarle aplicaciones reales.
