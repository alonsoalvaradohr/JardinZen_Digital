# JZ-019 — Cerebro local RAW/RAG y ontología de proyectos

## Identidad

- Estado: IMPLEMENTED · INGESTION RUNNING
- Prioridad: P0
- Objetivo: extraer texto localmente de documentos de C:/D:/E:, indexar FTS + embeddings Ollama con progreso durable y reducir falsos árboles del catálogo.
- Alcance de lectura: raíces físicas ya inventariadas `C:\`, `D:\`, `E:\`.
- Excluido: `[CLOUD_ROOT]` y otras unidades virtuales/cloud; cualquier escritura en fuentes; ejecución de archivos; trasplantes/renombres; transmisión de datos fuera de localhost.

## Criterios de aceptación

- [x] Procesamiento por lotes reanudable, limitado en memoria y con parada/reanudación persistente.
- [x] RAW de extracción local asociado a ruta, hash, tamaño, modificación, parser y estado.
- [x] Búsqueda lexical FTS y semántica por embeddings locales; no crear relaciones factuales automáticas por similitud.
- [x] El catálogo no cuenta cada manifiesto como árbol; separar repositorios, ramas/copias, módulos y dependencias.
- [x] El contenido es dato no confiable; nunca se ejecuta ni se sigue una instrucción que contenga.
- [x] Un piloto local demuestra extracción, embeddings y búsqueda; el job total continúa fuera del chat.
- [x] Reporte/estado/commit y hashes verificables.

## Política de procesamiento

- Incluir formatos de texto/documento conocidos, con límites por tamaño/formato; binarios y formatos sin parser reciben estado explícito.
- Saltar carpetas generadas, cachés, paquetes, secretos/credenciales, `.git` y archivos no legibles.
- Persistir cursor por ruta, checkpoint por archivo, hash del origen, versión de parser y modelo de embedding.
- Mantener RAW/FTS/chunks/embeddings separados del inventario físico y del journal de movimientos.
- No generar un Markdown por cada archivo. Markdown es una vista de entidades/proyectos; SQLite mantiene el corpus masivo.

## Cierre

OBJETIVO: pendiente.
PUNTO: pendiente.
VISTO: pendiente.
CAUSA: 226 incluye 181 raíces de manifiesto y 45 raíces Git con copias/worktrees/dependencias.
SIGUIENTE: construir e iniciar la tubería segura local.

## Evidencia de ejecución · 2026-11-09

- Mapa recatalogado desde el inventario existente: 9,478 marcadores; 13 raíces Git (árboles), 61 módulos y 36 manifiestos independientes agrupados como arbustos en revisión. El conteo anterior de 226 queda reemplazado. Se excluyen paquetes/herramientas instalados (VS Code, Python, TeX Live, Arduino tooling y .pio) para evitar falsos proyectos.
- RAW/RAG local iniciado en `%LOCALAPPDATA%\JardinZen\brain.sqlite3`; inventario metadata contiene 3,415,257 filas y el universo de job cuenta 2,918,993 archivos en C:/D:/E:. Checkpoint observado a las 11:45 CST: 336,647 inspeccionados, 181 documentos extraídos, 2,006 chunks, 2,006 embeddings, 4 errores y 0 elementos bajo revisión sensible. El job conserva cursor y sigue corriendo.
- Se corrigieron tres defectos encontrados en operación: conteo consultaba `items` en la DB RAW (debía usar inventario); el cursor SQL ordenaba todo el volumen por lote; y la consolidación no normalizaba las claves de rutas. La búsqueda semántica filtra vecinos distantes para evitar falsos positivos.
- Límite intencional: los enlaces a árboles son por contención de ruta y evidencia FACT. No se generan todavía asignaciones semánticas archivo→árbol/arbusto ni propuestas de trasplante. Eso requiere etiquetas y evaluación; similitud vectorial no se publica como hecho.
- Evidencia extendida: `audits/JZ-019-AUDITORIA.md`.

## Cierre

OBJETIVO: implementación local de RAW/RAG y corrección del conteo de árboles completadas; ingesta total sigue activa y durable.
PUNTO: 336,647/2,918,993 filas del universo del job a las 11:45 CST, progreso variable según tamaño/formato.
VISTO: 13 árboles, 61 módulos, 36 arbustos candidatos; Ollama responde con embeddings locales.
CAUSA: consulta a base equivocada, ordenamiento completo repetido por lote y claves de ruta no normalizadas al consolidar candidatos.
SIGUIENTE: dejar terminar ingesta; luego construir y evaluar asignación semántica con casos etiquetados antes de usarla para decidir organización.
