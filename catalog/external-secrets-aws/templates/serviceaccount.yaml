apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ .Values.aws.serviceAccount.name | quote }}
  namespace: {{ .Values.aws.namespace | default "external-secrets" | quote }}
  annotations:
    eks.amazonaws.com/role-arn: {{ required "aws.serviceAccount.roleArn is required" .Values.aws.serviceAccount.roleArn | quote }}
