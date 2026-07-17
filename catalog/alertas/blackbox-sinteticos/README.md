# alertas/blackbox-sinteticos

Chart de recursos K8s directos: genera un `PrometheusRule` por cada probe sintético definido en `synthetics`, alertando cuando `probe_success` cae — pensado para usarse junto con `catalog/blackbox-exporter` (que es quien genera la métrica `probe_success`).

```yaml
account: internal
environment: internal
synthetics:
  - name: grafana-internal
    matchLabels:
      service: grafana
```

Cada entrada de `synthetics` genera su propio `PrometheusRule` (nombre derivado de `name`, sanitizado a minúsculas/guiones). `matchLabels` debe coincidir con las labels que `catalog/blackbox-exporter` le puso a ese target en su `ServiceMonitor` — si no matchean, la alerta nunca dispara ni por falso positivo ni por real, simplemente no encuentra series.
