# postgres-exporter

Wrapper para `prometheus-postgres-exporter`.

La idea es:

- `catalog/postgres-exporter` queda agnóstico
- el cliente define host, base, usuario, secret y `ServiceMonitor`

Caso actual:

- `internal` lo usa para la base externa de `sonarqube`
