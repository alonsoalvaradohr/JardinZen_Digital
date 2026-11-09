# World Model — Ontología y evidencia del Jardín

Este documento es el contrato conceptual entre inventario, cerebro local, clasificador y visor. SQLite conserva el estado operacional; Markdown ofrece una superficie navegable estilo Obsidian. Ninguna vista debe convertir inferencias en hechos.

## Entidades del jardín

| Entidad | Significado | Evidencia primaria |
|---|---|---|
| Jardín | Espacio conceptual local y catálogo de todas las raíces observadas | Configuración local y mapa de volúmenes |
| Parcela / oasis | Raíz organizacional o espacio de trabajo con identidad conocida | Ruta canónica confirmada, volumen y catálogo de proyectos |
| Árbol | Repositorio Git o proyecto confirmado como unidad coherente | Raíz Git, worktree, manifiestos y revisión/confirmación humana |
| Arbusto | Colección temática o grupo documental que no es un repositorio autónomo | Conjunto de archivos, contexto de carpeta y evidencia concordante |
| Rama | Módulo, subsistema o subcarpeta con rol explícito | Manifiesto, import, referencia documentada o jerarquía observada |
| Hoja | Archivo individual | Ruta y metadatos; contenido solo si un extractor local lo procesa |
| Raíz / conexión | Relación tipada entre entidades | Enlace explícito, import, pertenencia estructural, referencia Git o sugerencia semántica marcada |
| Fruto / flor / hongo | Artefacto producido, resultado, documento especial o elemento sin proyecto | Tipo de artefacto y procedencia; nunca clasificación decorativa arbitraria |

La metáfora no impone un único árbol a cada archivo. Un archivo puede tener una pertenencia primaria y varias relaciones tipadas. Las copias/worktrees conservan identidades propias hasta reconciliación.

## Capas de conocimiento

1. **Mapa de metadatos (`inventario.sqlite3`):** ruta, padre, nombre, formato, tamaño, fechas del sistema, atributos y estado de recorrido. No lee el contenido.
2. **Catálogo estructural (`projects`, `project_modules`):** candidatos de árboles/módulos obtenidos de marcadores como `.git` y manifiestos. Los marcadores son evidencia, no confirmación universal.
3. **Índice textual/vectorial (`index.sqlite3`):** texto extraído localmente, chunks, FTS y embeddings para los documentos procesados. Hoy solo incluye elementos ya ingeridos en Jardinero; no equivale al mapa completo.
4. **World Model:** entidades y aristas con clase de evidencia, fuente, fecha, versión de parser/modelo y estado (observado, derivado, candidato, confirmado, rechazado, desconocido).
5. **Brain Markdown:** notas por jardín/parcela/árbol/arbusto con propiedades estables y enlaces a evidencia. Los millones de hojas y estados permanecen en SQLite; no duplicar cada registro como archivo Markdown por defecto.
6. **Propuestas/gobernanza:** destino y nombre candidatos, alternativas, razones, evidencia, riesgos, decisión humana y eventual operación transaccional. Proponer no muta archivos.

## Tipos de arista

- `contains`: contención de ruta observada.
- `project_root_of`: raíz de proyecto respaldada por marcador/confirmación.
- `module_of`: módulo respaldado por manifiesto/dependencia.
- `links_to` / `imports`: referencia literal analizada por parser local.
- `same_content_as`: igualdad de hash, calculada explícitamente.
- `lexical_candidate` / `semantic_candidate`: similitud recuperada; siempre tentativa.
- `human_confirmed`: decisión de Alonso con fecha y alcance.

Cada arista guarda fuente, evidencia, fecha, regla/modelo y nivel de certeza. Similitud nunca se dibuja como conexión confirmada.

## Clasificación jerárquica

Primero se identifica la parcela y el proyecto conocido, luego rama/colección, finalmente nombre descriptivo del archivo. Ruta confirmada, raíz Git/manifiestos y referencias explícitas preceden a búsqueda FTS/vectorial; el LLM local resume o propone solo después de recibir evidencia acotada. Señales fuertes en conflicto, datos no extraíbles o raíz no autorizada terminan en `REVIEW`.

## Estado verificable a 2026-11-09

- `inventario.sqlite3` contiene el barrido metadata-only de 3,415,257 entradas en C:, D: y E:, con rutas inaccesibles/exclusiones registradas.
- `proyectos.py` detectó 226 árboles candidatos (45 Git, 181 por manifiestos) y 606 módulos desde 9,481 marcadores, sin leer contenido.
- `index.sqlite3` contiene el índice FTS/vectorial de documentos ingeridos por el flujo anterior, no de cada entrada del inventario.
- JZ-017 añadió propuestas metadata-only por archivo con coincidencia léxica de nombre y destino candidato bloqueado. No implementa extracción semántica ni la ruta `thermal-test`.
- `[CLOUD_ROOT]\...` es raíz cloud/virtual fuera de escritura autorizada y no se trasplanta por inferencia.
