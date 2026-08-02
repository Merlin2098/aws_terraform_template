# SPEC-FW-002 — SaaS Capability Extension

## Objetivo

Incorporar al framework actual todas las capacidades necesarias para desarrollar aplicaciones SaaS modernas utilizando React, FastAPI y Supabase.

---

## Contexto

El framework actual está optimizado para:

- Data Engineering
- ETL
- AWS
- Terraform
- Automatización

No contempla formalmente:

- Frontend
- UX/UI
- Gestión de usuarios
- Autenticación
- SaaS Analytics
- Despliegues Web

---

## Alcance

Añadir capacidades SaaS sin modificar las capacidades existentes.

---

## Nuevo Dominio

```
domains/saas/
```

---

# Skill Group 1 — Frontend

## Objetivo

Desarrollar interfaces web modernas.

---

## Capacidades

```
ReactViteTailwindReact RouterAxiosFormsReusable ComponentsResponsive Design
```

---

## Policies

### Frontend Policy 001

```
Component First
```

---

### Frontend Policy 002

```
No Business Logic Inside UI Components
```

---

### Frontend Policy 003

```
API Driven UI
```

---

# Skill Group 2 — Backend

## Objetivo

Construir APIs SaaS escalables.

---

## Capacidades

```
FastAPISQLAlchemyAlembicPydanticRepository PatternService Layer
```

---

## Policies

### Backend Policy 001

```
Controller → Service → Repository
```

---

### Backend Policy 002

```
Business Logic Only In Services
```

---

### Backend Policy 003

```
Database Access Only Through Repositories
```

---

# Skill Group 3 — Database

## Capacidades

```
PostgreSQLSupabaseIndexesConstraintsMigrationsPerformance
```

---

## Policies

### Database Policy 001

```
Soft Delete By Default
```

---

### Database Policy 002

```
Audit Fields Mandatory
```

---

### Database Policy 003

```
No Direct Production Changes
```

---

# Skill Group 4 — Authentication

## Capacidades

```
Supabase AuthJWTSession ManagementRBAC
```

---

## Roles Estándar

```
OWNERADMINSALESSPECIALIST
```

---

## Policies

### Auth Policy 001

```
Authentication Managed By Supabase
```

---

### Auth Policy 002

```
Authorization Managed By Application Layer
```

---

# Skill Group 5 — SaaS Analytics

## Capacidades

```
KPIsOperational DashboardsFiltersAggregationsBusiness Metrics
```

---

## Métricas Base

```
AppointmentsLeadsConversionCancellation RateOverbookingUtilization
```

---

## Policies

### Analytics Policy 001

```
Analytics Requirements Must Be Defined During Data Modeling
```

---

### Analytics Policy 002

```
Historical Tracking Required
```

---

# Skill Group 6 — Deployment

## Capacidades

```
RailwayVercelEnvironment VariablesGitHub ActionsCI/CD
```

---

## Policies

### Deploy Policy 001

```
No Secrets In Source Code
```

---

### Deploy Policy 002

```
Environment Specific Configuration
```

---

### Deploy Policy 003

```
Deploy Must Be Reproducible
```

---

# Skill Group 7 — UX/UI

## Capacidades

```
Dashboard DesignForm DesignUser FlowsNavigationAccessibility
```

---

## Policies

### UX Policy 001

```
Most Frequent Operations In Less Than 3 Clicks
```

---

### UX Policy 002

```
Minimize User Friction
```

---

# Future SaaS Capabilities

No implementar aún, pero preparar la estructura.

```
Multi-TenantSubscription BillingPaymentsNotificationsWhatsApp IntegrationCRM FeaturesCustomer Portal
```

---

## Criterios de Aceptación

- El framework incorpora un dominio SaaS independiente.
- Ninguna capacidad existente se rompe.
- Las policies SaaS son reutilizables en proyectos futuros.
- El framework puede soportar múltiples SaaS sin redefinir capacidades.