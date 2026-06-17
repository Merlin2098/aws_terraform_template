# SPEC-018 - Shell Automation Skill Pack

## Objetivo

Incorporar un conjunto de skills especializados en generación, validación y mantenimiento de scripts Bash y PowerShell para entornos Windows, Linux y entornos híbridos.

Los skills deberán ser reutilizables por múltiples agentes y no depender de un dominio específico (AWS, Terraform, Kubernetes, etc.).

---

# Motivación

Actualmente los agentes poseen capacidades de generación de código generalista, pero carecen de conocimiento especializado para:

* Automatización de sistemas operativos.
* Administración Windows mediante PowerShell.
* Automatización Linux mediante Bash.
* Detección de entornos shell.
* Generación segura de scripts.
* Testing y validación de scripts.
* Documentación automática.

Esto provoca:

* Scripts no idempotentes.
* Uso de comandos incompatibles con el entorno.
* Ausencia de validaciones de seguridad.
* Baja reutilización entre agentes.

---

# Alcance

El presente spec define:

* Nuevos skills.
* Contratos esperados.
* Capacidades mínimas.
* Dependencias entre skills.
* Criterios de aceptación.

No define:

* Integración con proveedores LLM específicos.
* Implementación interna del framework.
* Tooling concreto de ejecución.

---

# Arquitectura Implementada

Los 20 skills conceptuales del spec original se consolidaron en 9 archivos
siguiendo Policy 008 (simplicidad). La estructura implementada es:

```text
ai/skills/shell/
├── environment_detection.md      (environment-detection)
├── powershell_core.md            (powershell-core)
├── powershell_filesystem.md      (powershell-filesystem)
├── powershell_windows_admin.md   (powershell-services + powershell-registry + powershell-scheduled-tasks)
├── powershell_json_yaml.md       (powershell-json-yaml)
├── bash_core.md                  (bash-core)
├── cli_automation.md             (bash-devops + git-cli + terraform-cli + docker-cli + aws-cli + azure-cli)
├── script_security.md            (script-security)
└── script_quality.md             (script-testing + script-documentation + script-refactoring)
```

Los skills de CLI (terraform-cli, aws-cli, etc.) se enfocan en la mecánica de scripting
seguro. El comportamiento de cada servicio vive en los dominios existentes `ai/skills/aws/`
y `ai/skills/terraform/`, que los nuevos skills referencian explícitamente.

---

# Skill: environment-detection

## Responsabilidad

Determinar el entorno objetivo antes de generar scripts.

## Capacidades

* Detectar Windows.
* Detectar Linux.
* Detectar macOS.
* Detectar WSL.
* Detectar Git Bash.
* Detectar PowerShell 5.1.
* Detectar PowerShell 7+.

## Resultado Esperado

```yaml
environment:
  os: windows
  shell: powershell
  shell_version: 7.5
  wsl_enabled: true
```

---

# Skill: powershell-core

## Responsabilidad

Generar scripts PowerShell idiomáticos.

## Capacidades

* Cmdlets estándar.
* Funciones.
* Módulos.
* Parámetros.
* Pipeline.
* Manejo de errores.
* Logging.

## Restricciones

Debe evitar:

```powershell
Write-Host "error"
exit 1
```

cuando exista una alternativa estructurada.

---

# Skill: powershell-filesystem

## Responsabilidad

Operaciones de archivos y directorios.

## Capacidades

* Copy-Item
* Move-Item
* Remove-Item
* Rename-Item
* Compress-Archive
* Expand-Archive

## Requisito

Toda operación destructiva deberá soportar:

```powershell
-WhatIf
```

---

# Skill: powershell-services

## Responsabilidad

Administración de servicios Windows.

## Capacidades

* Get-Service
* Start-Service
* Stop-Service
* Restart-Service

## Validaciones

Comprobar existencia previa del servicio.

---

# Skill: powershell-registry

## Responsabilidad

Administración segura del Registro de Windows.

## Capacidades

* Lectura.
* Escritura.
* Backup previo.
* Restauración.

## Restricción

Nunca modificar claves sin validación previa.

---

# Skill: powershell-scheduled-tasks

## Responsabilidad

Gestión de tareas programadas.

## Capacidades

* Crear.
* Actualizar.
* Eliminar.
* Consultar.

---

# Skill: powershell-json-yaml

## Responsabilidad

Manipulación de estructuras de configuración.

## Capacidades

* ConvertFrom-Json
* ConvertTo-Json
* YAML parsing
* YAML serialization

## Casos

* Terraform
* Kubernetes
* CI/CD

---

# Skill: bash-core

## Responsabilidad

Generación de scripts Bash portables.

## Capacidades

* Variables.
* Loops.
* Functions.
* Pipes.
* Exit codes.

## Restricciones

Generar scripts compatibles con:

* Linux
* WSL
* Git Bash

cuando sea posible.

---

# Skill: bash-devops

## Responsabilidad

Automatización DevOps mediante Bash.

## Capacidades

* Docker.
* Git.
* Terraform.
* Kubernetes.
* CI/CD.

---

# Skill: git-cli

## Responsabilidad

Operaciones Git comunes.

## Capacidades

* clone
* fetch
* pull
* checkout
* merge
* rebase
* tag

## Restricciones

Evitar comandos destructivos sin confirmación.

---

# Skill: terraform-cli

## Responsabilidad

Automatización Terraform.

## Capacidades

* init
* validate
* fmt
* plan
* apply
* destroy

## Validaciones

Promover:

```bash
terraform validate
terraform plan
```

antes de apply.

---

# Skill: docker-cli

## Responsabilidad

Automatización Docker.

## Capacidades

* build
* run
* stop
* rm
* logs
* exec

---

# Skill: aws-cli

## Responsabilidad

Automatización AWS mediante CLI.

## Capacidades

* Lambda
* S3
* CloudFormation
* ECS
* IAM
* ECR

## Restricciones

No exponer secretos.

---

# Skill: azure-cli

## Responsabilidad

Automatización Azure mediante CLI.

## Capacidades

* Resource Groups
* Storage
* Functions
* AKS

---

# Skill: script-security

## Responsabilidad

Evaluar riesgos antes de generar scripts.

## Capacidades

Detectar:

```bash
rm -rf
```

```powershell
Remove-Item -Recurse -Force
```

```bash
terraform destroy
```

## Comportamiento

Requerir confirmación explícita.

---

# Skill: script-testing

## Responsabilidad

Validar scripts generados.

## Capacidades

### Bash

* ShellCheck

### PowerShell

* PSScriptAnalyzer
* Pester

## Resultado

Generar reporte de hallazgos.

---

# Skill: script-documentation

## Responsabilidad

Documentar scripts automáticamente.

## Capacidades

### PowerShell

Generar:

```powershell
.SYNOPSIS
.DESCRIPTION
.PARAMETER
.EXAMPLE
```

### Bash

Generar encabezados descriptivos.

---

# Skill: script-refactoring

## Responsabilidad

Mejorar scripts existentes.

## Capacidades

* Detectar duplicación.
* Mejorar legibilidad.
* Simplificar lógica.
* Introducir funciones reutilizables.
* Aplicar buenas prácticas.

---

# Dependencias

| Skill                      | Depends On                 |
| -------------------------- | -------------------------- |
| powershell-filesystem      | powershell-core            |
| powershell-services        | powershell-core            |
| powershell-registry        | powershell-core            |
| powershell-scheduled-tasks | powershell-core            |
| bash-devops                | bash-core                  |
| terraform-cli              | bash-core                  |
| docker-cli                 | bash-core                  |
| aws-cli                    | bash-core                  |
| azure-cli                  | bash-core                  |
| script-testing             | bash-core, powershell-core |
| script-documentation       | bash-core, powershell-core |

---

# Acceptance Criteria

## AC-1

El agente identifica correctamente el entorno antes de generar scripts.

## AC-2

Todo script generado incluye manejo de errores.

## AC-3

Toda operación destructiva requiere confirmación.

## AC-4

Los scripts PowerShell soportan WhatIf cuando aplique.

## AC-5

Los scripts Bash pasan ShellCheck sin errores críticos.

## AC-6

Los scripts PowerShell pasan PSScriptAnalyzer sin errores críticos.

## AC-7

Todo script generado incluye documentación mínima.

## AC-8

Los skills pueden ser consumidos independientemente por agentes host.
