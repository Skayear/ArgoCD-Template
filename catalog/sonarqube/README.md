# sonarqube

Wrapper del chart oficial `SonarSource/sonarqube`. Análisis estático de calidad de código, usado como app de plataforma (ver el ejemplo completo en `clients/devops`: SonarQube + `catalog/dns-endpoints` + `catalog/certificates` + `catalog/apisix-routes` + `catalog/postgres-exporter`).

## Base de datos

Este chart **no** trae Postgres embebido para producción — se espera una base externa (RDS u otra), con las credenciales JDBC inyectadas vía `externalSecrets` (`secretStoreRef` + `remoteRef` a `sonarqube/db`) en vez de en texto plano. Ver `clients/devops/values/sonarqube.yaml` para el ejemplo completo de `jdbcOverwrite` + `externalSecrets`.

Las métricas de esa base se exponen aparte, con `catalog/postgres-exporter` apuntando a la misma instancia.

## Exposición

Queda `ClusterIP` + `ingress.enabled: false` — la exposición HTTP se resuelve con `catalog/apisix-routes` (gateway) en vez del `Ingress` propio del chart.
