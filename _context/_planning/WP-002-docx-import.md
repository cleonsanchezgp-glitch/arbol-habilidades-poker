## Title

| Field | Value |
| --- | --- |
| Document | DOCX extraction and import states |
| Work Package ID | WP-002 |
| Version | 0.1 |
| Status | Implemented; representative DOCX validation pending |
| Author | Rector |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Overview

Accept DOCX files, retain originals, extract ordered source material, and report progress and extraction gaps.

## 2. Belongs to Project

| Project (PRJ-xxx) |
| --- |
| PRJ-001 |

## 3. Realizes

| Requirement (FR-xxx / NFR-xxx) | Notes |
| --- | --- |
| FR-001 | Upload and processing states. |
| FR-002 | Ordered text, tables, and extractable images with omissions. |
| NFR-001 | Processing does not freeze navigation. |
| NFR-002 | Validate DOCX and reject unsupported input. |

## 4. Tasks

| ID | Task | Status | Owner |
| --- | --- | --- | --- |
| TSK-004 | Implement upload validation, file hash, original storage, and import status record. | Implemented | Project owner |
| TSK-005 | Extract paragraphs, tables, and available images in source order with fragment references. | Implemented; synthetic-DOCX check | Project owner |
| TSK-006 | Report extraction omissions and failure states; verify a multi-section DOCX and an invalid file. | Partial; representative multi-section DOCX pending | Project owner |

## 5. Status

| Field | Value |
| --- | --- |
| Overall status | Implemented for synthetic DOCX; representative-document validation pending |
| Start date | Not committed |
| Target completion | Not committed |

## References

- [Project](PRJ-001-local-mvp.md).
- [Import FRD](../_specification/FRDs/FRD-import-and-topics.md).
- [NFRD](../_specification/NFRD.md).
