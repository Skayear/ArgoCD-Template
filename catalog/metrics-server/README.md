# metrics-server

Wrapper del chart oficial `kubernetes-sigs/metrics-server`. Expone métricas de CPU/memoria de nodos y pods vía la Metrics API (`metrics.k8s.io`), que consumen `kubectl top` y cualquier `HorizontalPodAutoscaler` basado en CPU/memoria.

Sin este chart, cualquier `HorizontalPodAutoscaler` basado en CPU/memoria se queda sin métricas para escalar.
