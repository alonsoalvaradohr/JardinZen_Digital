# Ticket JZ-018 — Visor de propuestas, trazabilidad y World Model

## Identidad

- ID: JZ-018
- Título: Reparar controles de propuestas y anclar el flujo al World Model del Jardín
- Estado: DONE
- Modo: IMPLEMENTATION
- Fecha: 2026-11-09
- Repo / rama / commit inicial: [JARDINZEN_ROOT] / main / ba5c5ecdcc29197982f638e916afc373d27a3298

## Evidencia inicial

- Etiqueta: observed
- Qué ocurre ahora: `http://127.0.0.1:8765/api/proposals/status` devuelve 404 desde el proceso activo iniciado 2026-11-09 09:16. El HTML en disco sí contiene los botones. El proceso Python sirve HTML desde disco, pero tiene módulos importados en memoria.
- Qué debe ocurrir: `ABRIR_JARDIN.cmd` debe detectar API de propuesta ausente y reiniciar exclusivamente el servidor Jardinero de esta ruta; las acciones deben mostrar progreso o error HTTP visible.
- Causa adicional observada: JZ-017 usa `_match()` sobre tokens de nombre de archivo contra nombre de proyecto; aún no hace indexación semántica ni decide rama/arbusto con contenido.
- Riesgo / reversión: servidor local reiniciable; cambios de código locales y revertibles por Git. No se hacen movimientos ni escrituras a raíces de usuario.

## Alcance

### Scope in

- `.gitignore`, `NORTHSTAR.md`, `WORLD_MODEL.md`
- `ABRIR_JARDIN.ps1`, `visor.py`, `visor.html`, `propuestas.py`
- `BACKLOG.md`, `ROADMAP.md`, `README.md`, `STATE.md`, `AGENTS.md`
- `tickets/active/JZ-018-visor-trazabilidad-y-world-model.md`

### Scope out

- `jardinero.py` y toda acción física de mover/renombrar.
- Inventario en vivo, extracción de contenido real, nubes y repositorios externos.
- Escritura en `[CLOUD_WORKSPACE]\...` o autorización de raíz nueva.
- Push remoto, despliegue o publicación.

## Criterios de aceptación

- [x] Git local registra el snapshot fuente existente y un commit separado con este ticket/corrección.
- [x] API de salud versionada; el lanzador detecta build obsoleto y reinicia solo el visor de este repo.
- [x] El botón de lote respondió desde la interfaz: el contador persistido avanzó de 180 a 210; luego se observó 240/208.820. “Crear propuestas” queda deshabilitado con un trabajo activo para evitar duplicados.
- [x] Conteo y páginas SQL acotadas; no materializa las 208.820 rutas en memoria.
- [x] Extensiones y términos comunes no bastan para asociar un archivo; fixture confirmó la corrección.
- [x] World Model y Northstar distinguen jardín/parcela/árbol/arbusto/rama/hoja y separan hechos, candidatos y decisiones.
- [x] Backlog/roadmap/README explicitan que JZ-017 solo usa metadatos y que RAG semántico por archivo sigue pendiente.
- [x] Fixture aislado con SQLite temporal: 75 elementos en lotes 30/30/15, 75 únicos, cero estados mutables.
- [x] Validación, auditoría y cierre registrados; hash de commit en Git y SHA-256 en manifiesto.

## Validación y evidencia

- Comandos ejecutados: `python -m py_compile propuestas.py visor.py` OK; `git diff --check` OK (aviso de normalización de fin de línea LF/CRLF de Git en Windows); `/api/health` confirma `proposal_api=true`, build `jz018-paginated-v3`.
- Comandos no ejecutados: acceso a Drive/otras raíces, barrido real, indexación de contenido real, trasplantes, push.
- Evidencia humana pendiente: ninguna para la corrección local; decisiones de raíz/destino siguen separadas.

## Cierre en cinco líneas

OBJETIVO: controles operativos, paginación segura y gobernanza JZ-018 documentados.
PUNTO: `main` @ commit local JZ-018; visor en `127.0.0.1:8765`, build `jz018-paginated-v3`.
VISTO: salud correcta; el clic web avanzó el contador; fixture 75/75; compilación y diff limpios.
CAUSA: proceso visor obsoleto y cola sin paginación; asignación por nombre demasiado permisiva.
SIGUIENTE: JZ-017 — extraer contenido por lotes y enlazar evidencia jerárquicamente al World Model, propuesta solamente.

## Regla de parada

Tras dos intentos sin evidencia nueva o 15 minutos sin cambio concreto, registrar el dato que falta.
