<p align="center">
  <img src="https://raw.githubusercontent.com/argoproj/argo-cd/master/ui/src/assets/images/argo_o.svg" alt="Argo CD logo" width="180"/>
</p>

<h1 align="center">ArgoCD-Template</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Argo%20CD-EF7B4D?style=for-the-badge&logo=argo&logoColor=white" alt="Argo CD"/>
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white" alt="Kubernetes"/>
  <img src="https://img.shields.io/badge/Helm-0F1689?style=for-the-badge&logo=helm&logoColor=white" alt="Helm"/>
</p>

Plantilla base para levantar un ambiente nuevo en Kubernetes usando **Argo CD** con el patrón **App of Apps**, gestionando toda la plataforma (Argo CD mismo, add-ons de cluster, gateway, observabilidad, certificados, DNS, autoscaling, secretos) como código versionado en Git.

Este repo es una extracción genérica de una plataforma real en producción, con todos los datos específicos de esa organización (cuentas de nube, dominios, secretos, nombres de clientes) reemplazados por placeholders. Antes de usarlo hay que completar esos placeholders con los valores reales de tu entorno.

## Arquitectura

```
ArgoCD-Template/
├── argocd/                 # Cómo instalar Argo CD mismo (Helm values + runbooks)
│   ├── values/custom_argo.yaml
│   ├── Plan_Argo.md
│   ├── plan_sso.md
│   ├── troubleshooting.md
│   └── apisix-architecture-notes.md
├── catalog/                 # Charts Helm reutilizables y parametrizables (el "qué")
│   ├── cert-manager/ external-dns/ external-secrets-aws/ karpenter/ ...
│   └── argocd-projects/ argocd-clusters/ ...
├── clients/                  # App of Apps por cliente/ambiente (el "cómo" y "con qué valores")
│   ├── README.md              # explica el patrón en detalle
│   ├── devops/                 # ejemplo: bootstrap de plataforma cross-cluster
│   └── internal/                # ejemplo: add-ons del cluster donde vive Argo CD
├── .github/workflows/       # Deploy de Argo CD, toggle de admin, validaciones de CI (ver README propio)
└── scripts/                  # Validaciones usadas por los workflows
```

El flujo es de **2 niveles**, sin Applications intermedias:

```
clients/<cliente>/<ambiente>  →  ArgoCD Application  →  catalog/<chart>  →  recursos K8s
```

Ver [`clients/README.md`](clients/README.md) para la explicación completa del patrón (bootstrap, sync waves, cómo agregar un cliente/ambiente nuevo, cómo agregar un chart al catálogo).

## Cómo levantar un ambiente nuevo

1. **Instalar Argo CD.**
   Completá los placeholders de [`argocd/values/custom_argo.yaml`](argocd/values/custom_argo.yaml) (dominio, OIDC de tu proveedor de identidad, RBAC, `role-arn`/`client-id` de tu cloud) y desplegalo con Helm — manualmente o vía [`.github/workflows/eks_argocd_deploy.yml`](.github/workflows/eks_argocd_deploy.yml) si tu cluster es EKS.
   Ver [`argocd/Plan_Argo.md`](argocd/Plan_Argo.md) para el plan paso a paso y [`argocd/plan_sso.md`](argocd/plan_sso.md) para SSO/OIDC.

2. **Bootstrap del cluster donde vive Argo CD.**
   Aplicá manualmente (una sola vez) una Application raíz apuntando a [`clients/internal`](clients/internal) — instala `argocd-projects`, el gateway, cert-manager, external-dns, external-secrets, etc. Completá antes los placeholders en `clients/internal/values/*.yaml` (dominio, VPC, cuenta de nube, ARNs de IAM).

3. **Bootstrap de plataforma cross-cluster.**
   Igual que el paso anterior, apuntando a [`clients/devops`](clients/devops) — registra clusters remotos (`catalog/argocd-clusters`), Karpenter, y cualquier app de plataforma (el ejemplo incluye SonarQube).

4. **Agregar un cliente/ambiente real.**
   Copiá la estructura de `clients/devops` o `clients/internal` a `clients/<tu-cliente>/<ambiente>`, definí sus `applications` en `values.yaml` apuntando a charts de `catalog/`, y aplicá el bootstrap una sola vez. Instrucciones detalladas en [`clients/README.md`](clients/README.md#agregar-un-nuevo-cliente-o-ambiente).

## Seguridad

- **Nunca** pongas credenciales en texto plano en `values.yaml`. El patrón de este repo es usar `external-secrets` (`catalog/external-secrets-aws`, `catalog/external-secrets`) para inyectar secrets desde AWS Secrets Manager u otro backend, referenciados vía `ExternalSecret`/`ClusterSecretStore`. `clients/devops/values/clusters.yaml` muestra el patrón recomendado para registrar clusters remotos sin credenciales en Git.
- Todos los placeholders (`<AWS_ACCOUNT_ID>`, `<AZURE_TENANT_ID>`, `example.com`, IDs con `0`/`1` repetidos, etc.) deben reemplazarse por los valores reales de tu organización antes de desplegar.
- `Chart.lock` se commitea para que Argo CD pueda resolver dependencias sin acceso a red arbitrario; después de tocar un `Chart.yaml` con dependencias, correr `helm dependency update catalog/<chart>/`.

## Pipelines

Ver [`.github/workflows/README.md`](.github/workflows/README.md) para qué hace cada workflow (deploy de Argo CD, toggle de admin, validación de `targetRevision`).

## Troubleshooting

Ver [`argocd/troubleshooting.md`](argocd/troubleshooting.md) para problemas comunes de integración con OIDC, RBAC por grupos y el gateway/ingress.

## Pendientes

Ver [`TODO.md`](TODO.md) — por ahora, la reincorporación de Argo CD Image Updater al catálogo.
