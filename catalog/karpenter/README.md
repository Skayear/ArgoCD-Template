# karpenter

Wrapper del chart oficial `oci://public.ecr.aws/karpenter/karpenter`. Instala el controller que provisiona/desprovisiona nodos EC2 en base a los `NodePool`/`EC2NodeClass` declarados en `catalog/karpenter-nodepools`.

## Requiere

- `catalog/crds/karpenter-crd` ya instalado (un `syncWave` antes)
- `karpenter.settings.clusterName` y `karpenter.settings.interruptionQueue` (cola SQS para spot interruption) apuntando al cluster real
- IRSA en el `serviceAccount` con permisos para crear/terminar instancias EC2, pasar el rol de `EC2NodeClass`, etc.

```yaml
karpenter:
  settings:
    clusterName: my-eks-cluster
    interruptionQueue: Karpenter-my-eks-cluster
  serviceAccount:
    create: true
    name: karpenter
```

Sin `catalog/karpenter-nodepools` este controller queda instalado pero sin ningún `NodePool` que le diga qué tipo de nodos levantar.
