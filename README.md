# Jardín Zen Digital — Instalación de una línea (Windows 11)

Extraer ZIP en cualquier carpeta estable. En **CMD / PowerShell**, dentro de esa carpeta:

```cmd
.\INICIAR.cmd
```

Sin edición previa de archivos. Windows con `winget` e Internet cuando falte Python/Ollama/modelos. Dependencias: Python >=3.10, Ollama nativo y modelos de 2–3 GB aproximadamente en conjunto. Python/Ollama se instalan automáticamente *si winget está disponible y permite la instalación*. Una instalación fallida detiene los movimientos.

## Efecto REAL del comando

1. **F0** Resuelve desde Windows las rutas efectivas de Descargas y Escritorio (incluidas rutas redirigidas), crea `00_MACETA` bajo ambas, crea `%USERPROFILE%\JardinZen`, genera `%LOCALAPPDATA%\JardinZen\runtime.json`, `index.sqlite3`, checkpoints y carpeta privada de respaldos.
2. **F1** Descarga modelos locales Ollama si faltan. En la primera ejecución procesa un lote de hasta 30 elementos *directos* de macetas cuando lleven ≥20 segundos sin modificarse. Clasifica localmente, mueve físicamente, verifica SHA256 e indexa texto y embeddings disponibles. Archivos ambiguos/quebrados/secretos permanecen en origen.
3. **F3** Registra la tarea `JardinZen_Jardinero` en el Programador de tareas cada 15 minutos (usuario actual). No necesita ejecutar un proceso residente constantemente.
4. **F2** *No* comienza migración de Escritorio/Descargas completos, repositorios o discos: todavía no hay autorización explícita de esas raíces. La primera fase automática trabaja sólo con contenido puesto voluntariamente en las macetas.
5. **F4** Banco de 50 preguntas pendiente: RAG léxico y vectorial ya funciona para texto extraíble indexado; no se atribuye Recall@5 sin datos.

## Operación

- Consultar `STATE.md` real en `%LOCALAPPDATA%\JardinZen\STATE.md`.
- Detener nuevos lotes: `DETENER.cmd` (crea `STOP`). La operación en curso termina antes de detenerse.
- Reanudar: `REANUDAR.cmd`.
- Búsqueda: `BUSCAR.cmd "consulta"` (requiere Python Launcher `py`; alternativamente llamar a `jardinero.py search ...`).
- Preguntas RAG (texto local recuperado + modelo local): `PREGUNTAR.cmd "pregunta"`. Los modelos no conocen documentos que no pudieron extraerse.
- Ejecución inmediata de otro lote: `EJECUTAR.cmd`.
- Para restaurar una operación concreta, usar `jardinero.py undo --operation <ID> ...`. **Restaura el origen pero conserva el destino** para que nada sea borrado sin revisión.
- Respaldos por operación: `%LOCALAPPDATA%\JardinZen\backups\<id>`. **No** mover ni borrar manualmente durante operaciones. Política de retención no automática.

## Política de seguridad / límites intencionales

- Sin red externa para procesar contenido; Ollama debe estar en localhost. **Solo el instalador/descarga inicial de modelos usa Internet**.
- No hay modificaciones en directorios de usuario fuera de las macetas aprobadas, nueva raíz propia y estado local de la aplicación. La tarea Windows es el único cambio de sistema operativo.
- Sin accesos directos. Jerarquía física: `Dominio/Proyecto/AAAAMMDD/NombreOriginal/descripcion.ext`. Directorios se trasladan completos y conservan sus nombres internos. No sigue symlinks/junctions; rechaza conjuntos con `.git` o secretos hasta revisión humana.
- Límite predeterminado: 1.5 GB por elemento y respaldo; si no hay espacio se bloquea el movimiento.
- No garantiza clasificar bien contenido no extraíble, PDFs escaneados, imágenes o ensambles CAD: esos elementos deben quedar en revisión según la confianza del modelo. Los PDF textuales se leen si `pypdf` está instalado; se puede instalar con `py -m pip install pypdf` opcionalmente.
- Prohibido inferir que todo el sistema quedó ordenado solo porque un lote haya pasado. Ningún archivo original entregado ha sido movido por la generación de este ZIP.

## Desinstalación

1. `schtasks /Delete /TN JardinZen_Jardinero /F` para desregistrar la tarea.
2. Conservar **JardinZen y backups** si no se ha reconciliado cada operación.
3. Quitar carpeta del programa sólo después de detener la tarea. Python y Ollama se desinstalan por separado si ya no son utilizados.

## Primer mapa visual del disco

El visor incluye **Primer mapa del disco**. Inicia el barrido desde esa tarjeta: registra metadatos en `%LOCALAPPDATA%\JardinZen\inventario.sqlite3` y muestra el avance, errores, carpetas excluidas y enlaces omitidos. Incluye unidades locales fijas con letra; reconoce montajes cloud por la etiqueta del volumen y los omite. El proceso se puede pausar, detener y reanudar; el punto de avance queda en SQLite. Al reiniciar el visor, usa **Reanudar mapa** si el recorrido no terminó.

Este barrido no abre contenidos ni cambia archivos. Guarda ruta, nombre, tipo, extensión, tamaño, fecha de creación informada por Windows, modificación y atributos. Los errores de acceso quedan anotados. No sigue enlaces/junctions; no incluye unidades virtuales o de nube ni volúmenes sin letra. Windows no mantiene un campo confiable de "quién creó" para todos los archivos; el propietario actual no se presenta como creador.

El mapa es la base para descubrir después repositorios, estructuras de proyecto y vínculos simbólicos. El análisis semántico/embeddings es una fase posterior y no se ejecuta dentro del barrido para que millones de entradas no dependan del contexto conversacional del modelo.

## Árboles del jardín

La fase siguiente ya está desplegada en el visor. Pulsa **Descubrir árboles** para identificar repositorios por `.git`, reconocer candidatos por manifiestos de proyecto y formar ramas de módulos. La detección trabaja solo con el índice de metadatos y deja evidencia de los marcadores; no abre archivos. La última ejecución encontró 226 árboles (45 con Git, 181 candidatos por manifiesto) y 606 módulos sobre 9,481 marcadores.

Los proyectos se agrupan en parcelas por carpeta contenedora. Esa vecindad describe dónde viven en el disco; no declara que tengan una dependencia. El tamaño del árbol refleja los archivos del subárbol y sus ramas principales las carpetas inmediatas. Los manifiestos son señales, no confirmación humana: copias, worktrees y archivos fuente históricos pueden aparecer como proyectos separados.

La búsqueda existente del índice principal es léxica/vectorial sobre los documentos que Jardinero ya procesó; no representa aún los millones de elementos del inventario. Esta fase no genera notas Markdown ni embeddings por cada archivo. El próximo paso es extraer relaciones simbólicas con procedencia verificable, después ofrecer vistas tipo Bases y, por separado, una cola de extracción/RAG local reanudable.

## Visor visual local

Abre `ABRIR_JARDIN.cmd` para iniciar el visor y abrir `http://127.0.0.1:8765`. El lanzador comprueba `/api/health`; si la página visible es más nueva que el proceso Python activo, reinicia únicamente el servidor Jardinero cuya línea de comandos apunta al `visor.py` de esta carpeta. Si otro programa ocupa el puerto, se detiene sin matar ese proceso. El panel de propuestas informa progreso y errores HTTP.

La arboleda muestra árboles candidatos desde el mapa de metadatos; las macetas reflejan el contenido actual de `00_MACETA`. El panel de inventario controla el barrido metadata-only y el de proyectos vuelve a ejecutar la detección por marcadores. Northstar: `NORTHSTAR.md`; entidades, capas de índice y tipos de evidencia: `WORLD_MODEL.md`.

**Alcance semántico actual:** el mapa completo contiene metadatos, y el descubrimiento identifica candidatos estructurales. `index.sqlite3` contiene texto/FTS/embeddings solo de documentos procesados por F1. JZ-017 compara tokens de nombres contra el catálogo; no indexa contenido ni resuelve ramas temáticas como `evidence/thermal-test`. Ningún botón de propuestas trasplanta archivos.

Para cerrar el servidor local, ejecuta `DETENER_JARDIN.cmd`. Solo escucha en `127.0.0.1`. El índice principal `index.sqlite3` se abre en modo de solo lectura; el nuevo inventario se guarda aparte en `inventario.sqlite3` cuando se inicia desde la interfaz. No inicia el clasificador, no mueve archivos ni modifica la tarea de Jardinero. Guía de uso y prompt para retomarlo: `PROMPT_DESPLIEGUE_VISOR.md`.

## JZ-017 · Tubería contextual en modo propuesta

El panel **Tubería contextual** trabaja solo con filas que ya existen en `%LOCALAPPDATA%\JardinZen\inventario.sqlite3` y cuyas rutas estén bajo las dos macetas de `runtime.json`. No inicia un escaneo, no abre archivos y procesa hasta 30 registros por lote. La cola durable queda en `propuestas.sqlite3`; al cerrar el visor se puede continuar con **Procesar siguiente lote**. La API local expone `/api/proposals/status`, `/api/proposals/start` y `/api/proposals/next`.

Cada fila conserva metadatos observados, origen de la evidencia y una coincidencia léxica de nombre contra proyectos ya descubiertos. Esta coincidencia es solo candidata y no equivale a validar el proyecto. Las rutas de proyecto aparecen como destinos candidatos bloqueados; no existe aprobación ni endpoint de ejecución. El nombre propuesto conserva el nombre actual para evitar renombres inferidos sin extracción.

Esta entrega no extrae texto, no calcula hash, no genera chunks/FTS/embeddings, no clasifica carpetas como conjunto, no detecta desacuerdos entre los archivos de una agrupación y no produce notas Markdown. Tampoco implementa decisiones humanas ni los criterios de evaluación etiquetados. Los datos térmicos mencionados en JZ-017 no se consideran confirmados por esta implementación y la ruta de Labot no queda autorizada. Para obtener candidatos se requiere que el mapa metadata-only y el descubrimiento de árboles ya se hayan ejecutado anteriormente por separado.
