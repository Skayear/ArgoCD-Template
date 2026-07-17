# karpenter-crd

Wrapper del chart oficial `oci://public.ecr.aws/karpenter/karpenter-crd`. Instala únicamente las CRDs de Karpenter (`NodePool`, `EC2NodeClass`, `NodeClaim`).

Va separado del controller (`catalog/karpenter`) a propósito: las CRDs se sincronizan con `syncWave` anterior al controller y a los `NodePool`/`EC2NodeClass` (ver `clients/devops/values.yaml`, wave `-1`), para que el CRD exista en el cluster antes de que Argo intente crear o validar cualquier recurso que dependa de él.
