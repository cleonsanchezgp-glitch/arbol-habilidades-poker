## Title

| Field | Value |
| --- | --- |
| Document | Business Requirements Document — Texas Hold'em Theory Knowledge Tree |
| Initiative | Organize and study Mentopoker theory |
| Version | 0.1 |
| Status | Draft - for review |
| Author | Consultor, based on the user's project brief |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Introduction

### 1.1 Purpose

The user needs to turn collected Texas Hold'em theory into an organized, searchable learning resource while preserving the conditions and provenance of each strategic explanation.

### 1.2 Scope

The first version covers DOCX import, structured topics, a learning tree, review and correction, local source-grounded natural-language search, a basic study sequence, and durable storage. It does not calculate solver results or supply unsupported strategic advice.

### 1.3 Definitions

| Term | Definition |
| --- | --- |
| Topic | A distinct concept or strategy extracted from one or more imported documents. |
| Source fragment | A traceable portion of an original document supporting a topic or answer. |
| Prerequisite | A topic the learner should understand before another topic. It is separate from difficulty. |
| RAG | Retrieval of indexed source material to ground a locally generated response. |
| Texas Hold'em | The poker modality covered by this product. |
| Ollama | A proposed local AI runtime, separate from the poker modality and replaceable in the architecture. |
| Generated example | Teaching material created to clarify a source-backed concept, identified separately from source claims. |

## 2. Business Objectives

| Objective | Description |
| --- | --- |
| OBJ-001 | Transform DOCX material into durable, reviewable topics with source links. |
| OBJ-002 | Preserve the meaning, conditions, limitations, and provenance of imported theory. |
| OBJ-003 | Organize topics in a correctable learning progression. |
| OBJ-004 | Find relevant imported theory using informal language. |
| OBJ-005 | Suggest study sequences supported by available topics. |
| OBJ-006 | Keep knowledge correctable and persistent. |

## 3. Stakeholders

| Stakeholder | Role | Interest |
| --- | --- | --- |
| Project owner and learner | Primary user | Accurate, navigable, correctable, durable theory |
| Aelium | Product organization | Maintainable product and risk-based verification |

## 4. Business Requirements

| ID | Requirement | Priority | Traces to (OBJ-xxx) |
| --- | --- | --- | --- |
| REQ-001 | The user can import a DOCX and see processing progress, completion, and failure information. | Must | OBJ-001 |
| REQ-002 | An import can produce several distinct, structured topics while preserving links to the original document and supporting fragments. | Must | OBJ-001, OBJ-002 |
| REQ-003 | Processed topics retain strategic conditions and distinguish sourced content, generated teaching examples, unknowns, and contradictions. | Must | OBJ-002 |
| REQ-004 | The system proposes extensible strategic classification, difficulty, and pedagogically justified, acyclic prerequisites without filling unknown fields by invention. | Must | OBJ-003, OBJ-002 |
| REQ-005 | The user can explore a descending learning tree, open topics, inspect sources and prerequisites, and return to the topic's location. | Must | OBJ-003, OBJ-006 |
| REQ-006 | The user can edit topic content, classification, placement, and prerequisite relations. | Must | OBJ-006, OBJ-003 |
| REQ-007 | The user can query imported theory in natural language and receive relevant topics and a source-grounded explanation, or a clear lack-of-evidence or ambiguity response. | Must | OBJ-004, OBJ-002 |
| REQ-008 | The user can request a basic learning path ordered by prerequisites and limited to available topics. | Must | OBJ-005, OBJ-003 |
| REQ-009 | The system preserves imported documents, topics, relationships, and searchability after restart. | Must | OBJ-001, OBJ-006 |
| REQ-010 | The system detects exact repeat imports and flags similar theory for review before avoidable duplication. | Should | OBJ-001, OBJ-006 |
| REQ-011 | The application uses locally executed AI and retrieval over imported content, with separate document extraction, storage, indexing, and inference responsibilities. | Must | OBJ-002, OBJ-004 |

## 5. Business Constraints

| ID | Constraint | Rationale |
| --- | --- | --- |
| CON-001 | Imported user documents are the primary knowledge authority. | The tool organizes and explains the user's theory. |
| CON-002 | AI inference executes locally. | Explicit product constraint from the project brief. |
| CON-004 | The poker modality in scope is Texas Hold'em. | Clarification from the project owner. |
| CON-003 | The repository contains a static interface prototype but no backend or persistent application architecture. | The visual design can be adapted; data processing and storage still require design. |

The brief does not establish regulatory, budget, licensing, or deployment constraints. These remain open rather than assumed.

## 6. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| DOCX layout contains tables or images whose meaning is lost during extraction | Incomplete or misleading topic | Retain the original file, report extraction omissions, and allow review. |
| A generated explanation changes a strategic condition or invents numbers | Incorrect study material | Link claims to source fragments, label generated examples, and expose unsupported or unknown details. |
| Similar topics and inferred prerequisites create duplicate or misleading learning paths | Confusing tree | Flag similarity, allow manual correction, and reject cyclic prerequisite links. |
| Local model or index is unavailable | Import or search cannot complete | Surface clear status and errors while keeping stored material intact. |

## 7. Success Criteria

- A DOCX with several identifiable concepts can be imported into several separately editable topics, each linked to its original document.
- The tree shows difficulty and prerequisites, prevents cycles, and retains manual corrections after restart.
- A natural-language query returns relevant imported material with sources, or explains what information is missing.
- An introductory study request returns only available topics in prerequisite order.
- Import, processing, search, and failure states are visible to the user.

## References

- [Vision and Scope Document](../VSD.md).
- User's project brief in this conversation, 2026-10-31.
- ISO/IEC/IEEE 29148:2018, Requirements Engineering.
