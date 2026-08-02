# SPEC-FW-016 — Detección de Divergencia y Gobernanza de Distribución sin Archivo de Versión

## Status

Proposed

## Context

El framework se distribuye a repositorios *host* por **copia de artefactos**, no
por instalación de un paquete. El motor es [`ai/installer.py`](../../ai/installer.py),
invocado desde [`install_linux.py`](../../install_linux.py) /
[`install_windows.py`](../../install_windows.py). Lo que se copia no es la carpeta
`ai/` sino un **árbol de artefactos de gobernanza completo**: `AGENTS.md`,
`CLAUDE.md`/`GEMINI.md`, perfiles de plantilla (`.template-profile.yaml`),
políticas (`ai/policies/`), skills (`ai/skills/`), specs (`specs/template/`),
descriptores de capacidad, hooks y configuración. `src/`, `infra/`, `tests/` y
`specs/project/` son **host-owned** (`HOST_OWNED_TOP_LEVEL`, `HOST_OWNED_PATHS`)
y quedan fuera de este análisis.

### Mecanismo actual (lo que realmente existe hoy)

El instalador **ya escribe** un archivo de estado en el host:
`.framework-version.json` (`STATE_FILENAME` en `ai/installer.py:24`). Contiene:

```json
{
  "framework_version": "0.1.0",        // leído de pyproject.toml [project].version
  "installed_at": "...",
  "include_structure": false,
  "enabled_capabilities": ["languages:python", ...],
  "framework_manifest": ["AGENTS.md", "ai/skills/...", ...]  // rutas framework-owned
}
```

La lógica de actualización (`update_template`, `ai/installer.py:525`) hace **una
sola cosa para decidir si hay cambios**: comparar la cadena de versión.

```python
if previous_version == current_version and not force:
    return {"up_to_date": True, ...}   # se salta TODO
```

El `framework_manifest` **no se usa para detectar drift**: solo sirve para borrar
*huérfanos* (archivos que el framework distribuía antes y ya no). No hay hashes de
contenido. Consecuencias documentadas en
[`docs/windows_setup/template_versioning.md`](../../docs/windows_setup/template_versioning.md):

- Si cambias archivos en el template **sin** subir la versión en `pyproject.toml`,
  el host se considera "up to date" y **nada se propaga** (hay que usar `--force`).
- El instalador **no puede saber** si el host modificó localmente un archivo
  framework-owned (`ai/`, `AGENTS.md`, políticas…). En hosts, `ai/` está en
  `.gitignore` (`HOST_EXTRA_GITIGNORE_ENTRIES`), así que ni Git del host lo ve.
- No hay detección de **modificación parcial**: dentro de una misma versión, dos
  hosts pueden tener contenido distinto y el sistema los reporta idénticos.

**El problema real no es "no tenemos versión" — es que la versión es lo único que
miramos, y es una señal demasiado gruesa.** El objetivo de este SPEC es analizar
mecanismos de *detección de divergencia* que no dependan de un número de versión
como única fuente de verdad, y recomendar la gobernanza resultante.

Este es un documento de planificación bajo Policy 002 (ADR antes de cambio de
arquitectura). No implementa código.

---

## 1. Inventario de estrategias posibles

Cada estrategia se evalúa por su capacidad para responder tres preguntas que el
mecanismo actual no responde:

- **Q1 (drift global):** ¿el host está desincronizado del template?
- **Q2 (modificación local):** ¿el host *editó* un artefacto framework-owned?
- **Q3 (parcial):** ¿*qué* archivos concretos divergen, no solo "algo cambió"?

| # | Estrategia                                                    | Núcleo de la idea                                                                                                                                                                     |
| - | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A | **Hash de contenido por archivo (manifest de huellas)** | Extender `framework_manifest` de `list[str]` a `{ruta: sha256}`. Comparar hash actual del archivo en host vs. registrado y vs. template.                                         |
| B | **Hash de árbol agregado (Merkle / hash raíz)**       | Un solo hash que resume todo el árbol framework-owned (estilo Git tree / IaC plan-hash). Igualdad de raíz ⇒ idéntico; desigualdad ⇒ descender a B-hijos para localizar.           |
| C | **Comparación estructural directa (diff en seco)**     | No persistir nada extra: el instalador compara byte-a-byte template↔host en tiempo de `--update --dry-run` y reporta qué difiere.                                                  |
| D | **Git como fuente de verdad**                           | Distribuir vía `git subtree`/submódulo/remote del template en vez de copia opaca; `git diff` responde Q1–Q3 nativamente.                                                        |
| E | **Marcadores embebidos en archivos**                    | Cabecera generada (`# framework-managed: sha=…, src=…`) en cada artefacto editable; un linter detecta edición comparando hash de cuerpo vs. cabecera.                             |
| F | **Firma de contenido / sello criptográfico**           | Firmar el manifest (HMAC o firma asimétrica con clave del framework). Detecta no solo cambio sino*manipulación no autorizada* y prueba procedencia.                                |
| G | **Análisis semántico**                                | Comparar el*significado* (p. ej. reglas de una política, claves de YAML) en vez de bytes, tolerando reformateo/espaciado.                                                           |
| H | **Convención documental + tres niveles de propiedad**  | Declarar explícitamente, por artefacto, su modo:`managed` (sobrescribible), `template` (host no debe tocar), `host` (libre). El drift solo importa en `managed`/`template`. |

Las estrategias **no son excluyentes**: la recomendación (§4) combina A + B + H.

---

## 2. Comparativa detallada

Escala: ◌ nulo · ○ bajo · ◐ medio · ● alto.

| Estrategia                              | Complejidad impl.                           | Confiabilidad            | Drift global (Q1)         | Mod. local (Q2)                              | Parcial (Q3) | UX final                                     | Escalabilidad          |
| --------------------------------------- | ------------------------------------------- | ------------------------ | ------------------------- | -------------------------------------------- | ------------ | -------------------------------------------- | ---------------------- |
| **A · Hash por archivo**         | ○ baja (extiende `write_state`)          | ●                       | ●                        | ●                                           | ●           | ● claro: "estos 3 archivos divergen"        | ●                     |
| **B · Hash de árbol (Merkle)**  | ◐ media                                    | ●                       | ●                        | ◐ (solo si se desciende)                    | ◐           | ◐ "algo cambió" sin descenso               | ● muy barato a escala |
| **C · Diff estructural en seco** | ○ baja                                     | ●                       | ●                        | ◐ (no distingue edición de versión vieja) | ●           | ◐ requiere template presente                | ◐                     |
| **D · Git subtree/submódulo**   | ● alta (cambia el modelo de distribución) | ●                       | ●                        | ●                                           | ●           | ○ exige fluidez en Git; conflictos de merge | ●                     |
| **E · Marcadores embebidos**     | ◐ media (reescribe artefactos)             | ◐ (cabeceras se borran) | ◐                        | ●                                           | ●           | ◐ ruido visual en archivos                  | ◐                     |
| **F · Firma criptográfica**     | ● alta (gestión de claves)                | ●                       | ◐                        | ●                                           | ○           | ○ overkill para uso interno                 | ◐                     |
| **G · Análisis semántico**     | ● alta (un parser por tipo)                | ◐ (depende del parser)  | ◐                        | ◐                                           | ●           | ● "cambió esta regla, no el formato"       | ○ (N parsers)         |
| **H · Convención de propiedad** | ○ baja (metadatos en descriptor)           | ● (como política)      | n/a (habilita las demás) | ● define qué cuenta como drift             | ●           | ● expectativas explícitas                  | ●                     |

Lecturas clave de la tabla:

- **A es el mejor retorno por esfuerzo**: reutiliza el `framework_manifest` que ya
  existe; el cambio es de tipo de dato, no de arquitectura. Responde Q1, Q2 y Q3.
- **B no añade detección que A no tenga**; añade *eficiencia* (un hash raíz para
  decir "idéntico" sin recorrer N archivos). Es una optimización de A, valiosa
  cuando el árbol crece (capacidades nuevas de SPEC-FW-011..014).
- **C** evita persistir estado pero **no distingue** "el host editó el archivo" de
  "el host tiene una versión anterior del template" — colapsa Q2 con Q1.
- **D** es el más potente y el más caro: cambia el contrato de distribución de
  "copia" a "Git compartido", rompe el modelo `ai/` gitignored en hosts, e impone
  resolución de conflictos al usuario final. Es una decisión de producto, no un
  ajuste del instalador.
- **G** es valioso solo para artefactos donde el formato no importa (YAML de
  política), pero requiere un parser por tipo de artefacto → no escala como
  mecanismo *general*.
- **H** no detecta nada por sí mismo; **define qué divergencia importa**. Sin él, A
  marcaría como "drift" cualquier edición legítima del host. Es el prerrequisito
  conceptual.

---

## 3. Riesgos por enfoque

| Estrategia                              | Riesgos principales                                                                                                                                                                                                 | Mitigación                                                                                                                                                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A · Hash por archivo**         | `.framework-version.json` puede editarse o borrarse a mano → estado mentiroso. Hashes de archivos con render dinámico (`.template-profile.yaml` se genera por `render_profile`) no coinciden con el fuente. | Hashear el**resultado renderizado** que se escribió, no el fuente; tratar archivos renderizados como categoría aparte (`generated`). Validar estado al leer (ya hay `try/except` en `read_state`). |
| **B · Hash de árbol**           | Sensible al orden y a normalización de saltos de línea (CRLF en Windows — el repo es win32). Un solo bit cambia la raíz sin decir dónde.                                                                       | Normalizar EOL antes de hashear (`.gitattributes` ya existe); ordenar rutas (el manifest ya se guarda `sorted`); guardar también hashes por archivo (A) para el descenso.                                   |
| **C · Diff en seco**             | Requiere el template físicamente presente en el momento de comprobar; un host clonado sin el template no puede auto-diagnosticarse.                                                                                | Solo válido como modo del instalador, no como auto-check del host. Combinar con A para auto-diagnóstico offline.                                                                                               |
| **D · Git subtree/submódulo**   | Conflictos de merge expuestos al usuario; rompe `ai/` gitignored; acopla el host al historial del template; curva de aprendizaje.                                                                                 | Si se adopta, hacerlo opcional ("modo avanzado") y nunca por defecto. Fuera del alcance recomendado.                                                                                                             |
| **E · Marcadores embebidos**     | Contaminan archivos visibles al agente IA (ruido en `AGENTS.md`); fáciles de borrar accidentalmente; algunos formatos no admiten comentarios (JSON).                                                             | Limitar a formatos con comentarios; no aplicar a Markdown de cara al agente. Riesgo > beneficio frente a A.                                                                                                      |
| **F · Firma criptográfica**     | Gestión de claves, rotación, distribución de la clave pública. Resuelve un problema (manipulación maliciosa) que el caso de uso —template interno copiado a hosts propios— no tiene.                         | Diferir hasta que exista un modelo de amenaza real (distribución pública/multi-org).                                                                                                                           |
| **G · Análisis semántico**     | Cada tipo de artefacto necesita su parser; un parser con bug reporta falsos negativos (drift no detectado) → peor que no tenerlo.                                                                                  | Aplicar solo a artefactos donde ya hay parser (perfil YAML via `ai/runtime/profile.py`); no generalizar.                                                                                                       |
| **H · Convención de propiedad** | Si la clasificación está mal, A genera ruido (marca como drift lo que el host puede editar) o silencia drift real.                                                                                                | Derivar la clasificación del registro de capacidades (`ai/capabilities/`), única fuente de verdad ya existente.                                                                                              |

**Riesgo transversal del mecanismo actual (no migrar):** seguir comparando solo la
cadena de versión perpetúa que `--force` sea el flujo real de trabajo, lo que
—según el propio doc de versionado— "hace invisible el historial de actualización".

---

## 4. Recomendación de arquitectura

**Adoptar A + B + H. No adoptar D, E, F como mecanismo base; reservar G y F para
casos puntuales.**

Arquitectura objetivo, mínima y aditiva sobre lo que ya existe:

```
.framework-version.json  (evoluciona; NO se reemplaza)
├── framework_version        # se conserva: etiqueta humana / hito, NO el detector
├── enabled_capabilities     # se conserva
├── tree_digest              # (B) sha256 del árbol framework-owned normalizado
└── framework_manifest       # (A) pasa de list[str] a:
        { "AGENTS.md":        {"sha256": "...", "ownership": "managed"},
          "ai/policies/global.md": {"sha256": "...", "ownership": "template"},
          ".template-profile.yaml": {"sha256": "...", "ownership": "generated"} }
```

- **(H) Ownership** por artefacto, derivado del registro de capacidades, no
  inventado: `managed` (el framework sobrescribe en update), `template`
  (framework-owned pero el host no debería editar; drift = advertencia),
  `generated` (renderizado en destino; se hashea el resultado escrito), `host`
  (fuera del manifest, nunca se toca — ya cubierto por `is_framework_owned`).
- **(A) Hash por archivo** es el detector primario. En cada `--update`/`--dry-run`,
  el instalador recomputa el sha256 de cada artefacto en el host y lo compara con:
  (1) el hash registrado en el estado → **Q2: ¿el host lo editó tras instalar?**;
  (2) el hash del template actual → **Q1/Q3: ¿el template cambió este archivo?**.
  El cruce de ambas comparaciones clasifica cada archivo en: *sin cambios*,
  *actualizable* (template cambió, host no tocó), *en conflicto* (ambos cambiaron),
  *editado localmente* (host tocó, template no).
- **(B) `tree_digest`** es el atajo: si el digest del template == el del estado, el
  host está sincronizado y se omite el recorrido completo (rendimiento a escala).
  Solo si difieren se desciende a los hashes por archivo de (A).
- **`framework_version` se conserva** pero cambia de rol: deja de ser *el detector*
  y pasa a ser una **etiqueta de gobernanza** legible (hito/compatibilidad), igual
  que un tag de Git no es lo que detecta cambios sino lo que los nombra. Ver §7.

Por qué esta combinación y no Git (D): el contrato de distribución del framework es
*copia*, no *repo compartido* — `ai/` está deliberadamente gitignored en hosts. A+B
da detección a nivel Git (hashes de contenido, descenso por árbol) **sin** imponer
el modelo de merge de Git al usuario final, y sin cambiar el contrato. Es el
patrón de los gestores de paquetes/IaC: un lockfile con huellas + un plan en seco
que muestra el diff (`terraform plan`, `npm ci` verificando integridad), aplicado
al árbol de artefactos.

### Encaje con el trabajo en curso

`is_framework_owned`, `framework_manifest` (borrado de huérfanos) y `read/write_state`
ya existen y se conservan. El registro tipado de capacidades (ADR-FW-001,
SPEC-FW-006) es la fuente natural del campo `ownership` de (H). El comando
`restore` (SPEC-FW-009) es el consumidor natural de la detección: "restaurar" =
"reescribir los `managed`/`template` que divergen". Nada de esto rompe a hosts
legacy: un estado viejo sin `tree_digest`/hashes degrada a la comparación de
versión actual (compatibilidad hacia atrás aditiva, como ADR-FW-001).

---

## 5. Roadmap evolutivo (1 / 2 / 3 años)

**Año 1 — Detección de contenido (A + H), aditiva.**

- Migrar `framework_manifest` a mapa `{ruta: {sha256, ownership}}`; hashear el
  resultado *renderizado* para `generated`.
- Modo `--update --dry-run` reporta por archivo: *unchanged / updatable / conflict
  / locally-modified* (resuelve Q1–Q3 sin tocar el modelo de distribución).
- `ownership` derivado del registro de capacidades.
- `framework_version` se conserva tal cual; deja de ser la única señal.
- Compatibilidad: estado legacy sin hashes ⇒ comportamiento actual.

**Año 2 — Agregación y gobernanza (B), integración con `restore`.**

- Añadir `tree_digest` (Merkle/raíz) con normalización EOL; short-circuit cuando
  coincide.
- `restore` (SPEC-FW-009) consume la clasificación: reescribe `managed`/`template`
  divergentes, deja `host`, pide confirmación en `conflict`.
- Reporte de drift como salida de CI (hosts desactualizados detectables en pipeline,
  el caso de uso citado en el doc de versionado para "cuándo subir versión").

**Año 3 — Gobernanza semántica/firmada (G/F) solo donde aporte.**

- (G) Comparación semántica para artefactos parseables (políticas/perfil YAML):
  distinguir "cambió una regla" de "cambió el formato".
- (F) Firma del manifest **solo si** aparece un modelo de amenaza real
  (distribución pública o multi-organización). Hasta entonces, no.
- (D) Evaluar un modo Git-subtree *opcional* para hosts avanzados — nunca por
  defecto, registrado en su propio ADR.

---

## 6. Estrategia recomendada para un framework de agentes IA distribuido por copia

Para este caso concreto —artefactos de gobernanza (`AGENTS.md`, políticas, skills,
specs) copiados a hosts donde la carpeta del framework está gitignored— la
estrategia es:

1. **Manifest de huellas con propiedad declarada** (A+H) como detector. Es lo que
   un gestor de paquetes hace con su lockfile, adaptado a "copia de árbol".
2. **Hash de árbol** (B) como índice rápido de "sincronizado / no".
3. **Plan en seco** (`--update --dry-run`) como UX principal: el usuario ve, igual
   que en `terraform plan`, exactamente qué se actualizaría, qué editó él, y qué
   está en conflicto — **antes** de tocar nada.
4. **`restore`** como aplicador idempotente que reconcilia drift respetando la
   propiedad (`host` nunca se toca; `conflict` requiere confirmación).
5. **Nada de claves ni Git compartido por defecto**: el caso de uso es interno y de
   confianza; F y D añaden coste sin resolver un riesgo presente.

El principio rector coincide con el del propio repo (AGENTS.md: *Simple. Explícito.
Reproducible.*): la detección debe ser **offline** (el host se auto-diagnostica con
su `.framework-version.json` sin necesitar el template), **explícita** (un diff
legible, no un booleano) y **reproducible** (mismos hashes ⇒ mismo veredicto).

---

## 7. ¿Mantener el concepto de "versión" o reemplazarlo?

**Conservar la versión, pero degradarla de *detector* a *etiqueta de gobernanza*.**

La versión semántica (`pyproject.toml` → `framework_version`) **no debe seguir
siendo el mecanismo que decide si hay drift** — es demasiado gruesa: no ve
ediciones locales, no ve cambios intra-versión, y empuja al `--force` como flujo
real. Pero **no debe eliminarse**:

- Sigue siendo la **etiqueta humana** de un hito ("este host corre 0.4.x") y la
  base para reglas de **compatibilidad/breaking-change** (un major bump puede
  forzar reinstalación aunque los hashes "casi" coincidan).
- Es la unidad natural para **comunicar** cambios (changelog, "qué trae esta
  versión"), algo que un hash no comunica.
- Es barata de conservar y ya está integrada.

El **detector de divergencia** pasa a ser el **par (hash de árbol + manifest de
huellas con propiedad)**. Es decir: la versión responde *"¿qué generación del
framework es esta?"*; los hashes responden *"¿coincide bit a bit este host con esa
generación, y qué editó el host?"*. Son preguntas distintas y cada mecanismo debe
responder la suya.

Analogía: en un gestor de paquetes la **versión** nombra la release y el
**lockfile/hash de integridad** garantiza y verifica el contenido. Nadie elige una
en lugar de la otra; cumplen funciones complementarias. Este framework debe adoptar
el mismo reparto: **versión para gobernar, hashes para detectar.**

---

## Out of scope

- Implementar el mapa de huellas, `tree_digest`, el modo de reporte o `restore` —
  son specs de seguimiento, no este documento.
- Cambiar el modelo de distribución a Git subtree/submódulo (D) — requeriría su
  propio ADR bajo Policy 002.
- Firma criptográfica (F) y análisis semántico general (G) — diferidos a Año 3 y
  condicionados a necesidad real.
- `src/`, `infra/`, `tests/`, `specs/project/` — host-owned, fuera del análisis.

## References

- [`ai/installer.py`](../../ai/installer.py) — `STATE_FILENAME`, `framework_manifest`,
  `update_template`, `is_framework_owned`, `read_state`/`write_state`.
- [`docs/windows_setup/template_versioning.md`](../../docs/windows_setup/template_versioning.md)
  — comportamiento actual de detección por versión y el workaround `--force`.
- [`specs/rework/SPEC-FW-005.md`](SPEC-FW-005.md) — plan de refactor; restore (SPEC-FW-009),
  registro de capacidades.
- [`specs/rework/ADR-FW-001.md`](ADR-FW-001.md) — registro tipado de capacidades
  (fuente del campo `ownership`); patrón de compatibilidad aditiva.
- [`specs/rework/ADR-FW-003.md`](ADR-FW-003.md) — decisión que registra A+B+H y el
  rol de la versión, derivada de este análisis (Policy 002).
- `ai/policies/global.md` — Policy 002 (ADR antes de cambio de arquitectura): la
  adopción de A+B+H y el rechazo/diferimiento de D/F/G quedan registrados en
  ADR-FW-003.
