# Guía rápida: desplegar y abrir el visor Jardín

## Arranque normal

1. El visor necesita que ya existan `%LOCALAPPDATA%\JardinZen\runtime.json` y `index.sqlite3`. No ejecutes `INICIAR.cmd` solo para abrir el visor: la instalación también puede lanzar un lote que mueve archivos.
2. Abre `ABRIR_JARDIN.cmd` desde `[JARDINZEN_ROOT]`.
3. El lanzador inicia el visor en segundo plano y abre `http://127.0.0.1:8765` en el navegador.
4. Déjalo abierto mientras quieras consultar el jardín. Se actualiza automáticamente cada 15 segundos.
5. Para cerrarlo, ejecuta `DETENER_JARDIN.cmd`.

El visor lee `runtime.json`, `STATE.json`, las dos carpetas `00_MACETA` y `index.sqlite3` (esta última en modo SQLite de solo lectura). Desde **Primer mapa del disco** permite iniciar, pausar, reanudar o detener el inventario de metadatos; sus datos y checkpoints van a `%LOCALAPPDATA%\JardinZen\inventario.sqlite3`, separado del índice principal. Con el mapa completo, **Descubrir árboles** procesa los marcadores locales y presenta árboles, parcelas y módulos. El detector no abre contenidos ni mueve o renombra archivos. El visor no arranca lotes de organización ni cambia la tarea programada. Solo escucha en `127.0.0.1` (esta computadora); no está publicado para la red local ni Internet.

La dirección estable es `http://127.0.0.1:8765`. No se ha configurado `jardin.local`: ese nombre exige instalar resolución DNS o modificar el archivo `hosts` de Windows. Para mantener un arranque sin permisos de administrador, se usa el loopback local.

## Diagnóstico

- Si falta el índice o `runtime.json`, el visor no puede representar el jardín instalado. Inspecciona el despliegue antes de ejecutar `INICIAR.cmd`, porque puede iniciar el clasificador y mover elementos de las macetas.
- Si el puerto 8765 está ocupado, cierra el proceso que lo usa o cambia `JARDINERO_VIEWER_PORT` antes de arrancar el script.
- Si Ollama aparece sin conexión, el visor sigue mostrando el índice y movimientos existentes; la clasificación local requiere que Ollama esté activo.
- Si la aplicación falla, ejecuta `python visor.py` en una terminal para ver el error y detenerla con `Ctrl+C`.

## Prompt de despliegue/arranque para retomar el trabajo con un asistente

> Despliega y abre el visor local de Jardinero en `[JARDINZEN_ROOT]`. Lee `AGENTS.md` y esta guía; abre `ABRIR_JARDIN.cmd` en `http://127.0.0.1:8765`. No ejecutes `INICIAR.cmd` ni `EJECUTAR.cmd` para abrir el visor. El índice principal `index.sqlite3` permanece en solo lectura. El inventario y el mapa de árboles viven en la base independiente `inventario.sqlite3` y solo usan metadatos locales. Montajes cloud identificados por etiqueta se excluyen del barrido. Comprueba estado y cobertura desde `/api/inventory/status`; consulta `/api/overview` para el estado del jardín y `/api/garden/project?path=<ruta>` para el detalle de un árbol. Las aristas semánticas, el catálogo tipo Bases, extracción de contenido, RAG y embeddings por inventario aún no existen: son fases posteriores con persistencia y evidencia, no inventes que ya están desplegadas. No arranques el clasificador, no muevas archivos, no toques respaldos ni la tarea programada.
