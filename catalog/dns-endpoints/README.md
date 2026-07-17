# DNS Endpoints

Este catalogo renderiza recursos `DNSEndpoint` para que `external-dns` publique hostnames de aplicaciones que viven detras del gateway de APISIX.

## Caso de uso

Cuando una app no tiene su propio `LoadBalancer`, pero si necesita un hostname publico, se modela asi:

- `gateway.internal.example.com` lo mantiene `external-dns` desde el `Service` de APISIX
- `argocd.internal.example.com` o `sonarqube.internal.example.com` se crean con `DNSEndpoint`
- esos hostnames apuntan a `gateway.internal.example.com`

## Ejemplo

```yaml
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
```

## Advertencia

Si un hostname ya existe manualmente en Route53 con otro tipo de record, por ejemplo `A Alias`, primero hay que eliminar o migrar ese record para que `external-dns` pueda tomar control del nombre.
