## Title

| Field | Value |
| --- | --- |
| Document | Local first functional version |
| Project ID | PRJ-001 |
| Version | 0.1 |
| Status | Draft - planned |
| Author | Rector |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Overview

Build and validate a local, single-user application that imports DOCX theory, preserves sources, presents a correctable learning tree, and answers informal questions using local retrieval and model inference. The owner has approximately 12 hours per week and no calendar deadline. Work packages below are ordered by technical dependency; their calendar timing remains open.

## 2. Belongs to Initiative

| Initiative (INI-xxx) |
| --- |
| INI-001 |

## 3. Target Milestone

| Milestone (MS-xxx) | Horizon |
| --- | --- |
| MS-001 | H-001 — first functional version, undated |

## 4. Scope

### In Scope

- Durable local data and source files.
- DOCX extraction with visible omissions, topic generation, source links, and duplicate review.
- Editable strategic classification, prerequisites, and descending tree.
- Source-grounded natural-language search and a basic study sequence using a local model.
- Integration of the Poker Roots visual prototype with real data, processing states, and error states.
- Checks for import, provenance, cycle prevention, persistence after restart, and grounded answers.

### Out of Scope

- Solver calculations, cloud AI, multi-user synchronization, remote deployment, and a separate test infrastructure initiative.
- A fixed release date until work is sized against the owner's 12 hours per week.

## 5. Work Packages

| ID (WP-xxx) | Work Package | Status |
| --- | --- | --- |
| WP-001 | Local storage and API foundation | Implemented |
| WP-002 | DOCX extraction and import states | Implemented |
| WP-003 | Topic processing and provenance | Code complete; real-model validation pending |
| WP-004 | Learning graph and editing | Planned |
| WP-005 | Local retrieval, answers, and study paths | Planned |
| WP-006 | Poker Roots integration and first-version validation | Planned |

## 6. Status

| Field | Value |
| --- | --- |
| Overall status | In progress; local storage, extraction, and model-backed topic proposal code present |
| Start date | Not committed |
| Target completion | Not committed |

## References

- [Initiative](INI-001-texas-holdem-learning-library.md).
- [Roadmap](../_time/ROADMAP.md).
- [Architecture Design Document](../_design/ADD.md).
