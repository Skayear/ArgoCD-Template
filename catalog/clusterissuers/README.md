# clusterissuers

Chart de recursos K8s directos: genera `ClusterIssuer` (`cert-manager.io`) para emisión automática de certificados vía ACME (Let's Encrypt), con el challenge DNS-01 resuelto contra **AWS Route53** o **Azure DNS** según `dnsProvider`.

Requiere que `catalog/cert-manager` ya esté instalado.

## AWS (Route53)

```yaml
clusterIssuers:
  enabled: true
  items:
    - name: letsencrypt-prod
      email: sre@example.com
      server: https://acme-v02.api.letsencrypt.org/directory
      privateKeySecretRef: letsencrypt-prod
      dnsProvider: aws
      region: us-east-1
      iamRole: arn:aws:iam::<AWS_ACCOUNT_ID>:role/cert-manager-route53
      serviceAccount: cert-manager
```

`iamRole` + `serviceAccount` usan IRSA (sin credenciales estáticas). Si en cambio se omite `iamRole`, el template cae al modo `accessKeyID` + `credentialsSecretName` (ver `templates/clusterissuer.yaml`).

## Azure (Azure DNS)

```yaml
clusterIssuers:
  enabled: true
  items:
    - name: letsencrypt-prod-azure
      email: sre@example.com
      server: https://acme-v02.api.letsencrypt.org/directory
      privateKeySecretRef: letsencrypt-prod-azure
      dnsProvider: azure
      hostedZoneName: example.com
      resourceGroupName: my-resource-group
      subscriptionID: <AZURE_SUBSCRIPTION_ID>
      clientID: <AZURE_MANAGED_IDENTITY_CLIENT_ID>
```

`dnsProvider` distinto de `aws`/`azure` hace fallar el render explícitamente (`fail`) — no hay default silencioso.
