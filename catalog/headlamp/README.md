# headlamp

Wrapper del chart oficial `kubernetes-sigs/headlamp`. UI web para explorar recursos del cluster (alternativa liviana al dashboard de Kubernetes), pensada para correr `inCluster` con su propio `serviceAccount` de solo lectura.

## Plugin de Karpenter

`karpenterReadOnlyClusterRole` crea un `ClusterRole` adicional (`get/list/watch` sobre workloads estándar + `karpenter.sh/nodepools`, `nodeclaims`, `ec2nodeclasses`) para que el plugin de Karpenter de Headlamp pueda mostrar `NodePool`/`NodeClaim` sin darle permisos de escritura sobre nada.

## Notas

- `unsafeUseServiceAccountToken: false` — no usa el token del service account del propio pod para autenticar al usuario; espera OIDC (`config.oidc`) o el flujo normal de login de Headlamp.
- `pluginsManager` (apagado por defecto): si se habilita, permite instalar plugins adicionales (más allá del de Karpenter) sin rebuildear la imagen.
