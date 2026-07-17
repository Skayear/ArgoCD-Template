# alertas/prometheus-k8s

Chart de recursos K8s directos: un único `PrometheusRule` (`k8s-alerts`) con reglas de alerta base de Kubernetes (nodos no responden, uso de CPU alto, etc.) sobre Prometheus Operator, pensado para instanciarse contra el `catalog/prometheus-stack` de cada cluster.

```yaml
release: internal-prometheus-stack   # debe matchear el label `release` del Prometheus Operator del cluster
account: internal
environment: internal
```

`account`/`environment` se inyectan como labels en cada alerta (para poder filtrar/rutear en Alertmanager cuando hay varios clusters/cuentas reportando al mismo Grafana/Mimir central). `runbook_url` en las anotaciones apunta a un placeholder (`https://wiki.example.com/runbooks/...`) — reemplazar por la wiki real de tu equipo.
