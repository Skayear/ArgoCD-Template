# aws-load-balancer-controller

Wrapper del chart oficial `eks-charts/aws-load-balancer-controller`. Instala el controller que crea ALBs/NLBs de AWS a partir de `Ingress`/`Service type: LoadBalancer` con las annotations `service.beta.kubernetes.io/aws-load-balancer-*`.

## CRDs

Las CRDs upstream (`files/aws-load-balancer-controller-crds.yaml`) se empaquetan explícitamente como manifiestos propios del chart (`templates/crds.yaml`) en vez de dejar que las instale el subchart, para que Argo CD las gestione como recursos normales y no se dupliquen entre el chart y la Application.

## Requisitos antes de habilitarlo

- IRSA: el `serviceAccount` necesita el rol de IAM con la policy de `aws-load-balancer-controller` (ver `clients/internal/values/aws-load-balancer-controller.yaml` para el ejemplo de `role-arn`)
- `clusterName` y `vpcId` del cluster EKS destino

Es un prerequisito de `catalog/apisix` (y de cualquier otro `Service type: LoadBalancer`/`Ingress` sobre ALB) — sin este controller esos recursos se quedan sin balanceador real.
