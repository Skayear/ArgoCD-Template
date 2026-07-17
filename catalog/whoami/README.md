# whoami

Chart mínimo para desplegar [`traefik/whoami`](https://github.com/traefik/whoami) — un servicio HTTP de eco que devuelve request headers, IP, hostname del pod, etc. Sin dependencias externas, sin subchart.

## Para qué sirve

Es el target de referencia para probar el resto del catálogo sin depender de una app real:

- validar que `catalog/apisix-routes` enruta bien un host/path hacia un `Service`
- validar que `catalog/certificates`/`catalog/clusterissuers` emiten un certificado usable
- probar el flujo completo de un bootstrap nuevo (`clients/<cliente>/<ambiente>`) de punta a punta antes de conectarle una app de negocio real

Ver el ejemplo de uso en [`clients/README.md`](../../clients/README.md).
