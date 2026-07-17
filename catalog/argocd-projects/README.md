# argocd-projects

Chart de recursos K8s directos: genera `AppProject` (`argoproj.io`) a partir de una lista en `values.yaml`. Es el primer chart que se sincroniza en cualquier bootstrap (`syncWave: "-1"` en `clients/devops`/`clients/internal`) — todas las demás `Application` referencian un `project` que tiene que existir de antes.

```yaml
projects:
  enabled: true
  items:
    - name: my-project
      description: Proyecto para mi cliente/ambiente.
      sourceRepos:
        - '*'
      destinations:
        - namespace: '*'
          server: https://kubernetes.default.svc
      clusterResourceWhitelist:
        - group: '*'
          kind: '*'
      namespaceResourceWhitelist:
        - group: '*'
          kind: '*'
```

Ver `clients/devops/values/projects.yaml` para el patrón real: un proyecto por cluster/ambiente, con `destinations[].server` apuntando al cluster remoto correspondiente (registrado en `catalog/argocd-clusters`).
