## Title

| Field | Value |
| --- | --- |
| Document | Local storage and API foundation |
| Work Package ID | WP-001 |
| Version | 0.1 |
| Status | Implemented |
| Author | Rector |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Overview

Establish the local application shell, durable records, source-file storage, and API boundaries required by every later package.

## 2. Belongs to Project

| Project (PRJ-xxx) |
| --- |
| PRJ-001 |

## 3. Realizes

| Requirement (FR-xxx / NFR-xxx) | Notes |
| --- | --- |
| FR-006 | Persist original documents, fragments, topics, and relations. |
| NFR-005 | Verify data survives restart. |
| NFR-006 | Keep prior records intact when a later operation fails. |
| NFR-008 | Separate extraction, storage, retrieval, and model adapters. |

## 4. Tasks

| ID | Task | Status | Owner |
| --- | --- | --- | --- |
| TSK-001 | Define local data directory, database schema, source-file layout, and migrations. | Implemented | Project owner |
| TSK-002 | Implement document, fragment, topic, evidence, facet, and relation storage with transactional writes. | Implemented | Project owner |
| TSK-003 | Establish local API boundaries and verify a saved record survives restart and a failed write. | Implemented; automated checks | Project owner |

## 5. Status

| Field | Value |
| --- | --- |
| Overall status | Implemented; tests pass |
| Start date | Not committed |
| Target completion | Not committed |

## References

- [Project](PRJ-001-local-mvp.md).
- [Architecture](../_design/ADD.md).
- [Import FRD](../_specification/FRDs/FRD-import-and-topics.md).
- [NFRD](../_specification/NFRD.md).
