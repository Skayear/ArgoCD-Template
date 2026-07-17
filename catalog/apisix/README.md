# apisix

Wrapper del chart oficial `apache/apisix-helm-chart` (subchart `apisix`). Despliega el gateway APISIX (data plane + ingress-controller) como Application de Argo CD.

## Qué instala

- APISIX en modo `standalone` (config vía YAML, sin etcd propio — `etcd.enabled: false`)
- `ingress-controller` con `provider.type: apisix-standalone`, leyendo `ApisixRoute`/`ApisixTls` directamente
- métricas Prometheus expuestas en `/apisix/prometheus/metrics` + `ServiceMonitor`
- opcionalmente un NLB interno adicional (`nlbInternal`) para exponer el gateway también puertas adentro

## Exposición

El `Service` del gateway es `LoadBalancer` (NLB internet-facing por defecto, vía las annotations de `aws-load-balancer-controller` y `external-dns`). El hostname público que apunta a ese NLB (`gateway.internal.example.com` en este ejemplo) es la base sobre la que después `catalog/dns-endpoints` cuelga hostnames de apps individuales.

## Relación con `apisix-routes`

Este chart no define ningún `ApisixRoute`. Las rutas de cada app se declaran por separado en `catalog/apisix-routes`, que apunta al `ingressClassName` que expone este chart.
