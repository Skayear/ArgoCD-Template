# apisix-routes

Chart de recursos K8s directos (sin dependencias externas): genera `ApisixRoute` y `ApisixTls` para el ingress controller de APISIX declarado en `catalog/apisix`.

## Por qué existe separado de `apisix`

Cada cliente/app define sus propias rutas sin tocar el chart del gateway. `catalog/apisix` se despliega una sola vez por cluster; `apisix-routes` se instancia (con `releaseName` distinto) una vez por cada set de rutas que necesite un cliente.

## `privateAccessWhitelist`

Lista de CIDRs de referencia usada por el plugin `ip-restriction` cuando una ruta declara `privateAccess: true`. Reemplazar por las IPs/rangos reales que deben tener acceso (oficina, VPN, rangos internos) antes de usar en un ambiente real — los valores por defecto son de ejemplo (rango de documentación RFC 5737 + rangos privados).

## Ejemplo

```yaml
routes:
  enabled: true
  items:
    - name: example
      namespace: default
      ingressClassName: apisix
      privateAccess: false
      hosts:
        - example.internal.example.com
      paths:
        - "/*"
      backend:
        serviceName: example-service
        servicePort: 80
        resolveGranularity: service

tls:
  enabled: true
  items:
    - name: example-tls
      namespace: default
      ingressClassName: apisix
      hosts:
        - example.internal.example.com
      secret:
        name: example-tls
        namespace: default
```

`defaultPlugins` (por defecto solo `prometheus`) se aplica a **todas** las rutas de esta instancia del chart, además de los plugins propios de cada item.
