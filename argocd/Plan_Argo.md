# Plan de acción — Argo CD en EKS

## Objetivo
Implementar un proceso seguro, reproducible y simple para instalar o actualizar Argo CD en un cluster EKS usando Helm desde GitHub Actions.

## Concepto clave
Instalar Argo CD por primera vez para que luego gestione todo.

## Estructura del repo
``` bash
<your-repo>/
├─ argocd/
│  ├─ values/
│  │  └─ custom_argo.yaml
└─ .github/workflows/deploy-argo.yaml
```

## Flujo
1. GitHub Actions se autentica en AWS (OIDC)
2. Conecta a EKS
3. Ejecuta Helm
4. Instala/actualiza Argo CD


---

## Problemas durante la instalación

Durante la implementación se intentó integrar Argo CD con una GitHub App (`<github-app-name>`), pero no fue posible completar la autenticación correctamente debido a problemas con la generación del token de instalación.

### Solución temporal

Se optó por utilizar un **Personal Access Token (PAT)** creado desde la cuenta personal de **Pablo Rodriguez** para poder avanzar con las pruebas y validación de la integración.

### Configuración del PAT

- El PAT fue configurado con acceso **únicamente al repositorio**:
  - `<your-org>/<your-repo>`
- No tiene acceso a otros repositorios ni a nivel organizacional (principio de mínimo privilegio)

### Permisos utilizados

Siguiendo la documentación oficial de GitHub:

https://docs.github.com/es/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens?apiVersion=2026-03-10#repository-permissions-for-contents

Se configuró el siguiente permiso:

- **Contents: Read-only**

Esto permite:
- Clonar el repositorio
- Leer manifests
- Permitir a Argo CD sincronizar aplicaciones

Sin permitir:
- Escritura
- Modificación de código
- Acciones administrativas


### Consideraciones futuras

- Revisar la correcta configuración de la **GitHub App (`<github-app-name>`)**
- Migrar desde PAT a GitHub App para:
  - Mejor seguridad
  - Tokens temporales
  - Mejor control de acceso
- Evitar dependencia de credenciales personales a largo plazo


# Modelo de permisos en Argo CD

## Descripción general

El acceso a Argo CD se basa en dos niveles:

- **Autenticación** → Microsoft Entra ID
- **Autorización** → RBAC de Argo CD

---

## Roles definidos

### Admin

- Acceso completo al sistema
- Uso restringido al equipo de plataforma

---

### Devs

- Acceso a todas las aplicaciones

Permiten:

- Ver aplicaciones
- Sincronizar (`sync`)
- Ver logs
- Ejecutar comandos (`exec`)

Restricción:

- ❌ No pueden acceder al proyecto `internal`

---

## Regla de seguridad

El proyecto `internal` contiene componentes críticos de plataforma y está restringido únicamente a administradores.

---

## Flujo de autorización

1. El usuario inicia sesión mediante Microsoft Entra ID
2. Argo CD recibe los grupos incluidos en el token OIDC
3. Se asigna un rol (`admin` o `devs`) según el grupo
4. El rol define los permisos efectivos dentro de Argo CD

---

## Principio aplicado

Se sigue el principio de:

> **Acceso amplio por defecto + exclusión explícita de infraestructura crítica**

## Diagrama
## Diagrama simple

```text
[ Usuario ]
    |
    v
[ Microsoft Entra ID ]
    |
    | Token OIDC con grupos
    v
[ Argo CD ]
    |
    | RBAC
    v
+----------------------------------------------+
| Roles efectivos                              |
|----------------------------------------------|
| admin -> acceso completo                     |
| devs  -> acceso a todos los proyectos        |
|          excepto `internal`                  |
+----------------------------------------------+
