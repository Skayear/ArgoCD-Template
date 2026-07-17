# ExternalDNS

## Objetivo

Este componente instala `external-dns` de forma agnostica al cloud para que la gestion DNS quede modelada desde Kubernetes.

En este modelo hay dos capas:

- `gateway.internal.example.com`
  - lo publica `external-dns` desde el `Service` de APISIX
- los hostnames de aplicaciones
  - se publican con recursos `DNSEndpoint`
  - apuntan a `gateway.internal.example.com`

Con eso, si cambia el NLB de APISIX, solo cambia el gateway. Las apps siguen colgando del mismo nombre estable.

## Como quedo modelado en el repo

### Componente base

Ruta:

- `catalog/external-dns`

Responsabilidad:

- instala `external-dns`
- configura `sources: service,crd`
- habilita `DNSEndpoint`
- deja el provider y las credenciales para que cada cliente las defina

### Catalogo de registros de apps

Ruta:

- `catalog/dns-endpoints`

Responsabilidad:

- renderiza recursos `DNSEndpoint`
- publica hostnames de aplicaciones hacia `gateway.internal.example.com`

### Composicion del cliente

Ruta:

- `clients/internal/values.yaml`

Apps involucradas:

- `external-dns`
- `dns-endpoints`

## Que define el catalogo y que define el cliente

### En `catalog/external-dns`

Se deja solo lo comun:

- `sources: service,crd`
- `managedRecordTypes: A,CNAME`
- `policy: upsert-only`
- `registry: txt`
- soporte para `DNSEndpoint`

No queda hardcodeado:

- `provider.name`
- `domainFilters`
- `txtOwnerId`
- annotations del `ServiceAccount`
- labels del pod o del `ServiceAccount`
- `extraArgs` especificos del provider
- `env`
- `extraVolumes`
- `extraVolumeMounts`

### En `clients/<cliente>/values.yaml`

Cada cliente define lo especifico de su cloud o de su zona DNS, por ejemplo:

- `provider.name`
- `domainFilters`
- `txtOwnerId`
- identidad o credenciales
- `extraArgs` del provider
- secretos o mounts necesarios

## Como funciona

### 1. Gateway

El `Service` `apisix-gateway` tiene esta annotation:

```yaml
external-dns.alpha.kubernetes.io/hostname: gateway.internal.example.com
```

Entonces `external-dns` crea o actualiza:

- `gateway.internal.example.com`

apuntando al `LoadBalancer` de APISIX.

### 2. Aplicaciones

Cada app nueva que viva detras de APISIX se publica con un `DNSEndpoint`.

Ese `DNSEndpoint` crea un `CNAME` hacia:

- `gateway.internal.example.com`

APISIX recibe la request y la enruta por `Host`.

## Ejemplo actual del cliente interno en AWS

En `clients/internal/values.yaml` hoy se pasa este bloque:

```yaml
- name: external-dns
  namespace: external-dns
  path: catalog/external-dns
  project: internal
  syncWave: "0"
  valuesObject:
    enabled: true
    external-dns:
      provider:
        name: aws
      domainFilters:
        - internal.example.com
      txtOwnerId: example-cluster
      serviceAccount:
        annotations:
          eks.amazonaws.com/role-arn: arn:aws:iam::111111111111:role/external-dns-route53
      extraArgs:
        aws-zone-type: public
```

Para que esto funcione en EKS con Route53 hacen falta:

1. una IAM Policy para Route53
2. una IAM Role con IRSA
3. el ARN de esa role anotado en el `ServiceAccount` de `external-dns`

### IAM Policy

Nombre sugerido:

- `example-cluster-external-dns-route53-policy`

Descripcion sugerida:

- `Allows ExternalDNS running in EKS to manage Route53 records for internal.example.com`

Policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "route53:ChangeResourceRecordSets"
      ],
      "Resource": [
        "arn:aws:route53:::hostedzone/Z10234116VSX286O3J0M"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "route53:ListHostedZones",
        "route53:ListResourceRecordSets",
        "route53:ListTagsForResource"
      ],
      "Resource": [
        "*"
      ]
    }
  ]
}
```

### IAM Role

Role usada:

- `external-dns-route53`

OIDC provider del cluster:

- `oidc.eks.us-east-1.amazonaws.com/id/C8754EE112D866D5B3F4E53156AA749C`

Subject del `ServiceAccount`:

```text
system:serviceaccount:external-dns:external-dns
```

Trust policy:

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
            "system:serviceaccount:external-dns:external-dns"
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

## Ejemplo practico: nueva app `testdns`

Supongamos que queres publicar:

- `testdns.internal.example.com`

La app ya tiene que existir detras de APISIX, con su `ApisixRoute` y, si corresponde, su `ApisixTls`.

Despues agregas un item nuevo en la app `dns-endpoints` dentro de:

- `clients/internal/values.yaml`

Ejemplo:

```yaml
- name: dns-endpoints
  namespace: argocd
  path: catalog/dns-endpoints
  project: internal
  syncWave: "1"
  valuesObject:
    dnsEndpoints:
      enabled: true
      items:
        - name: argocd-dns
          namespace: argocd
          endpoints:
            - dnsName: argocd.internal.example.com
              recordTTL: 300
              recordType: CNAME
              targets:
                - gateway.internal.example.com
        - name: testdns-dns
          namespace: testdns
          endpoints:
            - dnsName: testdns.internal.example.com
              recordTTL: 300
              recordType: CNAME
              targets:
                - gateway.internal.example.com
```

Cuando Argo sincroniza:

1. se crea el recurso `DNSEndpoint`
2. `external-dns` lo detecta
3. Route53 crea:
   - `testdns.internal.example.com -> gateway.internal.example.com`
4. APISIX recibe el host `testdns.internal.example.com`
5. APISIX enruta al backend que corresponda

## Validacion

### Ver la app `external-dns`

```bash
kubectl get application -n argocd external-dns
```

### Ver la app `dns-endpoints`

```bash
kubectl get application -n argocd dns-endpoints
```

### Ver recursos `DNSEndpoint`

```bash
kubectl get dnsendpoints.externaldns.k8s.io -A
```

### Ver logs

```bash
kubectl logs -n external-dns deploy/external-dns --tail=200
```

Deberias ver:

- `Sources:[service crd]`
- `CRDSourceKind:DNSEndpoint`
- `ManagedDNSRecordTypes:[A CNAME]`
- mensajes de reconciliacion sin `AccessDenied`

### Ver record en Route53

```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id Z10234116VSX286O3J0M \
  --query "ResourceRecordSets[?Name=='testdns.internal.example.com.']"
```

## Nota importante

Si un hostname ya existe manualmente en Route53 con otro tipo de record, por ejemplo `A Alias`, primero hay que eliminar o migrar ese record para que `external-dns` pueda tomar control del nombre como `CNAME`.

## Ejemplo equivalente si el provider fuera Azure

El modelo no cambia:

- `gateway.internal.example.com` sigue siendo el hostname estable del gateway
- las apps siguen publicandose con `DNSEndpoint`
- APISIX sigue ruteando por `Host`

Lo que cambia es:

- el provider de `external-dns`
- la forma de autenticarse
- los permisos sobre la zona DNS

### Permisos en Azure

Segun la documentacion oficial de `external-dns`, la identidad usada por `external-dns` debe tener como minimo:

- `DNS Zone Contributor` sobre la zona DNS
- `Reader` sobre el resource group que contiene la zona

Si se usa Workload Identity, tambien hace falta la federacion entre el `ServiceAccount` de Kubernetes y la managed identity de Azure.

### Secret de configuracion para Azure

La documentacion oficial muestra un `Secret` con un `azure.json` parecido a este:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: external-dns-azure
  namespace: external-dns
type: Opaque
stringData:
  azure.json: |
    {
      "subscriptionId": "<SUBSCRIPTION_ID>",
      "resourceGroup": "<AZURE_DNS_RESOURCE_GROUP>",
      "useWorkloadIdentityExtension": true
    }
```

### Ejemplo de values para Azure

```yaml
enabled: true

external-dns:
  provider:
    name: azure

  sources:
    - service
    - crd

  managedRecordTypes:
    - A
    - CNAME

  domainFilters:
    - internal.example.com

  policy: upsert-only
  registry: txt
  txtOwnerId: example-cluster

  serviceAccount:
    create: true
    name: external-dns
    labels:
      azure.workload.identity/use: "true"
    annotations:
      azure.workload.identity/client-id: "<AZURE_MANAGED_IDENTITY_CLIENT_ID>"

  podLabels:
    azure.workload.identity/use: "true"

  extraVolumes:
    - name: azure-config-file
      secret:
        secretName: external-dns-azure

  extraVolumeMounts:
    - name: azure-config-file
      mountPath: /etc/kubernetes
      readOnly: true
```

En este caso, lo que cambia vive solo en el `client`:

- `provider.name: azure`
- labels y annotations para Workload Identity
- `extraVolumes` y `extraVolumeMounts` para `azure.json`

El catalogo reusable no cambia.

### Que se mantiene igual

El `DNSEndpoint` para una app nueva, por ejemplo `testdns`, queda exactamente igual:

```yaml
apiVersion: externaldns.k8s.io/v1alpha1
kind: DNSEndpoint
metadata:
  name: testdns-dns
  namespace: testdns
spec:
  endpoints:
    - dnsName: testdns.internal.example.com
      recordTTL: 300
      recordType: CNAME
      targets:
        - gateway.internal.example.com
```

O sea:

- en AWS cambia Route53 + IRSA
- en Azure cambia Azure DNS + Workload Identity
- pero el patron funcional `gateway + DNSEndpoint + APISIX` se mantiene

## Referencias oficiales

- ExternalDNS chart docs:
  - https://kubernetes-sigs.github.io/external-dns/latest/charts/external-dns/
- ExternalDNS CRD source (`DNSEndpoint`):
  - https://kubernetes-sigs.github.io/external-dns/latest/docs/sources/crd/
- ExternalDNS CRD tutorial:
  - https://kubernetes-sigs.github.io/external-dns/latest/docs/tutorials/crd/
- ExternalDNS Azure tutorial:
  - https://kubernetes-sigs.github.io/external-dns/v0.13.4/tutorials/azure/
