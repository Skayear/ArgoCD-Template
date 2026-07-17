# opencost

Wrapper del chart oficial `opencost/opencost`. Estima el costo por namespace/workload/label a partir de las métricas de uso reales del cluster (CPU/memoria/storage) consultando el Prometheus del cluster.

## Notas del wrapper

- El chart wrapper y la dependencia upstream comparten nombre (`opencost`), por eso los values del subchart van anidados dos veces: `opencost.opencost.*`.
- `prometheus.external.url` apunta al `Prometheus` del `catalog/prometheus-stack` local (`http://<release>-prometheus.monitoring.svc.cluster.local:9090`) — ajustar el nombre de release si difiere.
- `metrics.kubeStateMetrics.emitKsmV1Metrics: false` evita que OpenCost emita una serie de kube-state-metrics duplicada de la que ya expone `catalog/prometheus-stack`.
- `customPricing` queda en default (sin costos de nube reales) hasta que se defina el modelo de pricing — por ahora reporta solo uso relativo, no costo en moneda real.

`exporter.defaultClusterId` identifica el cluster en los reportes; conviene que coincida con el nombre real del cluster.
