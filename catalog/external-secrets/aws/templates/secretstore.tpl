apiVersion: external-secrets.io/v1
kind: {{ .Values.aws.kind | quote }}
metadata:
  name: {{ .Values.aws.secretStoreName | quote }}
  {{- if eq .Values.aws.kind "SecretStore" }}
  namespace: {{ required "aws.namespace is required when aws.kind is SecretStore" .Values.aws.namespace | quote }}
  {{- end }}
spec:
  provider:
    aws:
      service: {{ .Values.aws.service | quote }}
      region: {{ required "aws.region is required" .Values.aws.region | quote }}
      auth:
        jwt:
          serviceAccountRef:
            name: {{ .Values.aws.serviceAccount.name | quote }}
            namespace: {{ .Values.aws.namespace | default "external-secrets" | quote }}