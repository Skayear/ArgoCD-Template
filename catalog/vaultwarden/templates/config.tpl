{{- if .Values.configmap.enabled }}
{{- range .Values.configmap.configs }}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .name }}
  namespace: {{ $.Release.Namespace }}
data:
{{- range .data }}
  {{ .name }}: {{ .value | quote }}
{{- end }}
{{- end }}
{{- end }}