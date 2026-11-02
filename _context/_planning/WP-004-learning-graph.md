## Title

| Field | Value |
| --- | --- |
| Document | Learning graph and editing |
| Work Package ID | WP-004 |
| Version | 0.1 |
| Status | Planned |
| Author | Rector |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Overview

Maintain separate strategic facets, difficulty, branch placement, and acyclic prerequisite relations; allow the user to correct generated material.

## 2. Belongs to Project

| Project (PRJ-xxx) |
| --- |
| PRJ-001 |

## 3. Realizes

| Requirement (FR-xxx / NFR-xxx) | Notes |
| --- | --- |
| FR-007 | Extensible facets and unknown values. |
| FR-008 | Difficulty independent of prerequisite links. |
| FR-009 | Prevent cycles and duplicate topic content. |
| FR-010 | Navigable descending tree and location link. |
| FR-017 | Correct topic fields and classification. |
| FR-018 | Correct branch and prerequisite relations. |
| FR-019 | Persist edits and refresh representations. |
| NFR-009 | Extend facets without invalidating existing records. |

## 4. Tasks

| ID | Task | Status | Owner |
| --- | --- | --- | --- |
| TSK-010 | Implement facet, difficulty, placement, and prerequisite data rules. | Planned | Project owner |
| TSK-011 | Implement cycle validation and topological ordering of prerequisites. | Planned | Project owner |
| TSK-012 | Implement topic and relation edits, atomic save, and tree-location navigation. | Planned | Project owner |

## 5. Status

| Field | Value |
| --- | --- |
| Overall status | Planned |
| Start date | Not committed |
| Target completion | Not committed |

## References

- [Project](PRJ-001-local-mvp.md).
- [Tree FRD](../_specification/FRDs/FRD-learning-tree.md).
- [Review FRD](../_specification/FRDs/FRD-review-and-editing.md).
