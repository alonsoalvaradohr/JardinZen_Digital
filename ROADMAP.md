# ROADMAP de despliegue ejecutable — Jardín Zen Digital

| Hito | Acción real al ejecutar `INICIAR.cmd` | Criterio |
|---|---|---|
| F0 | Crear macetas permanentes Descargas y Escritorio; jardín y BD locales. | Directorios existentes, index.sqlite3 accesible y estado persistido. |
| F1 | Clasificación local, copia de respaldo, traslado físico, SHA-256, FTS5 + embeddings. | Cada elemento trasladado aparece en `moves.COMPLETE` y `docs`, con digest verificado. |
| F3 | Instalar tarea repetitiva Windows de 15 minutos y ejecutar primer lote. | `JardinZen_Jardinero` inscrita, sin más de una instancia. |
| F2 | Recorrer y reestructurar otras raíces y unidades, previa autorización. | BLOQUEADA: sin rutas explícitas ni política de respaldo y dependencias revisada. |
| F4 | Evaluación de consultas y mejora de ontología/modelo. | PENDIENTE de ground truth, Recall@5 aún no medido. |

## Topología

```text
<Descargas real>\00_MACETA\     --> Jardinero local --> %USERPROFILE%\JardinZen\<Dominio>\<Proyecto>\AAAAMMDD\<Nombre>\<Descripcion.ext>
<Escritorio real>\00_MACETA\ ---^                         |
                                                        +--> %LOCALAPPDATA%\JardinZen\index.sqlite3
                                                        +--> %LOCALAPPDATA%\JardinZen\backups\
                                                        +--> %LOCALAPPDATA%\JardinZen\STATE.md
```

## Alcance cerrado (v1)

- Las macetas siempre permanecen en sus ubicaciones reales; no son enlaces.
- Nunca escanear íntegramente Descargas, Escritorio, E: u otros discos por defecto.
- Trasladar unidades documentales individuales o carpetas completas; nunca romper la estructura interna de un proyecto.
- Política conservadora de exclusión. Una clasificación incierta NO mueve el archivo.
- Sin procesamiento automático de recursos no extraíbles o archivos sensibles.
- Sin borrado automático de duplicados ni de respaldos.
- Proceso de instalación **en el equipo Windows del usuario**: el ZIP sólo contiene ejecutables fuente y documentos, no se ha ejecutado aún sobre ese equipo.

## Evolución al Jardín navegable (2026-11-08)

### Hecho en esta iteración

- `inventario.py` implementa un primer recorrido recursivo de unidades locales fijas. Lee metadatos, no el contenido. No sigue reparse points, y registra errores y checkpoints en `%LOCALAPPDATA%\JardinZen\inventario.sqlite3`.
- `visor.py` expone estado y controles locales para inventario, propuestas y cerebro RAW/RAG.
- `visor.html` muestra avance, unidades, errores y exclusiones.
- El primer recorrido terminó en C:, D: y E:: 3,415,257 entradas, 495,330 carpetas, 303 errores de acceso, 203 enlaces/reparse points omitidos y 153 carpetas excluidas. Estado `complete_with_errors`; no equivale a cobertura perfecta.
- `proyectos.py` recatalogó 13 raíces Git, 61 módulos y 36 arbustos candidatos, a partir de 9,478 marcadores. El anterior 226 mezclaba manifiestos y repositorios. Carpetas de herramientas/paquetes se excluyen para reducir falsos candidatos.
- JZ-019 creó `brain.sqlite3` con extracción RAW, FTS5, chunks, embeddings Ollama y cursor durable. El primer job C:/D:/E: cuenta 2,918,993 archivos; el checkpoint registrado fue 23,218 inspeccionados, 181 documentos extraídos y 1,800 chunks vectorizados. El job sigue corriendo en segundo plano.
- `visor.html` ahora visualiza los árboles detectados agrupados por carpeta contenedora. La agrupación indica vecindad en el disco, no relación semántica. Tamaño = archivos del subárbol; ramas principales = carpetas inmediatas. El drag solo persiste coordenadas en el navegador.
- El inventario y el mapa son una línea base. No detectan todavía altas/cambios/eliminaciones en forma incremental, ni extraen enlaces, imports o dependencias.

### Principios inspirados en Obsidian

Obsidian guarda notas en Markdown local, conserva una caché de metadatos para funciones como Graph y Outline, y mantiene esa caché sincronizada con cambios de archivos ([almacenamiento y caché](https://obsidian.md/help/data-storage)). El Graph core representa notas como nodos y enlaces internos como aristas; permite vista local por profundidad, tamaño por referencias, filtros, movimiento, zoom y animación ([Graph](https://obsidian.md/help/plugins/graph)). Bases ofrece vistas sobre archivos y propiedades ([Bases](https://obsidian.md/help/bases)); Canvas guarda un espacio de tarjetas, grupos y relaciones en JSON Canvas abierto ([Canvas](https://obsidian.md/help/plugins/canvas)). Estas ideas sirven como referencias de interacción y formatos exportables, no implican que el Jardín deba convertir millones de archivos en notas Markdown individuales.

La documentación oficial de [plugins core](https://obsidian.md/help/plugins) describe enlaces, Graph, Bases y Canvas, pero no generación de embeddings/vector search como función central. En el catálogo comunitario hay complementos que construyen embeddings con proveedores concretos, algunos locales como Ollama ([ejemplo de Vector Search](https://community.obsidian.md/plugins/vector-search)); esa es una extensión optativa. Por tanto el análisis semántico debe tratarse como una capa explícita del Jardín, con modelo y almacenamiento local auditables.

### Próximos hitos

**JZ-018 activo:** [Visor de propuestas, trazabilidad y World Model](tickets/active/JZ-018-visor-trazabilidad-y-world-model.md). Northstar y ontología durables se describen en `NORTHSTAR.md` y `WORLD_MODEL.md`. Incidente del visor: HTML actualizado con proceso Python obsoleto que no cargó endpoints JZ-017; el lanzador debe validar `/api/proposals/status`.

**Estado semántico corregido:** JZ-019 ya extrae e indexa contenido con FTS + embeddings locales. La relación documento→árbol sigue siendo contención de ruta (hecho); no genera todavía clasificación semántica archivo→árbol/arbusto ni trasplantes. Eso sigue pendiente de modelado y evaluación con datos etiquetados.

**Nuevo ticket:** [JZ-017 — Tubería clasificadora contextual basada en el cerebro del Jardín](tickets/JZ-017-tuberia-clasificacion-contextual.md). Prioridad P0 para corregir la arquitectura que produjo clasificación genérica por muestra parcial. Introduce inventario por archivo, consulta del mapa/proyectos existentes, evidencia y relaciones locales, consenso por grupo, propuesta de nombres/rutas y revisión previa. La primera entrega es modo propuesta; no concede permiso para escribir en `[CLOUD_ROOT]` ni otras raíces externas.

**Estado:** F0 y F1 están ejecutadas; JZ-019 ejecuta RAW/RAG local en segundo plano. La siguiente fase es asignación contextual candidata con datos evaluables, luego F2 — grafo simbólico verificable. La vista es navegable y consultable, pero aún no un clasificador autónomo.

| Fase | Resultado | Estado / siguiente criterio |
|---|---|---|
| F0 — Inventario confiable | Barrido durable de metadatos, estados y cobertura. | **Ejecutada como línea base.** Quedan 303 rutas inaccesibles, 203 enlaces omitidos y 153 exclusiones registradas; falta reconciliación incremental. |
| F1 — Parcelas y árboles | Repositorios Git y candidatos por manifiestos, módulos y métricas de subárbol. | **Ejecutada.** 226 árboles; marcadores objetivos guardados como evidencia. Falta revisión humana para fusionar copias/worktrees o confirmar candidatos. |
| F2 — Estructura simbólica | Enlaces Markdown, imports/dependencias soportadas, referencias Git y jerarquía de carpetas. | **Siguiente.** Aristas tipadas por procedencia, dirección, fecha y confianza; similitud no se presenta como dependencia. |
| F3 — Catálogo / Bases | Vistas sobre propiedades sin convertir cada archivo en una nota: nombre, ruta, extensión, fechas, tamaño, hash/estado y descripción cuando exista evidencia. | Pendiente. Metadatos de origen conservan su procedencia; descripciones requieren extracción local de contenido. |
| F4 — Semántica local / RAG | Cola durable por archivo/proyecto; extracción aprobada, FTS, chunks y embeddings locales/Ollama; estados, hashes y versión de modelo. | Pendiente. Lotes retomables y contexto acotado por parcela; sugerencias semánticas requieren evidencia y nunca se guardan como aristas ciertas automáticamente. |
| F5 — Jardín espacial / Canvas | Oasis, árboles, ramas, hojas, raíces tipadas, frutos y casos especiales; zoom/pan/drag y vistas locales. | **Prototipo parcial:** árboles, parcelas contenedoras y drag visual. Falta Canvas persistente/interactivo, navegación de ramas/hojas y relaciones verificables. |
| F6 — Gobernanza | Bandeja de propuestas de poda/trasplante/renombrado con comparación previa y revisión humana. | Pendiente. Ninguna operación física se ejecuta por el mapa o IA sin previsualización, aprobación concreta, respaldo verificado y registro reversible. |

### Persistencia de análisis

No mantener una tarea de millones de elementos dentro de una conversación de IA. Guardar en SQLite: `jobs` (fase, lote, estado, cursor), `job_items` (ruta estable, hash/mtime, intentos, error), `evidence` (archivo y fragmento que respaldan cada conclusión), `entities` (volúmenes, proyectos, módulos), `edges` (origen/destino/tipo/confianza/procedencia/modelo) y `proposals` (cambios sugeridos y decisión). Cada trabajo tiene tamaño máximo, checkpoints, reintentos limitados y puede retomarse por lote; el prompt recibe solamente la parcela y su evidencia. Los datos y embeddings permanecen en local.

### Límites actuales del inventario

- La fecha de creación se obtiene de `st_birthtime` cuando Windows/Python la exponen; la fecha modificada es `st_mtime`. La resolución depende del sistema de archivos. El campo de propietario no equivale a quién creó el archivo y no se registra como tal.
- El primer mapa es un inventario de rutas accesibles; archivos protegidos o unidades desconectadas pueden producir errores. Las entradas cloud observadas antes de identificar G:/I: son un fragmento incompleto, no se contarán como cobertura de esas unidades.
- El inventario actual es una línea base. No actualiza aún eliminaciones ni cambios posteriores con una reconciliación incremental.
