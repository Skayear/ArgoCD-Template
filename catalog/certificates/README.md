# certificates

Chart de recursos K8s directos: genera objetos `Certificate` (`cert-manager.io`) individuales contra un `ClusterIssuer` ya existente (ver `catalog/clusterissuers`).

Se instancia una vez por cada hostname que necesita su propio certificado (a diferencia de `clusterissuers`, que es 1 por cluster).

```yaml
certificates:
  enabled: true
  items:
    - name: my-app-internal-example-com
      namespace: my-app
      secretName: my-app-internal-example-com-tls
      issuerRef:
        name: letsencrypt-prod
        kind: ClusterIssuer
      dnsNames:
        - my-app.internal.example.com
```

`secretName` es el `Secret` de tipo `kubernetes.io/tls` que cert-manager va a mantener actualizado; ese es el nombre que después referencia el `ApisixTls`/`Ingress` correspondiente (ver `catalog/apisix-routes`, bloque `tls`).

Los recursos se crean con `argocd.argoproj.io/sync-wave: "1"`, un wave después del `ClusterIssuer` del que dependen.
