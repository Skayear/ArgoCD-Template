# Workflows

Pipelines de GitHub Actions para instalar/operar Argo CD sobre EKS y mantener sano el repo GitOps. Todos (salvo `validate_target_revisions.yml`) requieren un `environment` de GitHub (por defecto `devops`) con las variables/secrets de AWS configurados.

## `eks_argocd_deploy.yml`

**Manual (`workflow_dispatch`).** Instala o actualiza Argo CD en el cluster EKS vía Helm.

1. Carga `EKS_CLUSTER_NAME`, `AWS_REGION` y `K8S_NAMESPACE` desde las variables del environment `devops`.
2. Llama al reusable `reusable_eks_get_context.yml` para validar que el cluster es alcanzable antes de desplegar.
3. Se autentica en AWS, hace `aws eks update-kubeconfig` y corre:
   ```
   helm upgrade --install argocd argo/argo-cd -f ./argocd/values/custom_argo.yaml --create-namespace
   ```

Es el punto de entrada para el paso 1 de ["Cómo levantar un ambiente nuevo"](../../README.md#cómo-levantar-un-ambiente-nuevo) del README raíz. Se corre a mano cada vez que cambia `argocd/values/custom_argo.yaml` (RBAC, OIDC, recursos, etc.).

## `reusable_eks_get_context.yml`

**Reusable (`workflow_call`) y también invocable a mano.** No instala nada: valida que se puede llegar al cluster antes de operar sobre él.

1. Verifica que estén los inputs (`cluster_name`, `aws_region`) y las credenciales AWS.
2. Configura AWS, instala `kubectl`, corre `aws eks update-kubeconfig`.
3. Corre chequeos de diagnóstico: `aws sts get-caller-identity`, `aws eks get-token`, `kubectl auth can-i`, `kubectl get pods`.

Lo usa `eks_argocd_deploy.yml` como pre-chequeo. Sirve también standalone para debuggear "¿por qué GitHub Actions no puede hablar con mi EKS?" sin tocar el cluster.

## `argocd-admin-toggle.yml`

**Manual (`workflow_dispatch`).** Prende o apaga el usuario `admin` local de Argo CD (`admin.enabled` en el ConfigMap `argocd-cm`) sin pasar por Helm.

Inputs: `action` (`enable`/`disable`) y `namespace` (default `argocd`). Útil como vía de escape cuando el SSO/OIDC está roto y hace falta entrar como admin para diagnosticar — habilitarlo, resolver el problema, y volver a deshabilitarlo con el mismo workflow.

## `validate_target_revisions.yml`

**Automático, en todo PR hacia `main`** (y manual). Corre `scripts/check_target_revisions.py`, que recorre todos los `clients/**/values.yaml` y falla el PR si algún `config.spec.source.targetRevision` no es `main`.

Existe para evitar mergear a `main` un `values.yaml` que quedó apuntando a una rama de feature/test — algo fácil de olvidar y que Argo CD sincronizaría igual, silenciosamente, desde una rama que no debería estar en producción. Si de verdad hace falta una excepción temporal, el propio `values.yaml` puede declarar:

```yaml
ci:
  allowNonMainTargetRevision: true
  allowNonMainTargetRevisionReason: "motivo"
```
