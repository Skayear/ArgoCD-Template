# Registro GitOps de Clusters EKS en Argo CD

## Objetivo

Registrar clusters EKS nuevos en Argo CD de forma declarativa, sin credenciales estaticas, y manteniendo el bootstrap centralizado en `clients/internal`.

## Resumen de la arquitectura

La solucion final quedo separada en 4 piezas:

1. `argocd-application-controller` en el cluster principal usa IRSA
2. esa identidad AWS asume una role destino en la cuenta del cluster remoto
3. el cluster remoto autoriza esa role con `Access Entry`
4. Argo registra el cluster remoto a traves de un `Secret` declarativo creado desde Git

Flujo:

```text
argocd-application-controller
  -> IAM role fuente
     -> sts:AssumeRole
        -> IAM role destino en la cuenta remota
           -> EKS Access Entry
              -> Argo CD puede usar el cluster remoto
```

## Convencion usada en este documento

Para evitar confusion:

- `source` = cuenta y cluster donde vive Argo CD
- `target` o `destino` = cuenta y cluster remoto que querés registrar en Argo

En este ejemplo concreto:

- `source account`: `111111111111`
- `source cluster`: cluster donde corre Argo CD
- `source role`: `internal-argocd-management-cluster-access`
- `target account`: `222222222222`
- `target cluster`: `example-app-eks-dev`
- `target role`: `argo-example-app-dev-cluster`

Pensalo asi:

- Argo corre en `source`
- Argo quiere administrar `target`

## Cambios hechos en el repo

### Catalogo nuevo

Se agrego:

- `catalog/argocd-clusters/Chart.yaml`
- `catalog/argocd-clusters/values.yaml`
- `catalog/argocd-clusters/templates/cluster-secret.yaml`
- `catalog/argocd-clusters/README.md`

Este catalogo crea `Secret` de tipo cluster para Argo CD usando el mecanismo oficial:

- `argocd.argoproj.io/secret-type: cluster`

### Template de aplicaciones por cliente

Se ajusto:

- `clients/internal/templates/applications.yaml`

Cambio importante:

```yaml
destination:
  namespace: {{ .namespace | default .name | quote }}
  server: {{ .destinationServer | default $config.spec.destination.server | quote }}
```

Con esto:

- una app puede seguir usando el destino default del cliente
- otra app puede apuntar a un cluster remoto especifico

### Bootstrap centralizado

Se centralizo en:

- `clients/internal/values.yaml`

Desde ahi ahora se manejan:

- `AppProject`
- registro de clusters
- componentes base de plataforma

## Roles, policies y access entry creados

## 1. Cuenta fuente

Cuenta donde vive el cluster principal y Argo CD:

- `111111111111`

### IAM role fuente

Nombre:

- `argocd-management-cluster-access`

Uso:

- la usa `argocd-application-controller` via IRSA

Tipo de role al crearla en AWS:

- `Web identity`

Porque:

- esta role la asume directamente el `ServiceAccount` de Kubernetes
- no la asume otra IAM role
- el trust se resuelve con OIDC/IRSA

ServiceAccount asociado:

- `system:serviceaccount:argocd:argocd-application-controller`

Valores concretos de `source` en este ejemplo:

- `source account id`: `111111111111`
- `source role name`: `argocd-management-cluster-access`
- `source role arn`: `arn:aws:iam::111111111111:role/argocd-management-cluster-access`
- `source service account`: `system:serviceaccount:argocd:argocd-application-controller`

Trust policy usada:

Esto se pega en:

- `Role -> Trust relationships -> Edit trust policy`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Principal": {
        "Federated": "arn:aws:iam::111111111111:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/C8754EE112D866D5B3F4E53156AA749C"
      },
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/C8754EE112D866D5B3F4E53156AA749C:sub": [
            "system:serviceaccount:argocd:argocd-application-controller"
          ],
          "oidc.eks.us-east-1.amazonaws.com/id/C8754EE112D866D5B3F4E53156AA749C:aud": [
            "sts.amazonaws.com"
          ]
        }
      }
    }
  ]
}
```

### Configuracion en Argo

Archivo:

- `argocd/values/custom_argo.yaml`

Bloque usado:

```yaml
controller:
  serviceAccount:
    annotations:
      eks.amazonaws.com/role-arn: arn:aws:iam::111111111111:role/argocd-management-cluster-access
```

### Permisos de la role fuente

La role fuente necesita poder asumir las roles destino de los clusters remotos.

Esto va en:

- `Role -> Permissions policies`
- puede ser como `inline policy` o `customer managed policy`

Patron minimo:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": [
        "arn:aws:iam::<REMOTE_ACCOUNT_ID>:role/<REMOTE_ARGO_ROLE>"
      ]
    }
  ]
}
```

## 2. Cuenta destino

Cuenta del cluster remoto Example App:

- `222222222222`

Cluster:

- `example-app-eks-dev`

### IAM role destino

Nombre:

- `argo-example-app-dev-cluster`

ARN:

- `arn:aws:iam::222222222222:role/argo-example-app-dev-cluster`

Tipo de role al crearla en AWS:

- `Another AWS account`

Account ID usado en la UI:

- `111111111111`

Porque:

- esta role la asume la role fuente `argocd-management-cluster-access`
- no la asume un pod directo
- por eso el principal de confianza es una IAM role de otra cuenta, no un OIDC provider

Trust policy usada:

Esto se pega en:

- `Role -> Trust relationships -> Edit trust policy`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:role/internal-argocd-management-cluster-access"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Policy minima usada:

- `eks:DescribeCluster`

Esto va en:

- `Role -> Permissions policies`
- puede ser como `inline policy` o `customer managed policy`

Ejemplo minimo:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster"
      ],
      "Resource": "*"
    }
  ]
}
```

Valores concretos de `target` en este ejemplo:

- `target account id`: `222222222222`
- `target cluster name`: `example-app-eks-dev`
- `target role name`: `argo-example-app-dev-cluster`
- `target role arn`: `arn:aws:iam::222222222222:role/argo-example-app-dev-cluster`

Plantilla generica para otro cluster:

- `target account id`: `<TARGET_ACCOUNT_ID>`
- `target cluster name`: `<TARGET_EKS_CLUSTER_NAME>`
- `target role name`: `argo-<cliente>-<env>-cluster`
- `target role arn`: `arn:aws:iam::<TARGET_ACCOUNT_ID>:role/argo-<cliente>-<env>-cluster`

## 3. Access Entry en EKS

Cluster:

- `example-app-eks-dev`

Principal:

- `arn:aws:iam::222222222222:role/argo-example-app-dev-cluster`

Tipo:

- `STANDARD`

Access policy asociada:

- `arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy`

Scope:

- `cluster`

## Registro del cluster en Argo

El registro declarativo quedo centralizado en:

- `clients/internal/values.yaml`

App usada:

- `argocd-clusters`

Wave:

- `-1`

Ejemplo real usado para Example App:

```yaml
- name: argocd-clusters
  namespace: argocd
  path: catalog/argocd-clusters
  project: default
  syncWave: "-1"
  valuesObject:
    clusters:
      enabled: true
      items:
        - name: admin-example-app-dev
          server: https://7C1DADF0916DA54A5B148B4748111CA1.gr7.us-east-1.eks.amazonaws.com
          project: internal
          config:
            awsAuthConfig:
              clusterName: example-app-eks-dev
              roleARN: arn:aws:iam::222222222222:role/argo-example-app-dev-cluster
            tlsClientConfig:
              insecure: false
              caData: <base64-ca>
```

## AppProject

El `AppProject` del cliente remoto se define tambien desde:

- `clients/internal/values.yaml`

Para `example-app`, el destino recomendado es solo el cluster remoto:

```yaml
destinations:
  - namespace: "*"
    server: https://7C1DADF0916DA54A5B148B4748111CA1.gr7.us-east-1.eks.amazonaws.com
```

El registro del cluster en si no usa el proyecto `example-app`; usa `project: internal` porque es bootstrap de plataforma.

## Pasos para agregar un cluster AWS nuevo

1. Crear o ajustar el `AppProject` del cliente en `clients/internal/values.yaml`
2. Crear la IAM role fuente en la cuenta donde vive Argo:
   - tipo `Web identity`
   - audience: `sts.amazonaws.com`
   - subject: `system:serviceaccount:argocd:argocd-application-controller`
3. Anotar `argocd-application-controller` con esa role fuente
4. Crear la IAM role destino en la cuenta remota:
   - tipo `Another AWS account`
   - account ID: `<SOURCE_ACCOUNT_ID>`
5. Configurar la trust policy de esa role destino para confiar en:
   - `arn:aws:iam::<SOURCE_ACCOUNT_ID>:role/<SOURCE_ROLE_NAME>`
6. Darle a la role fuente permiso:
   - `sts:AssumeRole` sobre la role destino
7. Darle a la role destino al menos:
   - `eks:DescribeCluster`
8. Crear el `Access Entry` en el cluster EKS remoto
9. Asociar una `cluster-access-policy`, por ejemplo para arranque:
   - `AmazonEKSClusterAdminPolicy`
10. Agregar un item nuevo en `clients/internal/values.yaml` dentro de la app `argocd-clusters`
11. Hacer sync del bootstrap `internal`
12. Verificar que aparezca el `Secret` de cluster en `argocd`

Checklist mental:

- en `source` creás la role que usa Argo
- en `target` creás la role que Argo va a asumir
- en `target` autorizás esa role con `Access Entry`
- en Git registrás el cluster remoto con endpoint, CA y `target role ARN`

## Datos que necesitás del cluster remoto

Del overview de EKS o por CLI:

- API server endpoint
- Certificate authority
- nombre real del cluster EKS

No usar:

- `Cluster IAM role ARN`
- `OIDC provider URL`

para el `Secret` del cluster, porque no son el `roleARN` que usa Argo para conectarse.

## Validaciones utiles

### Role fuente en el controller

```bash
kubectl get sa -n argocd argocd-application-controller -o yaml
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-application-controller -o yaml
```

Esperado:

- annotation `eks.amazonaws.com/role-arn`
- variables `AWS_ROLE_ARN` y `AWS_WEB_IDENTITY_TOKEN_FILE`

### Secret del cluster registrado

```bash
kubectl get secret -n argocd -l argocd.argoproj.io/secret-type=cluster
kubectl get secret -n argocd admin-example-app-dev-cluster -o yaml
```

### Access entry en EKS

```bash
aws eks list-access-entries --cluster-name example-app-eks-dev
aws eks describe-access-entry \
  --cluster-name example-app-eks-dev \
  --principal-arn arn:aws:iam::222222222222:role/argo-example-app-dev-cluster
```

## Troubleshooting

### `namespace argocd is not permitted in project 'example-app'`

Causa:

- el cluster registration se estaba asociando al proyecto `example-app`

Correccion:

- usar `project: internal` en el item de `argocd-clusters`

### `app path does not exist`

Causa:

- la app hija `argocd-clusters` quedo apuntando a una rama donde `catalog/argocd-clusters` no existe

Correccion:

- para pruebas, asegurar que el bootstrap y sus apps hijas apunten a la rama donde existe `catalog/argocd-clusters`
- o mergear el cambio a `main`

### `argocd-clusters` aparece con status `Unknown`

Hay dos causas posibles y ambas aparecieron durante esta implementacion:

1. La app hija estaba comparando contra `targetRevision: main` y en `main` todavia no existia `catalog/argocd-clusters`
2. El unico recurso manejado por `argocd-clusters` es un `Secret`, y Argo suele dejar ese recurso como `Unknown` a nivel de health/status de recurso

Pista importante:

- si el `Secret` existe en `argocd`
- y no hay errores de `AccessDenied` en el controller

entonces el `Unknown` de la app no implica necesariamente que el cluster remoto no haya quedado registrado

## Referencias oficiales

- Argo CD declarative clusters:
  - https://argo-cd.readthedocs.io/en/latest/operator-manual/declarative-setup/#clusters
- Argo CD cluster management:
  - https://argo-cd.readthedocs.io/en/latest/operator-manual/cluster-management/
- EKS access entries:
  - https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html
