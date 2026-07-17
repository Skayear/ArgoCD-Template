# prometheus-stack

Wrapper del chart oficial `prometheus-community/kube-prometheus-stack`. Instala Prometheus Operator + Prometheus + Alertmanager + kube-state-metrics + node-exporter. **Grafana viene deshabilitado** (`grafana.enabled: false`) porque en este catálogo Grafana se gestiona aparte, en `catalog/grafana`, como capa de visualización independiente que puede tener múltiples datasources (no solo el Prometheus local).

## Lo que cada cliente tiene que definir sí o sí

El chart no trae defaults para esto — hay que setearlo por cliente:

- `prometheus.prometheusSpec.retention`
- `prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage`

## Remote write

Si además de Prometheus local se quiere centralizar métricas (a `catalog/mimir`, Grafana Cloud, AMP, etc.), el bloque comentado en `values.yaml` muestra el patrón: `remoteWrite` con `basicAuth` referenciando un `Secret`/`ExternalSecret`, nunca credenciales en texto plano.

## Ajustes sobre los defaults del subchart

- `defaultRules` desactiva reglas de `etcd`/`kubeControllerManager`/`kubeScheduler` porque en clusters administrados (EKS, AKS) esos componentes no son accesibles para scrapear.
- `prometheus-node-exporter` fuerza `hostNetwork: false` y tolera todos los taints, para no depender de labels específicas del proveedor ni chocar con otro stack de monitoreo que ya use el puerto 9100.

## Con qué se usa junto

- `catalog/grafana` — visualización
- `catalog/alertas/prometheus-k8s` y `catalog/alertas/blackbox-sinteticos` — reglas de alerta que apuntan al `release` de este chart
- `catalog/prometheus-integrations` — `ServiceMonitor` de servicios externos al stack
