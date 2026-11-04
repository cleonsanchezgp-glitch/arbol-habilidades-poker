qualitas:handoff 2026-11-04 qualitas

Anchor: Owner request for UI test data without relying on a local model.
Repo: cleonsanchezgp-glitch/arbol-habilidades-poker · master · C:\Users\Usuario\Documents\empresa\repositorios\arbol-habilidades-poker
Findings:
- Added `backend/demo_data.py`, an explicit deterministic seed containing two valid fictional DOCX files, six source-linked topics, six branches, prerequisites and one similarity-review candidate. Titles and documents are labelled `Muestra`; content explicitly says it is not Mentopoker material or poker advice. No local model is used.
- The seed was run in the ignored `.poker-roots-data` directory for direct Python access. It reported 2 documents, 6 topics and 6 branches. A second run returned `already_seeded` without duplicates. Docker Compose now seeds only an empty named volume on startup; an existing library is left untouched.
- Added tests for DOCX validity, source links, graph relations, similarity, idempotence and preserving an existing library with `--empty-only`. `python -m unittest discover -s tests -q` passed 38/38. `docker-compose config` resolved the seed command, local port and persistent volume.
- A temporary local API and Edge browser check at 390px displayed the six topics, a rendered source table and the 68% similarity candidate without page overflow. `npm run test:ui` passed after a clearer mobile tree-scroll hint. Temporary browser files and the local API were removed/stopped.
- Docker Desktop's Linux engine is still unavailable, so no container image build or container runtime check was possible.
Decisions:
- The demo is opt-in for direct Python runs, and automatic only for an empty Docker volume. It does not touch existing documents or topics in a nonempty library. The ignored local seed directory is not committed.
- TSK-008 and WP-003 remain deferred pending a real local model; no formal TMP execution results or GitHub planning states were changed.
Uncommitted:
- `backend/demo_data.py`, `tests/test_demo_data.py`, `compose.yaml`, `README.md`, mobile hint in `index.html` and `tests/ui_smoke.cjs`, this handoff and the refreshed documentation-status snapshot, in addition to earlier uncommitted UI, Docker and audit work.
Next: With Docker Desktop running, start `docker-compose up --build -d`; an empty volume will seed automatically. Open `http://127.0.0.1:8765/` and review the sample library. Continue UI improvements based on owner feedback.
Pending:
1. Docker engine availability for container build and runtime verification.
2. Owner review and commit of the verified local changes.
