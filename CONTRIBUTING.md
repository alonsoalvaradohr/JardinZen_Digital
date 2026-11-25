# Contributing to Jardín Zen Digital

Thank you for your interest in contributing to **Jardín Zen Digital: Local-First Knowledge Graph & BRÚJULA AI OS Harness**! We welcome contributions that uphold the principles of sovereign data ownership, local-first zero-telemetry operations, and deterministic validation.

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) (Contributor Covenant v2.1).

---

## Local Development & Environment Setup

Jardín Zen Digital is engineered in Python 3.10+ without heavy runtime frameworks, relying on built-in standard library capabilities and optional local embeddings.

### Prerequisites

- **Python**: 3.10 or higher (`python --version`)
- **Git**: 2.30 or higher

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alonsoalvaradohr/JardinZen_Digital.git
   cd JardinZen_Digital
   ```

2. **Environment Configuration (Zero Credentials Policy):**
   - Copy `config.example.json` to your local environment configuration:
     ```bash
     cp config.example.json config.json
     ```
   - Customize your local scan directories and model paths in `config.json`.
   - **CRITICAL**: Never commit `config.json`, SQLite databases (`*.sqlite3`, `*.db`), or private personal paths. The `.gitignore` strictly protects these assets.

3. **Validate Repository Hygiene:**
   Jardín Zen Digital enforces deterministic repository hygiene via `brujula_hygiene.py`. Run the validation suite:
   ```bash
   python brujula_hygiene.py --check
   ```
   All checks must output `estado=OK` (0 unclassified files, 0 broken links, 0 secrets, 0 syntax errors).

---

## Commit Guidelines (Conventional Commits)

We enforce semantic commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` Introduces a new feature or capability.
- `fix:` Patches a bug or regression.
- `docs:` Documentation modifications.
- `refactor:` Code refactoring without changing observable behavior.
- `test:` Adding, updating, or fixing tests.
- `chore:` Maintenance tasks, dependency updates, hygiene adjustments.

*Example:* `feat(brain): add deterministic query tokenization filter`

---

## Pull Request Process

1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Verify all Python files pass syntax checks:
   ```bash
   python -m py_compile brain.py jardinero.py inventario.py propuestas.py proyectos.py visor.py
   ```
3. Run the BRÚJULA hygiene validation check:
   ```bash
   python brujula_hygiene.py --check
   ```
4. Ensure SPDX headers remain in place:
   ```python
   # SPDX-License-Identifier: AGPL-3.0-or-later
   # Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>
   ```
5. Open a Pull Request referencing the issue or specification ticket.
