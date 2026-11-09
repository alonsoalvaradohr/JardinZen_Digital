# Auditoría de ejecución — JZ-017

- Fecha: 2026-11-09
- Chat ejecutor: 00000000-0000-0000-0000-000000000000 (Codex local)
- Ticket: tickets/JZ-017-tuberia-clasificacion-contextual.md
- Commit Git: no existe. El directorio fuente no contiene .git; git rev-parse --show-toplevel falla. No se inicializó un repositorio ni se fabricó un commit sin baseline.
- Trazabilidad alternativa: manifiesto SHA-256 audits/JZ-017-SHA256.json, con checksum en audits/JZ-017-SHA256.sha256.

## Dictamen

La entrega del chat es una iteración parcial de modo propuesta, no la implementación completa de JZ-017. El código realiza emparejamiento léxico de nombres usando metadatos ya existentes. No implementa extracción ni clasificación semántica del contenido, RAG/embeddings de las macetas, Markdown del brain, consenso por carpeta, explicación basada en fragmentos, revisión humana ni los criterios integrales del ticket. Por tanto, no se puede concluir que determine correctamente el proyecto ni el destino; en particular no resuelve el ejemplo Labot / 30-quality-validation/evidence/thermal-test.

## Lo que sí quedó implementado y verificado

- Cola durable en propuestas.sqlite3, API local del visor y panel de propuestas.
- Consume filas de archivos ya presentes en inventario.sqlite3, limitadas al prefijo de las dos macetas de runtime.json; no inicia barrido ni abre contenido.
- Las coincidencias de nombre contra proyectos descubiertos se marcan como candidatas; las propuestas con proyecto quedan bloqueadas. No hay ruta API de aprobación ni llamada a movimiento/renombrado en este flujo.
- Conserva ruta/nombre/extensión/tamaño/fecha de metadatos y procedencia de la señal léxica.
- En esta auditoría se corrigió la ordenación del cursor para que use casefold igual que el filtro, evitando saltos/repeticiones con rutas de mayúsculas mixtas.

## Verificación realizada

- python -m py_compile propuestas.py visor.py: correcto.
- Prueba aislada con SQLite temporal y 75 rutas de fixture: lote terminó complete, 75/75 propuestas únicas; cero estados ejecutables/mutadores; los datos temporales se limpiaron.
- No se escanearon las macetas ni el inventario real; no se movió ni renombró ningún archivo; no se escribió en Labot/Drive.
- No se ejecutaron las pruebas existentes del proyecto porque tests/test_real_files.py es una suite sobre archivos reales y no hay aquí un harness de fixtures seguro. La verificación fue exclusivamente temporal y sintética.

## Hallazgos y trabajo pendiente

1. No clasifica semánticamente: _match() compara tokens del nombre del archivo con el nombre del proyecto; un match no valida pertenencia.
2. No propone subcarpeta contextual: el destino candidato se compone como project_path / filename; no deduce evidence/thermal-test.
3. Falta hash de los archivos de entrada en la cola y no se comprueba que rutas/metadatos sigan vigentes antes de mostrar la propuesta.
4. No procesa carpetas como grupos ni detecta consenso/conflictos entre sus miembros.
5. No genera notas Markdown ni embeddings/FTS desde contenido.
6. No existe decisión humana persistente, corpus etiquetado ni medición de precisión/abstención.
7. Ticket conserva alcance parcial y no habilita operaciones físicas. La ruta [CLOUD_ROOT]\... continúa sin autorización de escritura.

## Archivos de la entrega auditada

SHA-256 calculado sobre los bytes actuales de estos archivos. El manifiesto incluye también el hash de este informe.

| Archivo | SHA-256 |
|---|---|
| propuestas.py | 6868a1ce6b2bfffd1d5aca96e7343fc9121660cf5c5f8ba918ba878245455ae5 |
| visor.py | 600f194479272f5850c9eb8b98425502ed2ef008e0ec7774a015d01db80ec6c8 |
| visor.html | 629cf4bc5d5ce1660e187f3eb326ca5fe18d92d511b8f875e8bffbafb06ca6e6 |
| README.md | cb127cf67c5a2386c73963d8b30f5bd629f5161b21da10446718fddeed2ee647 |
| tickets/JZ-017-tuberia-clasificacion-contextual.md | f0089a313d0c3bb1502ee3646d02278fe9811868f92023e9b78bb67260d6b5ac |

