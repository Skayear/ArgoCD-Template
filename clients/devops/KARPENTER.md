# Karpenter placement - devops

Fecha: 2026-06-10

Este cliente despliega piezas de Karpenter y algunas apps que corren en el mismo cluster EKS que `clients/internal`. La regla actual del POC es mantener Karpenter para capacidad elastica de workloads stateless/reiniciables y dejar stateful/control-plane/ingress critico en legacy/base.

## Karpenter core

Estas aplicaciones habilitan Karpenter y deben sincronizarse antes de mover workloads:

- `karpenter-crd`: instala los CRDs (`NodePool`, `EC2NodeClass`, `NodeClaim`).
- `karpenter-controller`: controlador de Karpenter.
- `karpenter-nodepools`: define `EC2NodeClass/default` y `NodePool/karpenter-on-demand`.

El NodePool actual:

- `karpenter-on-demand`
- capacity type: `on-demand`
- familias: `m7i`, `m7i-flex`
- tamanos: `large`, `xlarge`
- limits: `cpu: "8"`, `memory: 32Gi`
- consolidation: `WhenEmptyOrUnderutilized`, `consolidateAfter: 5m`

## En Karpenter

Estos workloads usan `karpenter.sh/nodepool: karpenter-on-demand`:

- `devops-blackbox-exporter`: exporter stateless; seguro de recrear.
- `internal-sonarqube-postgres-exporter`: exporter stateless; seguro de recrear.

## En legacy/base

Estos workloads no deben forzarse a Karpenter en esta fase:

- `sonarqube`: single-replica/stateful y aplicacion sensible; se ajustaron recursos, pero no se movio a Karpenter.
- `internal-grafana`: una replica con PVC; queda en legacy/base por estabilidad simple.
- APISIX/ingress critico: no mover desde este POC.
- ArgoCD/controladores criticos: mantener fuera de Karpenter por ahora.

## Criterio

- Karpenter: exporters, demos, apps internas stateless y workloads que puedan reiniciarse sin impacto fuerte.
- Legacy/base: SonarQube, Grafana, Prometheus, Mimir/Tempo/Loki stateful single-replica, APISIX/ingress y controladores criticos.
- Si se quiere mover un workload nuevo, primero validar consumo real, replicas, PVC, PDB y si tolera recreacion por consolidacion.

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
