# prometheus-integrations

Chart simple para declarar `ServiceMonitor` externos al stack base.

Se usa para integrar servicios que ya exponen métricas, por ejemplo:

- `argocd`
- `cert-manager`
- `apisix`

El chart no habilita endpoints de métricas por sí mismo. Solo crea los
`ServiceMonitor` que Prometheus va a descubrir.
