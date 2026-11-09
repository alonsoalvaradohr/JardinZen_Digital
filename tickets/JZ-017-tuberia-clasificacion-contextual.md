# JZ-017 — Tubería clasificadora contextual basada en el cerebro del Jardín

**Estado:** Implementación parcial · primera iteración en modo propuesta
**Prioridad:** P0 — bloquea nuevos trasplantes automáticos  
**Tipo:** Arquitectura / clasificación / gobernanza  
**Incidente que lo origina:** las carpetas `061126` y `071126` fueron clasificadas por muestra parcial y enviadas a categorías genéricas, sin contrastarlas con el proyecto Labot ni clasificar sus archivos internos.

## Objetivo

Convertir el mapa de metadatos, el catálogo de proyectos y el índice local de Jardinero en un cerebro consultable que permita procesar los elementos de las macetas como una tubería durable. Cada archivo debe inventariarse e interpretarse individualmente, vincularse con evidencia a un proyecto conocido y recibir una propuesta de nombre y destino antes de que se realice cualquier trasplante.

La IA propone e interpreta; las rutas conocidas, las relaciones verificables, las reglas de seguridad y la revisión humana gobiernan la acción. Ninguna puntuación de confianza del modelo se considera por sí sola prueba de corrección.

## Contexto y fallo observado

El flujo actual de `jardinero.py` trata una carpeta de maceta como una unidad: `sample_item()` toma hasta ocho archivos según orden de recorrido, `llm_classify()` propone dominio/proyecto/descripción y `migrate()` mueve la carpeta completa. La carpeta recibe una descripción generada; sus archivos internos conservan sus nombres. No se consulta previamente `inventario.sqlite3`/`proyectos.py` para buscar el árbol conocido más probable ni se construye consenso a partir de todos los archivos.

En el ejemplo que motivó este ticket, el material de mediciones térmicas debería poder asociarse con el árbol/proyecto Labot y proponerse en `[CLOUD_WORKSPACE]\30-quality-validation\evidence\thermal-test`, sujeto a autorización de esa raíz. La salida previa `Personal\Temperature_Monitoring` no satisface esa expectativa.

## Principio de clasificación y precedencia

Resolver la identidad del proyecto primero y el nombre descriptivo después. Usar señales en este orden, guardando procedencia para cada señal:

1. Ruta/raíz de proyecto confirmada por el usuario o una regla explícita.
2. Identidad estructural determinista: raíz `.git` (incluidos archivos `.git` de worktrees/submódulos), manifiestos, jerarquía y módulos detectados; no abrir ni ejecutar hooks/configuración Git no confiables.
3. Enlaces y referencias explícitas entre documentos/proyectos, con tipo de relación y origen.
4. Coincidencias con registros y documentos previos del cerebro local: nombres, contenido extraído, hashes, FTS y vectores; una coincidencia vectorial es evidencia candidata, no dependencia cierta.
5. Clasificador local como fallback para interpretar tema y describir; no puede inventar una ruta raíz ni sustituir una coincidencia exacta fuerte.

Una señal fuerte contradictoria, múltiples proyectos plausibles o evidencia insuficiente producen `REVIEW`; nunca se resuelve por promedio opaco ni por una confianza autodeclarada del LLM.

## Flujo requerido

### Estación A — Descubrir e inventariar

- Crear un `job` durable y un `job_item` por archivo, con ruta de origen, padre, nombre, extensión, tamaño, fechas disponibles, hash cuando corresponda, estado, intentos y errores.
- En carpetas, completar el manifiesto recursivo antes de proponer movimiento; documentar límites, errores y archivos inaccesibles. Procesar por lotes reanudables y no mantener progreso en la memoria de una conversación.
- Reutilizar el mapa global de metadatos como contexto de descubrimiento, sin confundirlo con extracción semántica ni dar por indexado su contenido.

### Estación B — Extraer e indexar localmente

- Detectar formato y extraer texto/metadatos por archivo mediante parsers locales con límites de tamaño/tiempo y estados explícitos (`EXTRACTED`, `UNSUPPORTED`, `EMPTY`, `ERROR`, `SENSITIVE_REVIEW`). Nunca ejecutar archivos, macros ni instrucciones contenidas en estos.
- Crear chunks, FTS y embeddings locales con versión de parser/modelo, hash de entrada y progreso persistido. Indexar antes de decidir el destino cuando el tipo sea legible.
- Producir notas Markdown locales estilo Obsidian para entidades/proyectos y evidencia legible, con enlaces estables a registros/rutas; SQLite sigue siendo fuente de verdad para millones de items, estados y vectores. No crear millones de Markdown duplicados sin una política de tamaño/retención.
- Los Markdown exponen propiedades y enlaces; la similitud semántica se representa como sugerencia con puntuación/modelo, nunca como enlace factual automático.

### Estación C — Resolver proyecto y grupo

- Consultar primero el catálogo de los 226 árboles/606 módulos descubiertos (si sigue vigente, mostrar fecha del mapa) y enriquecer progresivamente proyectos con evidencia legible.
- Para cada archivo registrar candidatos de proyecto/ruta y evidencia exacta: marcador, ancestro, README/manifiesto, texto citado en fragmentos locales, enlace explícito, coincidencia lexical/vectorial.
- Para un lote/carpeta calcular el destino por conjunto: consenso de archivos, pertenencia a una raíz Git/proyecto, fecha/contexto; reportar desacuerdos. No usar solo una muestra de ocho archivos para declarar que todo el conjunto representa un proyecto.
- Conservar contenedores originales como contexto de agrupación; separar subgrupos solo en la propuesta y solicitar revisión si eso alteraría límites de proyecto o una carpeta Git.

### Estación D — Proponer nombres y destinos

- Generar una previsualización por archivo y agrupación: ruta/nombre actuales, ruta/nombre propuestos, razón, evidencia, alternativas, certeza calibrada, conflictos y operación de respaldo prevista.
- Usar una convención configurable y no destructiva, por ejemplo `AAAA/MM/DD/Nombre descriptivo.ext`, preservando extensión y nombre original como metadato/alias. No renombrar usando frases largas del modelo; sanitizar, limitar longitud y evitar colisiones.
- Destino preferido: proyecto conocido y su ubicación canónica confirmada. No crear dominios/proyectos nuevos automáticamente si hay candidato existente con evidencia sólida.
- Si las rutas objetivo son una unidad cloud/virtual o raíz fuera del allowlist, mostrarla como propuesta bloqueada. Este ticket no concede permiso de escritura a `[CLOUD_ROOT]` ni a ninguna raíz nueva.

### Estación E — Revisión y ejecución gobernada

- La primera iteración de esta fase opera en **modo propuesta solamente**: nada se mueve ni renombra por la tubería nueva.
- En el visor, permitir inspeccionar la evidencia y aprobar/rechazar propuestas concretas (archivo o lote), con destinos y nombres visibles antes de aprobar.
- Solo después de autorización separada y concreta para raíces destino, integrar con el journal transaccional existente: respaldo verificado, operación, hash, índice actualizado y rollback/reconciliación.
- Cambios al allowlist de raíces requieren autorización expresa aparte; no inferirla del ejemplo ni del hecho de que la unidad aparezca en el mapa.

## Modelo de datos / trazabilidad mínima

Entidades sugeridas: `jobs`, `job_items`, `extractions`, `chunks`, `entities/projects`, `edges`, `classification_candidates`, `proposals`, `proposal_decisions` y eventos de operación. Cada conclusión debe registrar `source_item`, fragmento/evidencia, regla o modelo, versión, fecha, scores por etapa, decisión y actor. Mantener separado:

- hecho observado (ruta, hash, manifest, enlace literal);
- inferencia léxica/vectorial/modelo;
- decisión humana;
- acción física completada y evidencia hash.

El procesamiento debe poder reanudarse después de cerrar visor, reiniciar Windows o fallar un parser/modelo, sin volver a leer/reclasificar entradas sin cambios.

## Criterios de aceptación

1. En modo propuesta, el lote de prueba reproduce el inventario completo de archivos de cada carpeta, no solo una muestra; indica los archivos no legibles y no modifica el origen.
2. Con un corpus de referencia revisado por el usuario, los documentos térmicos se vinculan al proyecto/árbol Labot y proponen `30-quality-validation/evidence/thermal-test` cuando esa ubicación figure como raíz conocida/autorizada; si no puede confirmarse, queda como candidato visible o bloqueado, nunca se trasplanta.
3. Cada propuesta explica qué señales sustentan proyecto, fecha, nombre y destino; enlaza a evidencia local y distingue hecho de similitud/inferencia.
4. Si archivos de una carpeta apuntan a destinos distintos o la evidencia entra en conflicto, la propuesta marca el conflicto y exige revisión.
5. Ninguna clasificación usa la confianza del LLM como único criterio de aceptación. Evaluar contra conjunto etiquetado y registrar precisión por nivel jerárquico, cobertura y tasa de abstención; fijar umbral de producción solo tras revisar resultados.
6. El visor muestra cola/estación actual, conteos por estado, evidencia, propuestas y errores; detener/reanudar no pierde checkpoints.
7. Pruebas de aceptación cubren documentos duplicados, extensión engañosa, PDF sin texto, archivo sensible, archivo `.git`/worktree, parser fallido, conflicto entre miembros, colisión de nombre, ruta no autorizada y reinicio en cada estación.
8. Antes de cualquier modo de ejecución, se requieren respaldo/hash, test de rollback y autorización concreta de las raíces. Este ticket no habilita el modo de ejecución física.

## Fuera de alcance

- Escanear contenido de unidades no autorizadas, escribir en unidades cloud/virtuales o cambiar raíces autorizadas.
- Mover/renombrar repositorios Git, alterar archivos internos de repositorios, subir contenido a servicios externos o ejecutar código de los documentos.
- Garantizar OCR/CAD/audio/video en esta fase; formatos no soportados van a cola visible.
- Declarar que el mapa de metadatos equivale a un índice semántico completo.

## Dependencias / entrega

- Fuente de contexto: `inventario.sqlite3`, salida de `proyectos.py`, `index.sqlite3`, bitácora y reglas de `AGENTS.md`.
- Coordinar con F2 (grafo simbólico) y F3/F4 (catálogo/extracción/RAG). Esta tubería puede arrancar con candidatos deterministas existentes, pero debe mantener procedencia compatible con las aristas futuras.
- Entregables: esquema migrable SQLite; workers por estación reanudables; Markdown del cerebro con enlaces estables; API/visor de evidencias y propuestas; corpus de evaluación etiquetado; guía operativa y política de autorización.

## Entrega parcial (2026-11-09)

- Añadidos `propuestas.py`, almacenamiento SQLite durable separado (`propuestas.sqlite3`), endpoints locales de estado/inicio/siguiente lote y tarjeta del visor.
- El flujo consume únicamente metadatos ya presentes bajo las dos macetas configuradas, hasta 30 archivos por avance. Conserva metadatos observados y procedencia de coincidencias léxicas con proyectos detectados.
- Cada coincidencia queda como candidata para revisión. Los destinos se marcan bloqueados y no hay aprobación, movimiento ni renombrado.
- No se ejecutó inventario, descubrimiento de proyectos, ni clasificación con datos del equipo durante esta entrega.
- Pendiente: extracción local robusta e indexación por archivo; manifiestos recursivos reanudables de carpetas; hashes y detección de cambios; resolución estructural y por enlaces; consenso/conflicto de grupos; convenciones de nombres configurables y conflictos; decisiones humanas auditables; corpus etiquetado y métricas; pruebas de aceptación; integración con el journal solo tras autorización separada.

## Referencias de diseño

- [Git: repositorio, working tree y objetos tree](https://git-scm.com/docs/gitrepository-layout) — identidad y límites reales de repositorios.
- [Apache Tika: detección y extracción de contenido](https://tika.apache.org/docs/) — parsing por tipo, metadatos y límites para procesamiento robusto.
- [DVC: pipelines reproducibles por etapas y dependencias](https://doc.dvc.org/user-guide/pipelines/defining-pipelines) — trabajos auditables y reanudables con artefactos.
