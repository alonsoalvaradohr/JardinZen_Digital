# Auditoría JZ-019 — RAW/RAG local y catálogo del Jardín

Fecha: 2026-11-09 11:45 CST  
Estado: implementación desplegada; job de ingestión RAW/RAG activo.

## Resultado observado

- El inventario de metadatos existente contiene 3,415,257 filas. El job RAW/RAG se limita a raíces físicas `C:\`, `D:\`, `E:\`; universo declarado: 2,918,993 archivos. `[CLOUD_ROOT]` y unidades virtuales/cloud están excluidas.
- El catálogo finalizó sobre ese inventario: 9,478 marcadores, 13 repositorios con raíz Git (árboles), 61 módulos y 36 arbustos/candidatos de manifiesto. Se excluyen instalaciones y paquetes típicos (Python, TeX Live, extensiones VS Code, Arduino tooling, `.pio`, caches/dependencias). El número anterior 226 no representaba proyectos: sumaba manifiestos y raíces Git sin consolidar.
- A las 11:45 CST el proceso reportaba `running`, 336,647/2,918,993 filas inspeccionadas, 181 documentos extraídos, 2,006 chunks y 2,006 embeddings. `documents` guardan RAW comprimido, hash SHA-256, ruta, metadatos, extractor y estado en `%LOCALAPPDATA%\JardinZen\brain.sqlite3`. El cursor se actualiza por lote y permite reanudar.
- Ollama está local y disponible con `qwen3-embedding:0.6b` (1024 dimensiones) y `qwen2.5:3b`; consultas semánticas usan el mismo modelo de embeddings que la indexación. FTS5 aporta búsqueda léxica. El visor en `http://127.0.0.1:8765` muestra controles y progreso, y genera una vista pequeña de notas Markdown en `%USERPROFILE%\JardinZen\Brain`.
- Primera búsqueda vectorial de prueba devolvió vecinos irrelevantes (distancia >1) porque el primer lote todavía era contenido de sistema/juegos. El buscador ahora descarta vecinos con distancia >0.65: ArduinoJson aún no tenía documentos indexados y el resultado quedó vacío en vez de inventar evidencia.

## Causa de fallos y correcciones

1. `brain.start()` contaba filas `items` desde `brain.sqlite3`, aunque la tabla vive en `inventario.sqlite3`. La API devolvía `no such table: items`, sin crear job. Corregido.
2. Cada checkpoint pedía filas del inventario y SQLite elegía el índice por `root`, ordenando millones de rutas nuevamente. El cursor avanzaba muy lento. Se fuerza `items_tree_metrics(path,kind,size)`, que cubre el recorrido ordenado por ruta.
3. La deduplicación de manifiestos guardaba claves con el casing original y las consultaba en minúsculas; manifiestos anidados se convertían en 165 arbustos. Normalizada la clave: quedan 36 grupos.
4. El detector anterior trataba dependencias/herramientas instaladas como candidatos de proyecto. Se excluyeron los componentes encontrados en evidencia del equipo.
5. El servidor reanudaba automáticamente jobs explícitamente detenidos tras reiniciar. Ahora solo reanuda jobs marcados como `running` o `interrupted`; `stopped` requiere acción del usuario.

## Qué hace y qué no hace la decisión actual

La extracción y los embeddings **leen contenido** de formatos soportados. Un archivo se vincula como hecho a un árbol cuando su ruta está contenida por esa raíz. La búsqueda semántica encuentra pasajes por similitud, pero similitud no demuestra pertenencia ni define un destino. La interfaz aún no genera clasificación contextual archivo→arbusto/árbol basada en contenido y no trasplanta ni renombra. Esa siguiente fase necesita candidatos explicables, criterios/etiquetas de evaluación y revisión humana antes de cualquier cambio físico.

Formatos documentales/textuales tienen parsers con límite de tamaño; binarios, secretos detectables, carpetas de sistema/generadas y extensiones no soportadas se omiten o marcan. No hay OCR para PDF escaneado ni parsing exhaustivo de CAD. El mapa inicial tuvo errores de acceso y reparse points omitidos, por lo que cobertura no significa perfección. Fuentes no se editan ni ejecutan, y no se transmite contenido fuera de localhost.

## Reproducción/operación

- Abrir: `ABRIR_JARDIN.cmd`; visor `http://127.0.0.1:8765`.
- En el panel Cerebro local, **Continuar** reanuda el job si está detenido; pausa/detención son durables.
- RAW/RAG: `%LOCALAPPDATA%\JardinZen\brain.sqlite3`; inventario de origen: `%LOCALAPPDATA%\JardinZen\inventario.sqlite3`; notas Obsidian: `%USERPROFILE%\JardinZen\Brain`.
- Dependencias Python en `requirements-brain.txt`.
- Código se valida en el commit de esta fase; ningún push ni movimiento de archivos fuente.
