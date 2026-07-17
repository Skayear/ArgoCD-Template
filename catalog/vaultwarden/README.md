# vaultwarden

Chart propio (no wrapper de un chart de terceros) para desplegar [Vaultwarden](https://github.com/dani-garcia/vaultwarden) (implementación compatible con Bitwarden) con MySQL opcional embebido.

## Base de datos

Dos modos, mutuamente excluyentes:

- `mysql.enabled: true` → despliega un MySQL propio (`Deployment` + `PVC` + `Service`) dentro del mismo release — pensado para instancias chicas, no HA.
- `externalDatabase.*` → apunta a una base externa ya existente.

## Persistencia y config

- `app.persistence`: PVC para los datos de Vaultwarden (adjuntos, attachments) — deshabilitado por defecto, hay que prenderlo y darle `storageClassName`/`size` explícitos para no perder datos ante un restart del pod.
- `app.secrets`/`app.configmaps` + `externalSecrets`: igual que el resto del catálogo, las credenciales (SMTP, admin token) se inyectan vía `ExternalSecret`, no en `values.yaml`.
- `strategy.type: Recreate`: con un PVC `ReadWriteOnce` de por medio, evita el mismo problema de rollout atascado que `catalog/grafana`.

## Probes

`readinessProbe`/`livenessProbe` apuntan a `/alive`, el healthcheck propio de Vaultwarden.
