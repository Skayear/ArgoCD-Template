# k8s-monitoring

Wrapper del chart oficial `grafana/k8s-monitoring` (Grafana Alloy). Recolecta logs y eventos del cluster y los envía a un backend (`destinations`) — pensado como fuente de logs para `catalog/loki`, aunque el chart en sí no asume proveedor.

## Qué viene prendido por defecto

- `podLogs` y `clusterEvents`: recolección de logs de pods y eventos del cluster (primera pasada útil)
- `alloy-logs` y `alloy-singleton`: los agentes Alloy que hacen esa recolección

## Qué viene apagado a propósito

- `clusterMetrics`, `nodeLogs`, `alloy-metrics`, `alloy-receiver`: hasta definir arquitectura final de métricas/traces centralizadas de aplicación
- `applicationObservability`: trae ya precargadas las `transforms` típicas para sanitizar nombres de métricas/atributos OTel (reemplazar `.` por `_`, etc.) para cuando se habilite

## Lo que cada cliente tiene que definir

- `cluster.name`
- `destinations` (a dónde van logs/eventos — ej. `catalog/loki`)

El chart queda deliberadamente agnóstico de nube (`# El chart base no asume AWS/Azure/Huawei`).
