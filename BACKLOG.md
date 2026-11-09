# BACKLOG — Sólo elementos no críticos para el primer jardín

- [x] **JZ-018 / P0 — Visor y World Model:** corregir el servicio obsoleto, validar controles, establecer Northstar/World Model y dejar commits/trazabilidad. [Ticket](tickets/active/JZ-018-visor-trazabilidad-y-world-model.md) · [Auditoría](audits/JZ-018-AUDITORIA.md).
- [x] **JZ-019 / P0 — Cerebro RAW/RAG local y ontología:** implementación y job reanudable activos; 13 árboles canónicos, 61 módulos y 36 arbustos de revisión. La ingesta total sigue en segundo plano; no asigna semánticamente ni trasplanta archivos. [Ticket](tickets/active/JZ-019-brain-local-raw-rag.md) · [Auditoría](audits/JZ-019-AUDITORIA.md).
- [ ] **JZ-017 / P0 — Clasificación semántica por ontología:** continuar extracción local por archivo, vinculación con árboles/arbustos/parcelas y evidencias. La entrega actual solo compara tokens de nombres contra proyectos y bloquea destinos; no cumple el objetivo de clasificación semántica. [Ticket](tickets/JZ-017-tuberia-clasificacion-contextual.md).

- [ ] **JZ-017 / F7 — Tubería clasificadora contextual:** inventario por archivo, cerebro Markdown + SQLite/FTS/vectores, vinculación jerárquica con árboles/proyectos conocidos, propuestas explicables y revisión en visor. Modo propuesta solamente; el ticket no autoriza raíces nuevas ni trasplantes. [Especificación](tickets/JZ-017-tuberia-clasificacion-contextual.md).

- [ ] F2: inventario/migración multi-TB con snapshot por conjunto, topología real de unidades y ACL por raíz.
- [ ] Extraer más contenido no textual (PDF escaneado/OCR, imágenes, CAD específicos); clasificaciones ambiguas permanecen intactas.
- [ ] F4: benchmarking `Recall@5` con 50 consultas acordadas y control de calidad de clasificación.
- [ ] Integración nube (OneDrive/Drive) con políticas de archivos virtuales y autorización separada.
- [ ] Re-evaluación ontológica y ajustes reversibles de colecciones ya migradas.
- [ ] Cifrado del índice en unidades sin BitLocker; controles de acceso avanzados y backup 3-2-1 global multi-TB.
