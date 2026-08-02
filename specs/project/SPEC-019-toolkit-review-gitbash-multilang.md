# SPEC-019 - Revisión de dominio shell, empaquetado cloud y multi-lenguaje en `.ai`

## Objetivo

Documentar y proponer los cambios a evaluar sobre seis ejes del framework
`richi_toolkit`: MCP de usuario disponibles para enriquecer `ai/`, migración
del dominio `shell` a `gitbash` (con `shell` como fallback), impacto de esa
migración en la distinción Windows/Linux, separación de gestión de paquetes
entre desarrollo (`uv`) y despliegue cloud (Lambda/Glue), simplificación de la
lógica de dominios, y ampliación de los hooks de generación de `.ai` más allá
de Python.

Este documento es un análisis y propuesta — no ejecuta ningún cambio por sí
mismo. Cada sección deja una recomendación y, cuando aplica, un checklist de
implementación para un spec de seguimiento.

---

# Motivación

El propietario del repositorio usa `richi_toolkit` como framework personal de
guidance para agentes de IA ("este repositorio se ha convertido en la
extensión de mi mente"). El repo evolucionó con supuestos que ya no reflejan
del todo el entorno real de trabajo:

* El shell de trabajo real es Git Bash sobre Windows, no PowerShell nativo ni
  Bash puro de Linux.
* El framework se distribuye a proyectos que despliegan a AWS Lambda/Glue,
  donde `uv` no es la herramienta relevante en tiempo de empaquetado.
* La lógica de dominios (`ai/domains/`, `ai/capabilities/`,
  `.template-profile.yaml`) tiene una capa de indirección notable para el
  tamaño actual del framework.
* Los hooks que generan `.ai/` (`ai/hooks/`, `scripts/hooks/ai_refresh.py`) y
  todo el toolchain de calidad (`Makefile`, `scripts/testing/`) están escritos
  y pensados exclusivamente en Python, aunque el perfil de capacidades ya
  contempla `frameworks.react` y el repo puede alojar frontend/Terraform.

---

# Alcance

Este spec cubre análisis y recomendaciones para:

1. Inventario de MCP a nivel usuario y su uso para enriquecer `ai/`.
2. Migración del dominio `shell` → `gitbash` con `shell` como fallback.
3. Impacto de esa migración en la distinción Windows/Linux del framework.
4. Separación `uv` (desarrollo) vs. `pip` empaquetado dedicado (Lambda/Glue).
5. Evaluación de simplificar la lógica de dominios/capacidades.
6. Ampliación de hooks de generación de `.ai` a Rust, Go y React/JS.

No cubre la implementación de ninguno de los cambios — eso queda para specs
de seguimiento por eje, referenciados en cada sección.

---

## 1. MCP de usuario disponibles para `ai/`

### Estado actual

El usuario tiene configurados a nivel global (`~/.claude.json` →
`mcpServers`) cuatro servidores MCP:

| Servidor | Transporte | Propósito relevante para `ai/` |
|---|---|---|
| `aws-documentation-mcp-server` | stdio (`uvx`) | Búsqueda y lectura de docs oficiales de AWS — puede validar/actualizar `ai/skills/aws/*.md` contra la documentación vigente en lugar de mantenerlas solo por memoria del agente. |
| `terraform` | stdio (`docker run hashicorp/terraform-mcp-server`) | Consulta de providers/módulos de registry de Terraform — relevante para `ai/skills/terraform/*.md` y `ai/domains/terraform.md`. |
| `markitdown` | stdio (`uvx`) | Conversión de documentos a Markdown — útil para ingerir specs/ADRs externos hacia `specs/project/`. |
| `obsidian` | stdio (`uvx`, API key local) | Lectura/escritura sobre un vault Obsidian local — posible fuente/destino de notas de diseño fuera del repo. |

### Observación

Ninguno de estos MCP está referenciado hoy desde `AGENTS.md`,
`ai/context.yaml` ni `ai/policies/global.md`. Son capacidades disponibles al
agente en runtime, pero invisibles como *fuente de conocimiento* documentada
del framework — un agente frío no sabe que existen salvo por config de
usuario, que no viaja con el repo (es user-level, no project-level).

### Recomendación

* No declarar los MCP como dependencia dura del framework (son config de
  usuario, no del repo — otro host del template puede no tenerlos).
* Añadir una nota breve en `AGENTS.md` bajo "Knowledge Sources": si los MCP
  `aws-documentation-mcp-server` y `terraform` están disponibles en la sesión,
  preferir su consulta para verificar vigencia de contenido en
  `ai/skills/aws/` y `ai/skills/terraform/` antes de asumir que el Markdown
  local está actualizado — sin bloquear el flujo si no están presentes.
* No incorporar `markitdown` ni `obsidian` a la guidance del framework: son
  herramientas de flujo personal del usuario (ingesta de notas), no parte del
  contrato de proyecto. Quedan fuera de alcance de `ai/`.
* No hace falta un quinto MCP dedicado a "AI docs" — el patrón ya existente
  (`ai/skills/*.md` versionado en git) sigue siendo preferible a una fuente
  externa para contenido que debe ser reproducible sin conexión a MCP.

---

## 2. Dominio `shell` → `gitbash` (con `shell` como fallback)

### Estado actual

`ai/domains/shell.md` cubre Bash **y** PowerShell como un único dominio
"Shell / Scripting", con detección de entorno (`ai/skills/shell/
environment_detection.md`) que ya reconoce Git Bash vía `$MSYSTEM` como una
señal más, no como el entorno primario. El `skills.yaml` y `domains.yaml`
(`ai/capabilities/platform/domains.yaml`, que en realidad es sobre dominios
DNS/SaaS, no confundir con el dominio de skills "shell") no tienen concepto de
prioridad entre shells.

### Problema

El entorno real de trabajo del usuario es Git Bash sobre Windows. Hoy el
framework trata Bash/PowerShell/Git Bash como variantes simétricas
detectadas en runtime, cuando en la práctica Git Bash es el shell primario y
PowerShell/cmd son casos secundarios (WhatIf, registro, tareas programadas
nativas de Windows que Git Bash no puede cubrir).

### Recomendación

* Renombrar el dominio primario de `shell` a `gitbash` conceptualmente (no
  necesariamente el archivo — ver nota de compatibilidad abajo), reordenando
  `ai/skills/shell/environment_detection.md` para que Git Bash sea el
  entorno *default asumido* en vez de una señal más entre varias.
* Mantener `shell` (Bash POSIX puro / PowerShell) como fallback explícito
  para: (a) scripts que deban correr en CI Linux sin Git Bash, (b) tareas que
  requieran cmdlets Windows-only (registro, servicios, tareas programadas) no
  disponibles desde Git Bash.
* Opciones de implementación a decidir en el spec de seguimiento:
  - **(a)** Renombrar `ai/domains/shell.md` → `ai/domains/gitbash.md` y
    `ai/skills/shell/` → `ai/skills/gitbash/`, dejando redirecciones/alias en
    `ai/skills.yaml` para no romper referencias existentes.
  - **(b)** Conservar los nombres de archivo actuales y solo reordenar
    contenido/precedencia dentro de `environment_detection.md` y
    `shell.md`, evitando el costo de renombrar rutas referenciadas desde
    `ai/skills.yaml`, `ai/domains/index.md` y `AGENTS.md`.
  - Recomendación: **(b)** primero (bajo costo, sin romper referencias);
    evaluar **(a)** solo si el framework crece lo suficiente como para
    justificar el rename.
* Ajustar `AGENTS.md` §"Execution Rules" ("on Windows, follow the documented
  wrapper flow under `docs/windows_setup/`") para aclarar que ese flujo
  asume Git Bash, no PowerShell, como shell de ejecución por defecto en
  Windows.

---

## 3. Impacto en la distinción Windows/Linux

### Estado actual

La distinción Windows/Linux vive en dos lugares concretos:

* `Makefile` (raíz): rama por `$(OS)` = `Windows_NT` vs. resto, seleccionando
  `PYTHON`, `UV` y `BOOTSTRAP_PYTHON` (`py -3` en Windows vs. `python3` en
  Linux/macOS). Esta rama usa `nmake`/`make` semantics de variables de
  entorno del SO, **no** del shell — sigue siendo válida en Git Bash sobre
  Windows porque `$(OS)` es una variable de entorno de Windows, no del shell.
* `ai/installer.py`: excluye explícitamente `install_linux.py` e
  `install_windows.py` como entry points separados por plataforma.

### Problema

Si el shell primario pasa a ser Git Bash, la distinción sigue siendo
necesaria a nivel de **sistema operativo** (rutas, `py -3` vs `python3`,
entry points de instalación), pero deja de ser necesaria a nivel de
**sintaxis de script** para la mayoría de los casos: Git Bash acepta
sintaxis POSIX Bash, así que gran parte de lo que hoy podría justificar un
`.ps1` puede resolverse con un único script Bash portable, reduciendo la
necesidad de mantener pares `.ps1`/`.sh` por tarea.

### Recomendación

* **No eliminar** la distinción Windows/Linux — sigue siendo real a nivel de
  intérprete Python (`py -3` vs `python3`), rutas (`\` vs `/`, aunque Git
  Bash normaliza la mayoría), e instaladores (`install_windows.py` /
  `install_linux.py`).
* **Sí reducir** la superficie de scripts que se generan en variante dual
  PowerShell+Bash: con Git Bash como shell primario en Windows, la política
  de `environment_detection.md` ("When both Bash and PowerShell are
  plausible, generate both variants") debería pasar a "generar Bash por
  defecto; generar PowerShell solo cuando la tarea requiera una capacidad
  Windows-only (registro, servicios, tareas programadas, WhatIf nativo)".
* Actualizar `ai/skills/shell/bash_core.md` para documentar explícitamente
  que Git Bash sobre Windows es un target de primera clase (no solo "también
  funciona"), incluyendo notas sobre limitaciones conocidas (rutas
  `/c/Users/...` vs `C:\Users\...`, ausencia de systemd, permisos POSIX
  simulados).

---

## 4. `uv` (desarrollo) vs. empaquetado dedicado para Lambda/Glue

### Estado actual

`pyproject.toml` usa `uv` con extras `local`, `cloud`, `saas`, `supabase` y
grupos de dependencias `dev-local`/`dev-cloud`. No hay separación entre
"dependencias para desarrollar/testear" y "dependencias que deben terminar
empaquetadas dentro de un `.zip` de Lambda o un job de Glue". `ai/skills/aws/
lambda_packaging.md` ya existe como skill dedicado — es el lugar natural para
esta política, pero no está claro (sin leerlo) si ya resuelve el problema o
solo documenta el empaquetado en general.

### Problema

`uv` es excelente para resolver y fijar (`uv.lock`) el entorno de desarrollo,
pero el artefacto final desplegado a Lambda/Glue no puede depender de `uv`
en runtime — necesita un `pip install --target` (o layer/wheel prebuild)
con solo las dependencias de producción de esa función específica, sin los
extras `local`/`dev-*` ni paquetes pesados no usados por esa Lambda concreta
(p. ej. `pyside6`, `duckdb`, `polars` del extra `local` no deberían viajar en
un paquete de Lambda que solo usa `boto3`+`awswrangler`).

### Recomendación

* Mantener `uv` como gestor único de desarrollo/lockfile — no introducir un
  segundo gestor de dependencias para desarrollo.
* Para el paso de empaquetado cloud, usar `uv export` (o `uv pip compile`)
  para generar un `requirements.txt` acotado al extra `cloud` (y, si aplica,
  por-función) y alimentar ese `requirements.txt` a `pip install --target
  <build_dir> --no-deps` o `uv pip install --target` dentro del script de
  empaquetado — evitando que `uv` mismo sea una dependencia runtime del
  paquete Lambda/Glue.
* Revisar `ai/skills/aws/lambda_packaging.md` y `scripts/package.py` para
  confirmar si ya implementan este patrón; si no, es el punto de extensión
  correcto (no crear un skill nuevo).
* Evaluar empaquetado por función (un `requirements.txt` mínimo por
  Lambda/Glue job, derivado de qué imports usa cada entry point en
  `src/jobs/`) frente a un único paquete con todo `cloud` — el primero reduce
  tamaño de despliegue y cold start; el segundo es más simple de mantener.
  Recomendación: empezar con un único extra `cloud` compilado a
  `requirements.txt` (más simple), y solo fragmentar por función si el
  tamaño del paquete se vuelve un problema real (Policy 008 — simplicidad).

---

## 5. Simplificación de la lógica de dominios

### Estado actual

El framework tiene tres capas relacionadas pero distintas:

1. `ai/capabilities/<category>/<name>.yaml` — registro de capacidades
   (`aws`, `terraform`, `react`, `python`, `saas`, `supabase`, `vps`,
   `domains`) con `depends_on` y `paths`.
2. `.template-profile.yaml` — perfil generado por capacidad habilitada/
   deshabilitada por proyecto host.
3. `ai/domains/*.md` + `ai/domains/index.md` — agrupación semántica de
   skills por dominio de trabajo, navegable por humano y agente.
4. `ai/skills.yaml` — índice canónico de slugs de skills.

Hay overlap conceptual entre "capability" (activable/desactivable, gate de
instalación) y "domain" (agrupación de guidance, siempre presente en el
repo una vez instalado). Por ejemplo, `platform.domains` en
`ai/capabilities/platform/domains.yaml` es sobre dominios *DNS/SaaS*
(`ai/skills/saas/domains.md`), mientras que "domain" en `ai/domains/` es
sobre dominios *de skill del agente* (shell, python, aws...) — mismo término,
dos significados distintos, lo cual es una fuente real de confusión al leer
el repo en frío.

### Problema

Para el tamaño actual del framework (un usuario, un repo plantilla, ~9
capacidades, ~9 dominios de skill), cuatro capas de indirección
(capability → profile → domain → skill index) es más maquinaria de la que el
volumen de contenido justifica. El costo no es solo de líneas de código sino
cognitivo: un agente (o el propio usuario) debe cruzar 3-4 archivos para
entender "¿este skill está activo en este proyecto y por qué".

### Recomendación

* **No colapsar** capability vs. domain-de-skill en una sola capa: cumplen
  roles distintos y necesarios — capability es un *gate de instalación*
  (¿este proyecto host necesita AWS?), domain es *navegación de contenido*
  (¿qué skills hay para AWS?). Fusionarlos acoplaría "¿está instalado?" con
  "¿cómo se organiza el contenido?", lo que dificultaría, por ejemplo, tener
  un dominio de skill documentado pero deshabilitado por defecto.
* **Sí resolver la colisión de nombres**: renombrar el concepto
  `platform.domains` (DNS/dominios de negocio, en
  `ai/capabilities/platform/domains.yaml` → `ai/skills/saas/domains.md`) a
  algo inequívoco como `platform.dns` o `business.dns`, dejando "domain"
  reservado exclusivamente para `ai/domains/` (agrupación de skills). Esto es
  una mejora de bajo riesgo y alto valor de claridad.
  - Nota: `saas.enabled` ya depende de `domains` según
    `ai/capabilities/platform/domains.yaml` (`depends_on: business: [saas]` —
    revisar si esa dependencia está invertida respecto a lo esperado antes
    de renombrar, para no arrastrar el bug al nuevo nombre).
* Evaluar si `ai/skills.yaml` (índice de slugs) y `ai/domains/index.md`
  (agrupación semántica) pueden fusionarse en un único archivo generado —
  hoy `ai/domains/index.md` es mantenido a mano y linkea a
  `ai/skills.yaml` como fuente canónica; si ambos listan esencialmente las
  mismas rutas, generar `index.md` a partir de `skills.yaml` (con un dominio
  como campo del slug) eliminaría un punto de mantenimiento duplicado.
  Marcar como candidato de simplificación, no ejecutar sin confirmar que
  `skills.yaml` ya tiene (o puede tener) el campo de dominio necesario.
* Mantener `.template-profile.yaml` tal cual — es el mecanismo correcto para
  que un host declare qué capacidades tiene activas, y ya es la pieza más
  simple de las cuatro.

---

## 6. Hooks de generación `.ai/` limitados a Python

### Estado actual

* `ai/context.yaml` → `structure:` solo declara `python`, `sql`, `config`,
  `contracts`, `infrastructure` como categorías de código fuente; no hay
  categoría para Rust, Go, ni JS/TS/React a pesar de que
  `ai/capabilities/frameworks/react.yaml` y `ai/skills/frontend/*.md` ya
  existen como dominio de skill.
* `ai/hooks/treemap.py` y (por convención en `Makefile`/`scripts/hooks/
  ai_refresh.py`) toda la cadena de generación de `.ai/context_bundle.yaml`,
  `.ai/skills_registry.json`, `.ai/dependencies_graph.json`,
  `.ai/treemap.md` está implementada en Python puro, y el treemap en sí es
  agnóstico de lenguaje (recorre el árbol de archivos sin importar
  extensión) — el sesgo a Python está en `ai/context.yaml` (`structure:`)
  y presumiblemente en `ai/runtime/dependency_graph.py`, no en el hook de
  treemap en sí.
* El propio `pyproject.toml` ya tiene extra `saas` con `fastapi` +
  frontend implícito, y el dominio `frontend.md` ya cubre React — es decir,
  el framework ya *asume* proyectos con frontend, pero `.ai/` no los modela
  como primera clase.

### Problema

Un proyecto host que combine Python (backend/Glue) con React (frontend) o,
a futuro, con servicios en Rust/Go, obtiene un `.ai/context_bundle.yaml` y
`dependencies_graph.json` que solo entienden el grafo de dependencias
Python — el resto del código queda invisible para esas dos artefactos
generados, aunque sí aparece en el treemap (agnóstico) y puede tener skills
documentados en `ai/skills/frontend/`.

### Recomendación

* Extender `ai/context.yaml` → `structure:` con categorías adicionales,
  activables por capacidad (siguiendo el patrón ya usado por `frameworks:
  react`):
  ```yaml
  structure:
    python:
      - src/
      - scripts/
    javascript:      # nuevo — gated por capabilities.frameworks.react (o futuro capability "node")
      - frontend/
      - src/frontend/
    rust:             # nuevo — requiere nueva capability languages.rust
      - src-rust/
    go:               # nuevo — requiere nueva capability languages.go
      - cmd/
      - internal/
  ```
* Revisar `ai/runtime/dependency_graph.py` (no leído en detalle en este
  spec) para confirmar si el grafo de dependencias es Python-específico
  (parseo de imports `import`/`from`) — si lo es, el hook de dependencias
  necesita un parser por lenguaje (o degradar con gracia: listar archivos
  sin grafo de imports para lenguajes no soportados, en vez de omitirlos).
* No es necesario un parser de imports completo para Rust/Go/JS en la
  primera iteración — mínimo viable: que `context_bundle.yaml` liste los
  archivos de esas categorías (igual que ya hace con `sql`/`config`), aunque
  `dependencies_graph.json` siga siendo Python-only hasta que se justifique
  el esfuerzo de un parser real.
* Priorización sugerida: React/JS primero (ya hay capability y skills
  activos: `frameworks.react`, `ai/skills/frontend/*.md`), Rust y Go después
  y solo si el usuario efectivamente empieza a alojar proyectos en esos
  lenguajes — no adelantarse sin caso de uso concreto (Policy 008).

---

# Dependencias entre ejes

| Eje | Depende de |
|---|---|
| 2. `shell` → `gitbash` | 1 (ninguna) |
| 3. Windows/Linux | 2 |
| 4. `uv` vs. pip cloud | ninguna (independiente) |
| 5. Simplificación de dominios | ninguna (independiente) |
| 6. Hooks multi-lenguaje en `.ai` | 5 (si se fusionan `skills.yaml`/`index.md`, el campo de dominio debe existir primero) |

---

# Fuera de alcance

* Ejecutar los renames/refactors propuestos — este documento es de análisis.
* Elegir el parser de imports concreto para Rust/Go (`syn`, `go/ast`, etc.)
  — depende de si el eje 6 se prioriza.
* Cambios a `ai/skills/aws/lambda_packaging.md` y `scripts/package.py` — se
  referencian pero no se leyeron línea a línea en este spec; su revisión
  detallada queda para el spec de seguimiento del eje 4.

---

# Próximos pasos

1. Confirmar con el usuario cuál(es) de los 6 ejes se implementan primero.
2. Por cada eje aprobado, abrir un spec de seguimiento numerado (SPEC-020+)
   con Contract/Invariants/Acceptance Criteria siguiendo el formato de
   `specs/template/000-template-spec-format.md`.
3. Los cambios a `AGENTS.md`, `ai/context.yaml` y `ai/capabilities/` son
   framework-owned (`managed` en `ai/installer.py`) — deben aplicarse en el
   repo plantilla, no parcheados ad-hoc en un host.
