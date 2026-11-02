## Title

| Field | Value |
| --- | --- |
| Document | Topic processing and provenance |
| Work Package ID | WP-003 |
| Version | 0.1 |
| Status | Code complete; real-model validation pending |
| Author | Rector |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Overview

Use locally executed AI to propose source-linked Texas Hold'em topics, preserve strategic conditions, and surface duplication or evidence gaps for review.

## 2. Belongs to Project

| Project (PRJ-xxx) |
| --- |
| PRJ-001 |

## 3. Realizes

| Requirement (FR-xxx / NFR-xxx) | Notes |
| --- | --- |
| FR-003 | Produce one or more structured topics per document. |
| FR-004 | Preserve conditions, unknowns, contradictions, and generated-example labels. |
| FR-005 | Detect exact imports and flag similar topics. |
| NFR-007 | Keep document and model processing local. |

## 4. Tasks

| ID | Task | Status | Owner |
| --- | --- | --- | --- |
| TSK-007 | Implement local-model topic proposal with structured fields and source-fragment references. | Implemented; simulated-model check | Project owner |
| TSK-008 | Validate evidence links, unknown qualifiers, generated examples, and conflicting statements. | Structural validation implemented; semantic review pending | Project owner |
| TSK-009 | Detect exact document hashes and similar existing topics; present review candidates. | Implemented in API; UI pending | Project owner |

## 5. Status

| Field | Value |
| --- | --- |
| Overall status | Code complete; validation with a real local model and representative DOCX pending |
| Start date | Not committed |
| Target completion | Not committed |

## References

- [Project](PRJ-001-local-mvp.md).
- [Import FRD](../_specification/FRDs/FRD-import-and-topics.md).
- [Architecture](../_design/ADD.md).
