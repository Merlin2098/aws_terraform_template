# ADR-FW-003 — Detección de Divergencia por Huellas de Contenido; Versión como Etiqueta de Gobernanza

## Status

Proposed

## Context

El framework se distribuye a repositorios *host* por **copia de artefactos** de
gobernanza (`AGENTS.md`, `CLAUDE.md`/`GEMINI.md`, `ai/policies/`, `ai/skills/`,
`specs/template/`, descriptores de capacidad, hooks, `.template-profile.yaml`),
mediante [`ai/installer.py`](../../ai/installer.py). No es la instalación de un
paquete: es la copia de un árbol.

El instalador ya escribe estado en el host (`.framework-version.json`,
`STATE_FILENAME`) con `framework_version`, `enabled_capabilities` y un
`framework_manifest` (lista de rutas framework-owned). Sin embargo, la decisión de
"¿hay cambios que propagar?" en `update_template` se reduce **a comparar la cadena
de versión**:

```python
if previous_version == current_version and not force:
    return {"up_to_date": True, ...}   # se salta todo
```

[SPEC-FW-016](SPEC-FW-016.md) analizó este mecanismo y ocho estrategias
alternativas de detección de divergencia. Sus conclusiones, que esta ADR registra
como decisión bajo Policy 002:

* La versión semántica es una señal **demasiado gruesa**: no detecta ediciones
  locales del host sobre artefactos framework-owned, no detecta divergencia parcial
  dentro de una misma versión, y empuja `--force` como flujo de trabajo real
  (documentado en
  [`docs/windows_setup/template_versioning.md`](../../docs/windows_setup/template_versioning.md)).
* El `framework_manifest` actual es solo una lista de rutas para borrar huérfanos;
  **no contiene huellas de contenido**, por lo que el sistema no puede responder
  *qué* archivos divergen ni *quién* los cambió.
* El modelo de distribución es **copia, no repositorio Git compartido** (`ai/` está
  gitignored en hosts), por lo que mecanismos basados en Git (subtree/submódulo) o
  en firma criptográfica imponen coste sin resolver el riesgo presente.

SPEC-FW-016 recomendó combinar tres estrategias —huellas por archivo (A), hash de
árbol agregado (B) y convención de propiedad por artefacto (H)— y **conservar** la
versión cambiándole el rol.

## Decision

El framework adopta un **detector de divergencia basado en huellas de contenido**
y **degrada la versión semántica de detector a etiqueta de gobernanza**.

Concretamente:

1. **Huella por archivo (A) — detector primario.** `framework_manifest` evoluciona
   de `list[str]` a un mapa `{ruta: {sha256, ownership}}`. En cada
   `--update`/`--dry-run`, el instalador recomputa el `sha256` de cada artefacto en
   el host y lo cruza con (i) el hash registrado en el estado y (ii) el hash del
   template actual, clasificando cada archivo en *unchanged / updatable / conflict
   / locally-modified*.

2. **Hash de árbol (B) — índice de sincronía.** El estado gana un `tree_digest`
   (hash raíz del árbol framework-owned, con normalización EOL). Si el digest del
   template coincide con el del estado, el host está sincronizado y se omite el
   recorrido por archivo; solo al diferir se desciende a las huellas de (A).

3. **Propiedad declarada (H) — qué cuenta como drift.** Cada artefacto lleva un
   `ownership` derivado del registro tipado de capacidades (ADR-FW-001):
   `managed` (el framework sobrescribe en update), `template` (framework-owned, el
   host no debería editar; drift = advertencia), `generated` (renderizado en
   destino — se hashea el resultado escrito, no el fuente), `host` (fuera del
   manifest, nunca se toca).

4. **La versión se conserva, con rol nuevo.** `framework_version` deja de decidir
   "up to date" y pasa a ser **etiqueta de gobernanza**: nombra la generación del
   framework, ancla las reglas de compatibilidad/breaking-change y soporta el
   changelog. El detector de "¿coincide bit a bit?" pasa a ser el par
   (`tree_digest` + huellas). **Versión para gobernar; hashes para detectar.**

**No se adopta** —ni se introduce en este cambio— la distribución por Git
subtree/submódulo, la firma criptográfica del manifest, ni el análisis semántico
general. Quedan diferidos y condicionados a necesidad real (ver Scope).

La adopción es **aditiva y compatible hacia atrás**: un estado legacy sin
`tree_digest` ni huellas degrada al comportamiento actual de comparación por
versión.

## Consequences

### Positive

* Detección de drift global, edición local y divergencia parcial — las tres
  preguntas que el mecanismo por versión no responde.
* Auto-diagnóstico **offline**: el host se compara contra su propio estado sin
  necesitar el template presente.
* `--update --dry-run` se convierte en un *plan en seco* legible (estilo
  `terraform plan`): el usuario ve qué se actualizaría, qué editó él y qué está en
  conflicto antes de tocar nada.
* Elimina la dependencia de `--force` como flujo real; recupera el historial de
  actualización.
* Reutiliza lo existente (`framework_manifest`, `read/write_state`,
  `is_framework_owned`) y el registro de capacidades (ADR-FW-001) como fuente del
  `ownership`; sin cambiar el modelo de distribución por copia.
* Da al comando `restore` (SPEC-FW-009) una entrada precisa: reconciliar solo los
  `managed`/`template` divergentes.

### Negative

* El estado pasa de lista simple a mapa con hashes: mayor tamaño y una migración de
  formato (mitigada por la degradación compatible hacia atrás).
* Los artefactos `generated` (p. ej. `.template-profile.yaml`, renderizado por
  `render_profile`) exigen hashear el resultado escrito, no el fuente — una
  categoría aparte que el código debe tratar explícitamente.
* Sensibilidad a CRLF/EOL en el hash de árbol en hosts win32: obliga a normalizar
  saltos de línea antes de hashear (apoyado en `.gitattributes`).
* `.framework-version.json` editado o borrado a mano produce estado mentiroso; el
  detector debe validar el estado al leerlo (ya existe `try/except` en `read_state`).

## Migration Strategy

Aditiva, escalonada (alineada con el roadmap de SPEC-FW-016):

* **Fase 1 — huellas + propiedad (A + H).** Migrar `framework_manifest` a mapa con
  `sha256` y `ownership`; hashear el resultado renderizado para `generated`. Añadir
  el reporte por archivo a `--update --dry-run`. Estado legacy sin hashes ⇒
  comportamiento actual sin cambios.
* **Fase 2 — agregación + restore (B).** Añadir `tree_digest` con normalización EOL
  y short-circuit. `restore` (SPEC-FW-009) consume la clasificación: reescribe
  `managed`/`template` divergentes, deja `host`, confirma en `conflict`. Reporte de
  drift apto para CI.
* **Fase 3 — condicional.** Análisis semántico (G) solo para artefactos parseables
  (políticas/perfil YAML); firma del manifest (F) solo ante un modelo de amenaza
  real (distribución pública/multi-organización); modo Git-subtree opcional (D) solo
  bajo su propio ADR. Ninguno por defecto.

Cada fase debe aterrizar como un SPEC-FW de seguimiento independiente.

## Scope

Esta ADR gobierna el **mecanismo de detección de divergencia y la gobernanza de
versión** del framework distribuido por copia. No introduce cambios en:

* Arquitectura de capacidades (gobernada por ADR-FW-001).
* Gestión de dependencias / package manager (gobernada por ADR-FW-002).
* Skills, domains, hooks, generación de artefactos, scanners.
* El contrato host-owned (`src/`, `infra/`, `tests/`, `specs/project/`), que
  permanece intocable.

Quedan **explícitamente fuera** y diferidas: distribución por Git subtree/submódulo,
firma criptográfica y análisis semántico general (condicionadas a necesidad real,
cada una con su propio ADR si se adoptan).

## Decision Summary

El framework adopta **detección de divergencia por huellas de contenido** —
`sha256` por archivo + `tree_digest` de árbol + `ownership` por artefacto— como
mecanismo de detección, y **conserva la versión semántica como etiqueta de
gobernanza, no como detector**. Versión para gobernar; hashes para detectar.
Distribución por Git, firma criptográfica y análisis semántico general quedan
diferidos y condicionados a necesidad real.

## References

* [SPEC-FW-016](SPEC-FW-016.md) — análisis que origina esta decisión (inventario,
  comparativa, riesgos, roadmap).
* [ADR-FW-001](ADR-FW-001.md) — registro tipado de capacidades (fuente del
  `ownership`); patrón de compatibilidad aditiva.
* [ADR-FW-002](ADR-FW-002.md) — estandarización en `uv` (precedente de formato y de
  "legacy-mark, do not remove").
* [`ai/installer.py`](../../ai/installer.py) — `STATE_FILENAME`,
  `framework_manifest`, `update_template`, `is_framework_owned`,
  `read_state`/`write_state`.
* [`docs/windows_setup/template_versioning.md`](../../docs/windows_setup/template_versioning.md)
  — comportamiento actual de detección por versión.
* `ai/policies/global.md` — Policy 002 (ADR antes de cambio de arquitectura).
