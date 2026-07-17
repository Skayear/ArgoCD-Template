{{- with .Values.aws.externalSecrets }}
{{- range . }}
{{- $externalSecret := . }}
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: {{ required "aws.externalSecrets[].name is required" $externalSecret.name | quote }}
  namespace: {{ $.Values.aws.namespace | default $.Release.Namespace | quote }}
spec:
  refreshInterval: {{ $externalSecret.refreshInterval | default "1h" | quote }}

  secretStoreRef:
    name: {{ required "aws.secretStoreName is required" $.Values.aws.secretStoreName | quote }}
    kind: {{ $.Values.aws.kind | default "SecretStore" | quote }}

  target:
    name: {{ $externalSecret.targetName | default $externalSecret.name | quote }}
    creationPolicy: {{ $externalSecret.creationPolicy | default "Owner" | quote }}

  data:
    {{- range $externalSecret.entries }}
    - secretKey: {{ required "aws.externalSecrets[].entries[].key is required" .key | quote }}
      remoteRef:
        key: {{ required "aws.externalSecrets[].remoteRef is required" $externalSecret.remoteRef | quote }}
        property: {{ required "aws.externalSecrets[].entries[].property is required" .property | quote }}
    {{- end }}
{{- end }}
{{- end }}