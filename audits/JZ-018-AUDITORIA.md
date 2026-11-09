# Auditoría JZ-018 — controles, trazabilidad y ontología

**Fecha:** 2026-11-09  
**Repo / rama:** `[JARDINZEN_ROOT]` / `main`  
**Modo:** propuesta solamente. No se autorizaron ni ejecutaron trasplantes.

## Hallazgos confirmados

1. El visor servía HTML reciente mientras el proceso Python conservaba módulos antiguos en memoria. `/api/proposals/status` devolvía 404 aunque el HTML mostraba los controles. Se añadió un endpoint de salud versionado; el lanzador compara el build y reinicia únicamente el proceso `visor.py` de este repositorio.
2. El primer `start()` consultaba las 208.820 rutas antes de producir el primer lote. La petición superaba el timeout del cliente aunque el trabajo persistía. Ahora usa `COUNT(*)` y páginas SQL de hasta 30 archivos.
3. El botón “Procesar siguiente lote” respondió desde la interfaz: el contador persistido pasó de 180 a 210; la consulta posterior mostró 240/208.820. Cada avance procesa hasta 30 filas. “Crear propuestas” está deshabilitado mientras el trabajo está `running`, para evitar duplicados.
4. La comparación anterior vinculaba `system_audit.log` con “Labot-Venue-System” por un token genérico. El build `jz018-paginated-v3` filtra términos generales y exige dos tokens no genéricos, salvo que el nombre del proyecto tenga un único token no genérico. El caso sintético queda en revisión.

## Estado del procesamiento real

- Mapa de metadatos: 3.415.257 entradas y 226 proyectos.
- Dos macetas configuradas, con 208.820 archivos contabilizados para la cola.
- Trabajo 1: `running`, 240 / 208.820 procesados al consultar; 96 `REVIEW`, 144 `REVIEW_BLOCKED`.
- No hay aprobaciones ni movimientos. No se leyó contenido ni se calcularon hashes de los archivos fuente.
- `index.sqlite3` contiene 122 chunks vectoriales; no representa semánticamente los 3,4 millones de entradas.

## Resolución de la pregunta ontológica

La clasificación completa **no está resuelta todavía**. El inventario es el mapa físico de rutas y metadatos. El catálogo detecta árboles y módulos; JZ-017 crea propuestas limitadas a nombres y metadatos dentro de las dos macetas. No lee contenido para decidir parcela, árbol, arbusto, rama u hoja; no genera una página Markdown por archivo ni relaciones vectoriales para el mapa completo. `WORLD_MODEL.md` formaliza esas entidades y separa hecho observado, candidato y decisión para guiar la fase siguiente. La cola actual no es RAG.

## Validación

- `python -m py_compile propuestas.py visor.py`: correcto.
- `git diff --check`: correcto; Git solo avisó de conversión LF/CRLF en Windows.
- `/api/health`: `proposal_api=true`, `proposal_build=jz018-paginated-v3` tras el arranque actualizado.
- Fixture de `_match`: `system_audit.log`, `telemetry.csv` y `Rainbow-CSV.csv` quedan sin asociación; `Labot-Venue-test.csv` propone Labot con dos tokens y `candidate_only`.
- Flujo aislado previo con SQLite temporal: 75 elementos en páginas 30/30/15, 75 únicos y cero estados mutables.
- Sin lectura real de contenidos, barrido adicional, movimientos, renombres, acceso a Drive ni push.

## Git

El commit inicial captura el paquete existente y establece la base local. Un commit separado registra JZ-018, el modelo del mundo, Northstar, backlog y esta auditoría. Los SHA quedan en `git log`; el manifiesto SHA-256 acompaña los archivos de auditoría.
