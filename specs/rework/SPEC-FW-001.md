# SPEC-FW-001 — Domain-Based Framework Refactoring

## Objetivo

Refactorizar el framework actual de desarrollo asistido por IA para separar capacidades por dominios de conocimiento, facilitando la reutilización, escalabilidad y mantenimiento de skills, policies y templates.

---

## Contexto

El framework actual ha evolucionado principalmente alrededor de proyectos:

- Data Engineering
- ETL
- AWS
- Terraform
- Automatización

Con la incorporación de Kadishas aparecen nuevas capacidades relacionadas con:

- SaaS
- Frontend
- UX/UI
- PostgreSQL
- Autenticación
- Analytics operacionales

Actualmente dichas capacidades no se encuentran organizadas por dominio.

---

## Problema

El crecimiento continuo del framework puede provocar:

- Duplicidad de políticas.
- Skills difíciles de localizar.
- Prompts demasiado extensos.
- Mezcla de capacidades de distintos dominios.
- Menor reutilización.

---

## Objetivos

### O1

Separar capacidades por dominio.

### O2

Reducir acoplamiento entre dominios.

### O3

Permitir añadir nuevos dominios sin modificar dominios existentes.

### O4

Mantener un núcleo común reutilizable.

---

## Arquitectura Objetivo

```
framework/├── core/│├── domains/│├── templates/│├── policies/│└── workflows/
```

---

## Core

Contendrá elementos transversales.

```
core/├── adr/├── specs/├── testing/├── documentation/├── planning/└── quality_gates/
```

---

## Dominio Data Product

```
domains/data-product/├── ingestion.md├── transformation.md├── serving.md├── analytics.md└── storage.md
```

---

## Dominio AWS

```
domains/aws/├── lambda.md├── s3.md├── sqs.md├── stepfunctions.md├── bedrock.md└── security.md
```

---

## Dominio Terraform

```
domains/terraform/├── modules.md├── remote_backend.md├── state_management.md├── cicd.md└── best_practices.md
```

---

## Dominio Automation

```
domains/automation/├── desktop.md├── excel.md├── email.md├── batch_processing.md└── packaging.md
```

---

## Políticas Globales

Aplicables a todos los dominios.

---

### Policy 001

```
No Code Before Spec
```

---

### Policy 002

```
ADR Before Architecture Change
```

---

### Policy 003

```
Configuration Over Hardcoding
```

---

### Policy 004

```
Security By Default
```

---

## Workflow Objetivo

```
Idea↓ADR↓Spec↓Design↓Implementation↓Testing↓Documentation
```

---

## Entregables Esperados

### E1

Mapa actual de capacidades.

### E2

Clasificación por dominio.

### E3

Migración de skills existentes.

### E4

Documentación actualizada.

---

## Criterios de Aceptación

- Ningún skill pertenece a más de un dominio.
- Toda policy global reside en Core.
- Todo dominio es independiente.
- Nuevos dominios pueden añadirse sin modificar dominios existentes.