# Karpenter placement - internal

Fecha: 2026-06-10

Este cliente apunta al mismo cluster EKS que `clients/devops`. La regla actual del POC es usar Karpenter solo para workloads stateless o reiniciables sin dolor. Los componentes single-replica, stateful o de control se quedan en los nodos legacy/base hasta tener HA o una estrategia de migracion mas segura.

## En Karpenter

Estos workloads usan:

```yaml
nodeSelector:
  karpenter.sh/nodepool: karpenter-on-demand
```

- `internal-mimir-gateway`: gateway stateless; reiniciable.
- `internal-mimir-distributor`: stateless; puede recrearse sin perdida de estado local.
- `internal-mimir-querier`: stateless; puede recrearse y volver a consultar backend.
- `internal-mimir-query-frontend`: stateless; frontend de queries.
- `internal-mimir-query-scheduler`: stateless; scheduler de queries.
- `internal-loki-gateway`: gateway stateless; no almacena datos.
- `internal-tempo-distributor`: stateless; recibe y distribuye trazas.
- `internal-tempo-querier`: stateless.
- `internal-tempo-query-frontend`: stateless.
- `internal-tempo-compactor`: se mantiene en Karpenter por ahora; si se vuelve sensible o queda single-replica con impacto operativo, moverlo a legacy.
- `internal-tempo-memcached`: cache reiniciable.
- `prometheus-stack-kube-state-metrics`: exporter stateless; facil de recrear.
- `internal-k8s-monitoring-alloy-singleton`: componente de observabilidad reiniciable para esta fase.

## En legacy/base

Estos workloads no deben forzarse a Karpenter en esta fase:

- `prometheus-internal-prometheus-stack-prometheus`: single-replica/stateful con PVC; fuente central de metricas.
- `internal-prometheus-stack-operator`: controlador critico de Prometheus CRDs.
- `internal-mimir-ingester`: stateful/single-replica con PVC; contiene estado activo de ingesta.
- `internal-mimir-store-gateway`: stateful/single-replica con PVC/cache local; mejor mantener estable.
- `internal-mimir-compactor`: stateful/single-replica con PVC; mantenimiento de bloques.
- `internal-loki` singleBinary: StatefulSet con PVC; no mover hasta tener HA o estrategia clara.
- `internal-tempo-ingester`: StatefulSet/single-replica con PVC; no mover hasta tener HA.
- `internal-grafana`: una replica con PVC; preferimos estabilidad simple.
- `internal-k8s-monitoring-alloy-operator`: controlador; mantener fuera de Karpenter por ahora.
- `internal-apisix` y `internal-apisix-ingress-controller`: camino critico de entrada al cluster; se mantiene en legacy/base.
- `argocd`: control-plane GitOps; no mover en este POC.
- Workloads de `kube-system`: add-ons y agentes del cluster; no mover desde este repo.

## Criterio

- Karpenter: gateways, query-frontends, queriers, distributors, exporters, caches y workloads stateless.
- Legacy/base: stateful single-replica, controladores, ingress/gateway critico, Prometheus/Grafana principales y cualquier componente con PVC sensible.
- Antes de mover un componente nuevo, validar replicas, PDB, PVC, requests/limits y consumo real con `kubectl top`.

## Nota: cargas stateful/criticas de observabilidad y consolidacion con Karpenter

Durante la migracion de workloads hacia nodos administrados por Karpenter, se identifico que algunos componentes de observabilidad no son buenos candidatos para consolidacion automatica agresiva en su configuracion actual.

En particular, componentes stateful/criticos como:

- `internal-mimir-ingester`
- `internal-mimir-store-gateway`
- `internal-mimir-compactor`
- otros componentes similares de Mimir/Tempo/Loki cuando corren con una sola replica

presentan limitaciones operativas para ser movidos libremente por Karpenter.

### Motivo

Actualmente varios de estos componentes corren con configuracion `1/1`, es decir, una sola replica disponible. En ese escenario, cualquier eviccion del pod implica una interrupcion temporal del componente, porque no existe otra replica lista que pueda absorber la carga mientras el pod se recrea en otro nodo.

Karpenter detecto nodos underutilized e intento consolidarlos, pero la operacion fue bloqueada por `PodDisruptionBudget` en componentes de Mimir. Se observaron eventos como:

```text
DisruptionBlocked: Pdb prevents pod evictions
FailedDraining: Failed to drain node, pods are waiting to be evicted
```

Esto indica que Karpenter esta funcionando correctamente: intenta consolidar, pero respeta las garantias de disponibilidad declaradas por Kubernetes mediante los PDBs.

### Conclusion

No es que estos workloads no puedan moverse. Si pueden moverse, pero no de forma automatica y transparente sin riesgo de interrupcion mientras sigan corriendo con una sola replica.

Para que estos componentes puedan ser movidos y consolidados de forma segura por Karpenter, se requiere una arquitectura con alta disponibilidad real, por ejemplo:

- multiples replicas para componentes criticos;
- PDBs compatibles con evicciones controladas;
- distribucion entre zonas/nodos mediante anti-affinity o topology spread;
- suficiente capacidad para recrear pods antes de interrumpir los existentes.

### Decision actual

Por ahora, se recomienda mantener los componentes stateful/criticos de observabilidad en nodos legacy/estables y usar Karpenter principalmente para workloads stateless o facilmente recreables.

Ejemplo de division recomendada:

```text
Nodos legacy / estables:
- Mimir ingester
- Mimir store-gateway
- Mimir compactor
- Prometheus
- otros componentes stateful/criticos

Nodos Karpenter:
- gateways
- query frontends
- queriers
- distributors
- exporters
- aplicaciones stateless
- workloads internos tolerantes a reinicio
```

Esta decision reduce ruido operativo, evita consolidaciones bloqueadas por PDBs y permite que Karpenter se enfoque en cargas que si pueden moverse de forma segura.

### Revision futura

Si se requiere mover completamente observabilidad a Karpenter, se debera redisenar la configuracion para alta disponibilidad, aumentando replicas y ajustando PDBs/topology spread antes de habilitar consolidacion automatica sobre esos componentes.
