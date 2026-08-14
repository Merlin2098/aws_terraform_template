# SPEC-019 - Revisión de dominio shell, empaquetado cloud y multi-lenguaje en `.ai`

## Objetivo

Documentar y proponer los cambios a evaluar sobre seis ejes del framework
`richi_toolkit`: MCP de usuario disponibles para enriquecer `ai/`, migración
del dominio `shell` a `gitbash` (con `shell` como fallback), impacto de esa
migración en la distinción Windows/Linux, separación de gestión de paquetes
entre desarrollo (`uv`) y despliegue cloud (Lambda/Glue), simplificación de la
lógica de dominios, y ampliación de los hooks de generación de `.ai` más allá
de Python.

Este documento nació como análisis y propuesta. Los 6 ejes fueron revisados
con el usuario y **implementados directamente en este spec** (sin abrir
specs de seguimiento numerados — ver el bloque de decisión al inicio de
cada sección). Varios ejes (4, 5, 6) se cerraron parcial o totalmente sin
escribir código nuevo, cuando el análisis reveló que el framework ya
resolvía el problema o que escribir código habría sido trabajo sin demanda
real (Policy 008/YAGNI) — ver "Próximos pasos" para lo diferido
intencionalmente.

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

Este spec cubre análisis, recomendaciones, y — para los ejes ya resueltos —
la implementación en sí:

1. Inventario de MCP a nivel usuario y su uso para enriquecer `ai/`. — ✅ Implementado
2. Migración del dominio `shell` → `gitbash` con `shell` como fallback. — ✅ Implementado
3. Impacto de esa migración en la distinción Windows/Linux del framework. — ✅ Implementado
4. Separación `uv` (desarrollo) vs. `pip` empaquetado dedicado (Lambda/Glue). — ✅ Cerrado (ya resuelto por ADR 0002, sin código nuevo)
5. Evaluación de simplificar la lógica de dominios/capacidades. — ✅ Implementado (parcial — rename `domains`→`dns`; no-fusión decidida)
6. Ampliación de hooks de generación de `.ai` a Rust, Go y React/JS. — ✅ Implementado (React/JS); Rust/Go diferido sin código

Los 6 ejes quedaron resueltos — ver "Próximos pasos" para lo explícitamente
diferido (Rust/Go, materialización Lambda ZIP).

---

## 1. MCP de usuario disponibles para `ai/` — ✅ Implementado

> **Decisión (2026-08-01):** Policy 011 en `ai/policies/global.md` (Advisory),
> referenciada desde `AGENTS.md` §Governance. Verificación solo bajo demanda
> (no proactiva en cada tarea AWS/Terraform) — ver detalle abajo.

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

## 2. Dominio `shell` → `gitbash` (con `shell` como fallback) — ✅ Implementado

> **Decisión (2026-08-01):** Opción (b) — sin renombrar archivos/rutas.
> `docs/windows_setup/` reescrito con Git Bash como vía primaria y PowerShell
> como fallback explícito en cada bloque de comandos. Precedencia
> Git Bash > Linux/WSL/macOS Bash > PowerShell documentada en
> `ai/domains/shell.md` §Shell precedence. No se crea `scripts/linux/run_make.sh`
> — `make` ya está en PATH y se documenta invocación directa.
>
> Archivos modificados: `docs/windows_setup/README.md`, `make_install.md`,
> `make_cheatlist.md`, `uv_install.md`, `template_versioning.md`; `README.md`
> (raíz); `AGENTS.md` §Execution Rules; `ai/domains/shell.md`;
> `ai/domains/index.md`; `ai/skills.yaml`;
> `ai/skills/shell/environment_detection.md`; `ai/skills/shell/powershell_core.md`;
> `ai/skills/shell/cli_automation.md`.

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

## 3. Impacto en la distinción Windows/Linux — ✅ Implementado

> **Decisión (2026-08-01):** Se verificó en vivo (Git Bash / MINGW64) que
> `Makefile`, `run_uv_sync.py` y `sync_dependencies.py` ya funcionan
> correctamente sin cambios — `$(OS)` es variable de entorno de Windows (no
> de shell) y `sys.platform.startswith("win")` detecta el SO
> independientemente del shell que invoca Python. El único gap real era un
> mensaje de UX en el instalador desalineado con la precedencia Git-Bash-primero
> del eje 2. Alcance ampliado a pedido del usuario: se fusionaron
> `install_windows.py` + `install_linux.py` en un único `install.py`
> agnóstico de SO (eliminados los dos originales, sin wrappers de
> compatibilidad — ver detalle abajo).

### Estado actual (antes del cambio)

La distinción Windows/Linux vivía en tres lugares concretos:

* `Makefile` (raíz): rama por `$(OS)` = `Windows_NT` vs. resto, seleccionando
  `PYTHON`, `UV` y `BOOTSTRAP_PYTHON` (`py -3` en Windows vs. `python3` en
  Linux/macOS). Esta rama usa `nmake`/`make` semantics de variables de
  entorno del SO, **no** del shell — sigue siendo válida en Git Bash sobre
  Windows porque `$(OS)` es una variable de entorno de Windows, no del shell.
  **Sin cambios — ya correcta.**
* `scripts/run_uv_sync.py` y `scripts/hooks/sync_dependencies.py`:
  `sys.platform.startswith("win") and shutil.which("py")` para resolver el
  launcher `py -3`. **Sin cambios — ya correcto, funciona igual desde Git
  Bash, PowerShell o cmd.**
* `install_windows.py` / `install_linux.py`: dos entry points casi idénticos
  (diferían solo en selector de carpeta GUI/Tkinter vs. prompt CLI, y en el
  mensaje final de "next step"). **Fusionados en `install.py`.**

### Problema

Si el shell primario pasa a ser Git Bash, la distinción sigue siendo
necesaria a nivel de **sistema operativo** (rutas, `py -3` vs `python3`,
entry points de instalación), pero deja de ser necesaria a nivel de
**sintaxis de script** para la mayoría de los casos: Git Bash acepta
sintaxis POSIX Bash, así que gran parte de lo que hoy podría justificar un
`.ps1` puede resolverse con un único script Bash portable, reduciendo la
necesidad de mantener pares `.ps1`/`.sh` por tarea.

### Cambios aplicados

* `install.py` (nuevo, raíz del repo) reemplaza `install_windows.py` +
  `install_linux.py`. Prompt CLI por defecto para el target path en ambos
  casos; `--select-target` abre el picker GUI (Tkinter) cuando hay display
  disponible. El mensaje final "Next step" ahora muestra Git Bash primero
  con fallback PowerShell, coherente con el eje 2.
* `install_windows.py` e `install_linux.py` eliminados — sin wrappers de
  compatibilidad (decisión explícita del usuario: reemplazo completo, no
  shims).
* Referencias actualizadas: `ai/installer.py` (`EXCLUDED_EXACT_FILES`,
  mensaje de error de `update_template`), `tests/test_install_entrypoints.py`
  (renombrado a pruebas agnósticas de SO — 7/7 pasan), `README.md` (raíz,
  sección "Installation Model"), `docs/windows_setup/README.md`,
  `docs/windows_setup/template_versioning.md`, `docs/linux_setup/README.md`.
* Verificado con `pytest tests/ -k "install or installer"` — 50/50 tests
  pasan sin regresiones — y con un `install.py --dry-run` real end-to-end.
* Distinción Windows/Linux a nivel `Makefile` e intérprete Python: **no
  tocada**, confirmada correcta tal cual estaba.

---

## 4. `uv` (desarrollo) vs. empaquetado dedicado para Lambda/Glue — ✅ Cerrado (ya resuelto)

> **Decisión (2026-08-01):** No requiere implementación nueva. El framework
> ya tiene exactamente el patrón que este eje pedía evaluar, con más rigor
> del que el análisis original anticipaba: [`docs/adr/0002-lambda-packaging-strategy.md`](../../docs/adr/0002-lambda-packaging-strategy.md)
> (Accepted). `uv` sigue siendo el único gestor de desarrollo; el empaquetado
> cloud usa `uv export` para producir un `requirements.txt` de solo-runtime,
> sin que `uv` sea dependencia del artefacto desplegado. Se documenta un gap
> conocido (no se corrige — ver más abajo) porque no hay Lambda desplegada
> hoy y adelantar código sin demanda real violaría Policy 008 (el propio ADR
> 0002 lo señala explícitamente como riesgo a evitar).

### Estado actual — verificado, no supuesto

* `ai/runtime/project_profile.py:204` (`uv_export_args`) genera
  `uv export --no-dev --format requirements.txt --extra <extras-resueltos-por-capacidad>`
  — filtra automáticamente por las capacidades activas en
  `.template-profile.yaml`, así que un host con solo `languages:python`
  habilitado nunca arrastra `pyside6`/`duckdb`/`polars` (extra `local`) al
  paquete cloud.
* `scripts/package.py` ya usa ese export: arma
  `artifacts/data_platform_bundle.zip` con `src/` + el `requirements.txt`
  resuelto, **sin invocar `uv` en runtime del artefacto** — exactamente el
  patrón que este eje proponía adoptar.
* `ai/skills/aws/lambda_functions.md` ya tiene un árbol de decisión
  ejecutable (R1–R6: ZIP → ZIP+Layer → ECR) y `ai/skills/aws/
  lambda_packaging.md` documenta el modo ECR completo (Dockerfile,
  `docker_push.sh`, Terraform, pitfalls conocidos como `--provenance=false`).
* `docs/adr/0002-lambda-packaging-strategy.md` formaliza todo lo anterior
  como decisión arquitectónica (Policy 002), con measurable inputs
  (`S_unzip`, `has_syslib`, `native_ok`, `N_share`, `t_build`) en vez de
  reglas ad-hoc.

### Gap real identificado (documentado, sin corregir)

El propio ADR 0002 (§Context, punto 1) señala que `scripts/package.py`
produce un bundle **manifest-only** — `requirements.txt` sin las
dependencias materializadas dentro del ZIP. Eso es correcto para **Glue**
(que instala paquetes en runtime vía `--additional-python-modules`) pero
**inválido** para un Lambda ZIP real, que debe llevar las dependencias
materializadas dentro del propio archivo. El ADR ya documenta esto como
riesgo conocido y lo deja fuera de alcance intencionalmente: no existe
ninguna función Lambda desplegada en el repo hoy (`aws` capability
deshabilitada por defecto en `.template-profile.yaml`), así que
materializar `pip install --target` dentro de `package.py` ahora sería
código sin consumidor — exactamente lo que Policy 008 (YAGNI) desaconseja.

### Recomendación

* **No escribir código nuevo en este eje.** El patrón uv-dev / pip-cloud ya
  existe y es correcto para su único consumidor actual (Glue).
* Cuando la primera Lambda real necesite empaquetarse en ZIP (R5/R6 del
  árbol de decisión), extender `scripts/package.py` con un modo que
  materialice dependencias vía `pip install --target <build_dir> --no-deps`
  a partir del mismo `requirements.txt` ya resuelto por `uv export` — no
  crear un mecanismo paralelo. Ese es el trigger real mencionado en el ADR
  ("Implementation is sequenced separately... gated by real demand").
* Medir `S_unzip` (tamaño real del extra `cloud` sin comprimir) la primera
  vez que se evalúe empaquetar una Lambda — hoy es un valor no verificado,
  solo estimado por el ADR.

---

## 5. Simplificación de la lógica de dominios — ✅ Implementado (parcial)

> **Decisión (2026-08-01):** Renombrado `platform:domains` → `platform:dns`
> (archivo `ai/capabilities/platform/domains.yaml` → `dns.yaml`, `name: dns`).
> "domain"/"dominio" queda reservado exclusivamente para `ai/domains/`
> (agrupación de skills). La dependencia `dns → business:saas` se verificó
> en vivo: **no estaba invertida** (era una sospecha del análisis original,
> descartada) — es semánticamente correcta, solo el nombre anterior era
> confuso. No se fusionó `ai/skills.yaml` + `ai/domains/index.md` (decisión
> explícita: sin fricción real reportada, agregar un campo `domain:` a las
> 71 entradas de `skills.yaml` sería inversión sin problema que la
> justifique — Policy 008/YAGNI). Capability vs. domain-de-skill se
> mantienen como capas separadas, sin fusionar (ver razón original abajo).

### Verificación del rename

* `ai/capabilities/platform/dns.yaml` (renombrado vía `git mv`, `name: dns`).
* `.template-profile.yaml`: `platform.domains` → `platform.dns`.
* `ai/runtime/capability_registry.load_registry` carga `platform:dns`
  correctamente con su `depends_on: {business: [saas]}` intacto (verificado
  en vivo).
* Ningún test referenciaba `platform:domains` por nombre explícito (usan
  `business:saas` como capability de ejemplo) — suite completa
  (`pytest tests/ -k "install or capability or profile"`) **71/71 pasan**
  sin cambios.
* `.ai/skills_registry.json`, `.ai/context_bundle.yaml`,
  `.ai/dependencies_graph.json` regenerados vía `make ai-refresh` — sin
  referencias colgantes al nombre anterior.
* `ai/skills/saas/domains.md` (el skill file de DNS/Cloudflare/SPF-DKIM en
  sí) **no se renombró** — ese nombre es correcto tal cual, describe
  dominios DNS, no colisiona con `ai/domains/`.

### Estado actual (antes del cambio)

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

### Decisiones tomadas

* **No colapsar** capability vs. domain-de-skill en una sola capa: cumplen
  roles distintos y necesarios — capability es un *gate de instalación*
  (¿este proyecto host necesita AWS?), domain es *navegación de contenido*
  (¿qué skills hay para AWS?). Fusionarlos acoplaría "¿está instalado?" con
  "¿cómo se organiza el contenido?", lo que dificultaría, por ejemplo, tener
  un dominio de skill documentado pero deshabilitado por defecto.
* **Colisión de nombres resuelta**: `platform.domains` renombrado a
  `platform.dns` (ver bloque de decisión arriba). La sospecha de que
  `depends_on: business: [saas]` estuviera invertida se descartó tras
  verificar en vivo con `resolve_project_profile` — activar
  `platform:domains` (ahora `platform:dns`) arrastraba correctamente
  `business:saas` como dependencia implícita; el comportamiento era
  correcto, solo el nombre confuso.
* **No fusionar** `ai/skills.yaml` (índice de slugs) y `ai/domains/index.md`
  (agrupación semántica) en un único archivo generado — decisión explícita:
  agregar un campo `domain:` a las 71 entradas de `skills.yaml` y escribir
  un generador es una inversión de mantenimiento sin fricción real
  reportada hoy (Policy 008/YAGNI). Ambos archivos se mantienen
  independientes, tal como estaban.
* `.template-profile.yaml` sin cambios estructurales (más allá del rename
  de la clave `domains` → `dns`) — sigue siendo el mecanismo correcto para
  que un host declare qué capacidades tiene activas.

---

## 6. Hooks de generación `.ai/` limitados a Python — ✅ Implementado (React/JS); Rust/Go diferido

> **Decisión (2026-08-01):** El diagnóstico original sobreestimaba el gap.
> `ai/runtime/dependency_graph.py` **ya tenía** un scanner de JS/TS completo
> (`scan_javascript`) cableado vía `frameworks:react.yaml` →
> `scanners: [javascript]` — no era "presumiblemente Python-específico",
> ya soportaba JS/TS antes de esta sesión. El gap real, ahora cerrado, era
> más pequeño: `ai/tools/inspect_project.py:_detect_languages` no
> reconocía `.js/.jsx/.ts/.tsx`, y `ai/context.yaml → structure:` no tenía
> categoría `javascript`. Rust y Go quedan **explícitamente diferidos, sin
> código**: no hay capability, scanner, ni skill para ninguno de los dos, y
> no hay indicio de proyectos reales en esos lenguajes — crear el andamiaje
> ahora sería trabajo especulativo (Policy 008/YAGNI).

### Cambios aplicados (React/JS)

* `ai/tools/inspect_project.py:_detect_languages` — añadido
  `JAVASCRIPT_SUFFIXES = {".js", ".jsx", ".ts", ".tsx"}`; ahora reconoce
  `javascript` en `project.languages`, lo agrega como `primary_language`
  cuando no hay Python/SQL/Terraform, añade `"frontend"` a `project_types`,
  y expone `structure.has_javascript`.
* `ai/context.yaml → structure:` — añadida la categoría `javascript: [frontend/]`,
  siguiendo la convención de ruta ya usada por
  `ai/skills/frontend/react_vite_aws.md` (`frontend/.env.production`, etc.).
* Verificado funcionalmente: un proyecto sintético solo con `frontend/src/App.tsx`
  produce `primary_language: javascript`, `project_types: ["frontend"]`,
  `has_javascript: true`.
* Suite completa: **92/92 tests pasan** tras el cambio y tras regenerar
  `.ai/` vía `make ai-refresh`.
* **No tocado** (ya eran correctos): `ai/runtime/dependency_graph.py`
  (`scan_javascript` ya existente, con resolución de imports relativos y
  paquetes con scope `@org/pkg`); `ai/capabilities/frameworks/react.yaml`
  (`scanners: [javascript]` ya declarado).

### Rust y Go — diferido, sin código

No existe `ai/capabilities/languages/rust.yaml` ni `go.yaml`, ningún
scanner, ningún skill, y ningún indicio en el repo o en la conversación de
que haya (o vaya a haber pronto) un proyecto real en esos lenguajes. Crear
capability + scanner + skills ahora sería andamiaje sin consumidor —
exactamente el mismo patrón de "no adelantarse sin demanda real" aplicado
en el eje 4 (Lambda ZIP) y en la no-fusión del eje 5. Retomar cuando exista
un proyecto Rust o Go real que lo necesite.

### Estado previo (antes de esta sesión, para referencia)

* `ai/context.yaml` → `structure:` solo declaraba `python`, `sql`, `config`,
  `contracts`, `infrastructure` como categorías de código fuente; no había
  categoría para Rust, Go, ni JS/TS/React a pesar de que
  `ai/capabilities/frameworks/react.yaml` y `ai/skills/frontend/*.md` ya
  existían como dominio de skill.
* El propio `pyproject.toml` ya tiene extra `saas` con `fastapi` +
  frontend implícito, y el dominio `frontend.md` ya cubre React — es decir,
  el framework ya *asume* proyectos con frontend, pero `.ai/` no los
  modelaba como primera clase (ahora sí, para el campo `languages`/
  `structure`).

### Problema (resuelto para React/JS; vigente para Rust/Go)

Un proyecto host que combine Python (backend/Glue) con React (frontend)
obtenía un `.ai/context_bundle.yaml` que no reconocía `javascript` como
lenguaje ni `frontend` como tipo de proyecto — aunque
`dependencies_graph.json` **ya** grafeaba sus imports correctamente vía
`scan_javascript` (esa parte nunca estuvo rota). Cerrado arriba.

Para Rust/Go el problema sigue vigente sin cambios: un proyecto host en
esos lenguajes obtendría un `context_bundle.yaml`/`dependencies_graph.json`
que no los reconoce en absoluto — solo el treemap (agnóstico de lenguaje)
los mostraría. Diferido intencionalmente (ver arriba).

---

# Dependencias entre ejes

| Eje | Depende de |
|---|---|
| 2. `shell` → `gitbash` | 1 (ninguna) |
| 3. Windows/Linux | 2 |
| 4. `uv` vs. pip cloud | ninguna (independiente) |
| 5. Simplificación de dominios | ninguna (independiente) |
| 6. Hooks multi-lenguaje en `.ai` | ninguna (React/JS no requirió tocar 5) |

---

# Fuera de alcance

* Elegir el parser de imports concreto para Rust/Go (`syn`, `go/ast`, etc.)
  — diferido junto con todo el soporte Rust/Go (eje 6), sin demanda real hoy.
* Materializar dependencias (`pip install --target`) para un Lambda ZIP real
  en `scripts/package.py` — diferido explícitamente por el eje 4 y por ADR
  0002 hasta que exista una Lambda real que lo necesite (Policy 008).
* Crear `ai/capabilities/languages/rust.yaml` / `go.yaml` sin skills reales
  detrás — decisión explícita de no crear andamiaje especulativo (eje 6).

---

# Próximos pasos

Los 6 ejes están **completos**. Resumen de lo diferido intencionalmente
(sin código, documentado para retomar ante demanda real):

* **Eje 4** — materializar dependencias (`pip install --target`) para un
  Lambda ZIP real en `scripts/package.py`, cuando exista la primera Lambda
  que dispare R5/R6 del árbol de decisión de `lambda_functions.md`.
* **Eje 5** — la fusión `skills.yaml`/`index.md` se descartó explícitamente
  (sin fricción real que la justifique); revisar solo si el catálogo de
  skills crece lo suficiente como para que el mantenimiento duplicado
  duela de verdad.
* **Eje 6** — soporte Rust/Go (capability, scanner de imports, skills) en
  `ai/`, cuando exista un proyecto real en alguno de esos lenguajes.

Los cambios a `AGENTS.md`, `ai/context.yaml`, `ai/capabilities/` y
`ai/policies/global.md` son framework-owned (`managed` en
`ai/installer.py`) — cualquier extensión futura de lo diferido debe
aplicarse en este repo plantilla, no parcheada ad-hoc en un host.
