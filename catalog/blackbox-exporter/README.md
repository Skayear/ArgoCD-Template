# blackbox-exporter

Wrapper chart para desplegar `prometheus-blackbox-exporter` y declarar probes
HTTP/TCP descubiertos por `kube-prometheus-stack`.

El modelo es intencionalmente simple:

- 1 `ServiceMonitor`
- muchos `targets`
- 1 scrape config por target dentro del mismo monitor

Eso evita multiplicar objetos de Kubernetes cuando tengas muchos endpoints que
vigilar.

El chart queda deshabilitado por defecto. Cada cliente debe habilitarlo desde su
`valuesObject` y definir todos los targets que quiere monitorear en una sola
lista.

Ejemplo:

```yaml
enabled: true
prometheus-blackbox-exporter:
  serviceMonitor:
    selfMonitor:
      labels:
        release: internal-prometheus-stack
    enabled: true
    defaults:
      labels:
        release: internal-prometheus-stack
      module: http_2xx
      interval: 30s
      scrapeTimeout: 10s
    targets:
      - name: grafana-internal
        url: https://grafana.internal.example.com/
        labels:
          release: internal-prometheus-stack
          service: grafana
          environment: internal
      - name: sonarqube-internal
        url: https://sonarqube.internal.example.com/
        labels:
          release: internal-prometheus-stack
          service: sonarqube
          environment: internal
```
