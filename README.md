# Poker Roots — Texas Hold'em study library

Local application in progress for organizing user-imported Texas Hold'em theory. The `poker-roots-boceto/` directory is the supplied visual prototype; it contains sample content, not imported theory. Project scope, architecture, and planned work are in `_context/`.

## Current executable foundation

WP-001 provides a durable SQLite store and a loopback HTTP API using Python's standard library. WP-002 adds DOCX validation and background extraction. WP-003 adds source-linked topic proposals through a locally configured Ollama-compatible text model. The application stores original document bytes, ordered source fragments, extractable images, topics, evidence links, strategic facets, branches, placements, and acyclic prerequisite relations. Data survives process restarts. Search and prototype integration remain planned.

Python 3.10 or newer is required. No package installation is needed for this foundation.

```powershell
$env:POKER_ROOTS_MODEL = "your-installed-local-model"
python -m backend.api --data-dir .poker-roots-data --port 8765
```

Open `http://127.0.0.1:8765/api/health` to check the server. The data directory defaults to `%LOCALAPPDATA%\PokerRoots` on Windows (or the user data directory on other systems) when `--data-dir` and `POKER_ROOTS_DATA_DIR` are not provided. Keep this directory to retain the library across restarts; back it up before replacing the machine or deleting user data.

Run a compatible model service on `http://127.0.0.1:11434`, or set `POKER_ROOTS_OLLAMA_URL` to another loopback HTTP address. Set `POKER_ROOTS_MODEL` to the name of a model actually installed there. The current environment has no reachable local model, so generation has been checked with a simulated model; quality on real theory remains unverified. Without configuration, DOCX extraction succeeds and the document waits in `awaiting_model`. After configuring the service and restarting, call its `/analyze` endpoint. Generated topics are marked `proposed` for manual review. Images are retained as source assets but are not interpreted by the text model.

### API foundation

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | API availability and schema version |
| GET, POST | `/api/documents` | List documents; import raw DOCX bytes with `X-Filename` header |
| GET | `/api/documents/{id}` | Document metadata and state |
| GET | `/api/documents/{id}/file` | Download retained original |
| GET | `/api/documents/{id}/fragments` | Read ordered source fragments |
| GET | `/api/documents/{id}/topics` | Read topics linked to this document |
| POST | `/api/documents/{id}/analyze` | Start topic analysis after extraction and model setup |
| GET | `/api/documents/{id}/images/{image_name}` | View an extracted image referenced by a fragment |
| POST | `/api/documents/{id}/retry` | Retry failed extraction or topic analysis |
| GET, POST | `/api/topics` | List or create structured topics |
| GET, PUT | `/api/topics/{id}` | Read or atomically edit topic fields, facets, placements, and prerequisites |
| GET | `/api/topics/{id}/locations` | Return every branch path where the topic appears |
| PUT | `/api/topics/{id}/facets` | Replace its strategic facets, using `null` for unknown |
| POST | `/api/topics/{id}/evidence` | Link a source fragment to a topic |
| GET, POST | `/api/branches` | Read or create navigation branches |
| GET | `/api/tree` | Read the current branches and topics in prerequisite order |
| POST, DELETE | `/api/topics/{id}/placements[/{branch_id}]` | Add or remove a branch placement |
| POST, DELETE | `/api/topics/{id}/prerequisites[/{prerequisite_id}]` | Add or remove a prerequisite; cycles are rejected |

The upload endpoint validates the DOCX package and responds `202 Accepted` with a document ID. Poll `/api/documents/{id}` until its state is `completed`, `awaiting_model`, or `failed`. `completed` means source-backed topic proposals were stored; `awaiting_model` means extraction succeeded but model configuration is missing. Exact duplicate bytes return the earlier document instead of creating another copy. Extraction preserves paragraphs and tables in body order and saves supported inline images. It reports omitted headers, footnotes, image text, complex layouts, and unsupported blocks as warnings where detected. The original DOCX remains available for inspection. Model proposals carry per-claim fragment links, unknowns, contradiction reports, example origin, and prerequisite suggestions. Exact duplicates are blocked by document hash; similar existing topics are flagged for review. These checks do not establish semantic fidelity of a real model output. JSON endpoints accept `Content-Type: application/json`. A topic `PUT` can include `facets` as a name-to-text-or-null map and `placements` and `prerequisites` as complete lists of IDs; all supplied changes commit together or none do. `/api/tree` is read from the saved graph after each edit, and `/api/topics/{id}/locations` gives each root-to-branch path for navigation. The server binds to `127.0.0.1` by default; exposing it on another interface would require an access-control design.

## Checks

```powershell
python -m unittest discover -s tests -v
```

The tests use disposable data directories, synthetic DOCX packages, and a simulated local model. They check extraction order, image access, invalid-file rejection, persistence after reopening the store, duplicate document hashes, atomic fragment writes, source-linked multi-topic proposals, numeric-detail rejection, cycle rejection, and API error handling.
