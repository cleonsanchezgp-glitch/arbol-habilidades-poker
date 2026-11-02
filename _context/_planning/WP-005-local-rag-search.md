## Title

| Field | Value |
| --- | --- |
| Document | Local retrieval, answers, and study paths |
| Work Package ID | WP-005 |
| Version | 0.1 |
| Status | Planned |
| Author | Rector |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Overview

Search imported evidence with lexical and local semantic retrieval; answer using source-linked context and recommend prerequisite-ordered paths.

## 2. Belongs to Project

| Project (PRJ-xxx) |
| --- |
| PRJ-001 |

## 3. Realizes

| Requirement (FR-xxx / NFR-xxx) | Notes |
| --- | --- |
| FR-011 | Interpret informal queries and retrieve relevant topics and fragments. |
| FR-012 | Answer with source links and preserved conditions. |
| FR-013 | Clarify material ambiguity and disclose insufficient coverage. |
| FR-014 | Recommend available topics in prerequisite order. |
| FR-015 | Use distinct local inference and retrieval components. |
| NFR-001 | Search processing remains visible and does not freeze navigation. |
| NFR-007 | Local model calls do not require remote AI. |
| NFR-008 | Retrieval and inference failures are distinguishable. |

## 4. Tasks

| ID | Task | Status | Owner |
| --- | --- | --- | --- |
| TSK-013 | Build lexical index and local embeddings with source-fragment identifiers. | Planned | Project owner |
| TSK-014 | Implement query interpretation, retrieval ranking, grounded answers, and ambiguity/coverage checks. | Planned | Project owner |
| TSK-015 | Implement prerequisite-ordered study recommendations and verify source links and no-evidence behavior. | Planned | Project owner |

## 5. Status

| Field | Value |
| --- | --- |
| Overall status | Planned |
| Start date | Not committed |
| Target completion | Not committed |

## References

- [Project](PRJ-001-local-mvp.md).
- [Search FRD](../_specification/FRDs/FRD-search-and-study-path.md).
- [Architecture](../_design/ADD.md).
