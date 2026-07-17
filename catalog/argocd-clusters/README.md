# Argo CD Clusters

Este catalogo registra clusters en Argo CD de forma declarativa usando `Secret` con label:

- `argocd.argoproj.io/secret-type: cluster`

Es el mecanismo oficial de Argo CD para cluster registration via GitOps.

## Como funciona

Cada cluster se modela como un `Secret` en el namespace `argocd`.

Campos principales:

- `name`
- `server`
- `namespaces` opcional
- `clusterResources` opcional
- `project` opcional
- `config`

El campo `config` se pasa como objeto YAML en values y el chart lo renderiza como JSON dentro de `stringData.config`, que es lo que Argo CD espera.

## Ejemplo minimo

```yaml
clusters:
  enabled: true
  items:
    - name: test-eks
      server: https://ABCDEF.gr7.us-east-1.eks.amazonaws.com
      project: internal
      config:
        awsAuthConfig:
          clusterName: test-eks
          roleARN: arn:aws:iam::123456789012:role/argocd-target-cluster
        tlsClientConfig:
          insecure: false
          caData: <base64-ca>
```

## Ejemplo con restriccion de namespaces

```yaml
clusters:
  enabled: true
  items:
    - name: client-a
      server: https://client-a.example.com
      namespaces:
        - app-a
        - app-b
      clusterResources: true
      project: example-app
      config:
        bearerToken: <token>
        tlsClientConfig:
          insecure: false
          caData: <base64-ca>
```

## Ejemplo AKS con execProviderConfig

```yaml
clusters:
  enabled: true
  items:
    - name: aks-prod
      server: https://aks-prod.example.com
      project: internal
      config:
        execProviderConfig:
          command: argocd-k8s-auth
          args:
            - azure
          apiVersion: client.authentication.k8s.io/v1beta1
          env:
            AAD_ENVIRONMENT_NAME: AzurePublicCloud
            AAD_LOGIN_METHOD: workloadidentity
            AZURE_CLIENT_ID: <client-id>
            AZURE_TENANT_ID: <tenant-id>
        tlsClientConfig:
          insecure: false
          caData: <base64-ca>
```

## Uso recomendado en este repo

1. Crear una app de composicion, por ejemplo:
   - `argocd-clusters`
2. Pasar `clusters.items` desde `clients/<cliente>/values.yaml`
3. Mantener credenciales sensibles protegidas si hace falta, por ejemplo con Sealed Secrets o External Secrets

## Referencias oficiales

- Declarative cluster setup:
  - https://argo-cd.readthedocs.io/en/latest/operator-manual/declarative-setup/#clusters
- Cluster management:
  - https://argo-cd.readthedocs.io/en/latest/operator-manual/cluster-management/
