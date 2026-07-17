# TODO

## Investigar: Argo CD Image Updater

Se sacaron del template `catalog/argocd-image-updater`, `catalog/sentinel` (probable bot de escritura a Git) y el workflow `auto-approve-image-updater.yml`, porque el diseño de referencia traía deuda técnica específica del repo de origen. Antes de reincorporarlos:

- [ ] **Autenticación con ECR.** La referencia original resolvía la falta de credential helper en la imagen oficial con un initContainer Alpine + `apk --usermode` (workaround manual). Revisar si versiones más nuevas de `argocd-image-updater` ya traen soporte nativo de ECR, o si hay una alternativa más simple.
- [ ] **Estrategia de write-back a Git.** El original abría PR contra `main` (por reglas de rama) y necesitaba un bot separado para auto-aprobar, porque GitHub no deja aprobar un PR con el mismo token que lo abrió. Evaluar: ¿mantener PR + auto-approve, o hacer write-back directo a una rama que no sea `main` para evitar el problema por completo?
- [ ] **Identidad del bot.** Si se mantiene el patrón de bot separado, definirlo explícitamente (no inferido de un secret llamado `sentinel-runtime` como en el original) y documentar cómo se gestiona su token (`ExternalSecret`, rotación, permisos mínimos).
- [ ] **Multi-registry / multi-nube.** La referencia solo cubre ECR. Ver si conviene soporte genérico para GCR/ACR/Docker Hub antes de meterlo al catálogo.
- [ ] **`allowed_pattern` reusable.** El guardrail que valida qué archivos puede tocar el write-back estaba hardcodeado por cliente. Pensar un patrón parametrizable por `values.yaml` en vez de editar el workflow a mano.

Cuando esto esté resuelto, reagregar como `catalog/argocd-image-updater` (+ el chart de identidad del bot si hace falta) y el workflow correspondiente en `.github/workflows/`, documentando ambos con su README.
