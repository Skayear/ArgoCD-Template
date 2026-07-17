# karpenter-nodepools

Chart de recursos K8s directos: genera `EC2NodeClass` y `NodePool` (`karpenter.sh`/`karpenter.k8s.aws`) a partir de listas declarativas en `values.yaml`. Requiere que `catalog/karpenter-crd` y `catalog/karpenter` ya estén instalados.

## Ejemplo

```yaml
ec2NodeClasses:
  enabled: true
  items:
    - name: default
      role: KarpenterNodeRole-my-eks-cluster
      amiFamily: AL2023
      amiSelectorTerms:
        - id: ami-xxxxxxxxxxxxxxxxx
      subnetSelectorTerms:
        - tags:
            karpenter.sh/discovery: my-eks-cluster
      securityGroupSelectorTerms:
        - tags:
            karpenter.sh/discovery: my-eks-cluster

nodePools:
  enabled: true
  items:
    - name: karpenter-on-demand
      nodeClassRef:
        name: default
      taints:
        - key: workload.example/nodepool
          value: karpenter-general
          effect: NoSchedule
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
      limits:
        cpu: "16"
        memory: 64Gi
      disruption:
        consolidationPolicy: WhenEmptyOrUnderutilized
        consolidateAfter: 5m
```

Cada `NodePool` puede tener `taints`, así que los workloads que quieran caer ahí necesitan la `toleration` correspondiente (ver el patrón `workload.example/nodepool` usado en varios `values.yaml` de `clients/internal` y `clients/devops`).
