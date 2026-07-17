# grafana

Wrapper del chart oficial `grafana/grafana`, como capa de visualización independiente del stack de métricas (`catalog/prometheus-stack` trae Grafana apagado a propósito — ver ese README).

## Por qué separado del `prometheus-stack`

Para poder tener una sola Grafana consultando varios datasources (Prometheus local, `catalog/mimir` centralizado, `catalog/loki`, `catalog/tempo`) sin acoplarla al ciclo de vida del Prometheus operator.

## Dashboards y datasources como código

- `defaultDashboards`: monta `dashboards/**/*.json` (ver la carpeta `dashboards/` de este chart) como `ConfigMap`s etiquetados `grafana_dashboard: "1"`, que el sidecar de dashboards descubre automáticamente
- `sidecar.dashboards`/`sidecar.datasources` con `searchNamespace: ALL`: cualquier `ConfigMap` con esas labels, en cualquier namespace, se importa solo — así cada app puede traer su propio dashboard sin tocar este chart

## Notas operativas

- `deploymentStrategy: Recreate`: con un solo réplica y un PVC `ReadWriteOnce`, un `RollingUpdate` puede quedar trabado intentando montar el volumen en el pod nuevo antes de que el viejo lo suelte.
- SMTP con `$__env{...}`: las credenciales de SMTP se inyectan por variable de entorno (via `envFromSecret`/`externalSecrets`), nunca en `grafana.ini` en texto plano.
- `externalSecrets` (bloque propio, no `catalog/external-secrets-aws`): pensado para secrets de runtime específicos de Grafana (webhooks de alerting, etc.) sin commitearlos en Git.
