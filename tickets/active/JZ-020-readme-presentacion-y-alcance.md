# JZ-020 — README de producto, operación y límites

## Propósito

Reemplazar la portada superficial y contradictoria por una guía clara para la primera visita: qué resuelve Jardinero, qué está implementado, cómo se ejecuta cada modo, dónde se guardan datos, cuáles son sus garantías y qué falta.

## Alcance

- Mejorar `README.md` para GitHub con resumen visual, arquitectura, inicio rápido, privacidad, operaciones, límites y enlaces a Northstar/World Model/invariantes/roadmap.
- Corregir contradicciones de estado visibles en `WORLD_MODEL.md` y `ROADMAP.md`.
- Mantener el repositorio privado y no incluir bases, contenido RAW ni datos locales.
- No modificar código del producto ni cambiar el estado de ejecución del job RAW/RAG.

## Criterios de aceptación

- [x] Un visitante distingue el organizador de macetas del mapa/RAG del equipo.
- [x] Se informa que `INICIAR.cmd` ejecuta un lote que puede mover archivos.
- [x] El README describe con precisión los estados, límites, dependencias y controles.
- [x] Mermaid, tablas y jerarquía visual hacen legible la arquitectura en GitHub.
- [x] Northstar, ontología, invariantes, roadmap y auditoría se encuentran desde la portada.
- [x] Las capas y hitos enlazados ya no señalan `index.sqlite3` como RAW/RAG ni afirman 226 árboles.
- [x] Commit local y push a `main` verificados.

## Enfoque de investigación

Se siguieron las recomendaciones oficiales de GitHub: explicar utilidad, motivación, primeros pasos, ayuda y mantenimiento; y se contrastó con README de aplicaciones maduras que exponen capacidades, instalación, documentación, seguridad y licencia. La portada distingue lo disponible de lo planeado y utiliza un diagrama de arquitectura en vez de prometer capacidades vagas.

## Resultado

README reorganizado como guía de producto y operación; World Model y Roadmap sincronizados con JZ-019. Ver [manifiesto SHA-256](../../audits/JZ-020-SHA256.txt). El repositorio sigue privado. El índice personal y el progreso de la ingesta no se publican.
