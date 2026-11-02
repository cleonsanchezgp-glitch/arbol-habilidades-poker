## Document Control

| Field | Value |
| --- | --- |
| Requirement Name | Topic review, correction, and source inspection |
| ID | FRD-REVIEW |
| Version | 0.1 |
| Author | Consultor |
| Last Updated | 2026-10-31 |

## 1. Overview

Allow the user to inspect original sources, correct generated topics and classifications, and preserve those corrections.

## 2. Actors

| Actor | Description |
| --- | --- |
| User | Reviews and edits processed theory. |
| System | Validates and persists changes. |

## 3. Functional Requirements

| ID | Description | Priority | Traces to (REQ-xxx) |
| --- | --- | --- | --- |
| FR-016 | Display the topic's structured content, source document, and supporting fragment references. | Must | REQ-005, REQ-003 |
| FR-017 | Let the user edit a topic's explanatory fields, examples, tags, difficulty, and strategic facets. | Must | REQ-006 |
| FR-018 | Let the user add, remove, or correct prerequisite and branch relations, subject to cycle validation. | Must | REQ-006 |
| FR-019 | Persist edits and update tree and search results to reflect the current topic. | Must | REQ-006, REQ-009 |
| FR-020 | Present exact-duplicate and similar-topic candidates for the user to review before keeping both. | Should | REQ-010 |

## 4. Workflow

1. The user opens a topic and its source references.
2. The user edits content, facets, difficulty, examples, or relations.
3. The system validates relations and saves accepted changes.
4. Tree and search representations are refreshed from the saved topic.
5. When duplicate candidates exist, the user reviews them before deciding whether to retain separate topics.

## 5. Inputs

| Input | Source |
| --- | --- |
| Topic edits and relation corrections | User |
| Original document and extracted fragments | Persistent knowledge store |

## 6. Outputs

| Output | Destination |
| --- | --- |
| Updated topic and relations | Persistent topic store |
| Updated tree and index | Navigation and search |
| Source view and duplicate candidates | Review interface |

## 7. Acceptance Criteria

| ID | Given | When | Then | Verifies |
| --- | --- | --- | --- | --- |
| AC-018 | A topic has a source fragment | The user opens its source | The original document and the associated reference are accessible | FR-016 |
| AC-019 | A topic has an incorrect difficulty or explanation | The user saves a correction | The corrected fields are shown on reopening the topic | FR-017 |
| AC-020 | A proposed prerequisite would create a cycle | The user saves it | The edit is rejected with an explanation and prior links remain | FR-018 |
| AC-021 | A topic has been edited | The application restarts and the user searches | The edit remains and tree and search show the current content | FR-019 |
| AC-022 | Similar content already exists | A new topic is processed | The candidate is shown for review without silently merging or duplicating it | FR-020 |

## 8. Error Handling

Failed saves leave the previous persisted topic intact and show an error. Source references that cannot be opened are identified explicitly. Relation validation errors do not partially apply a change.

## 9. Interface Requirements *(optional — only when this feature exposes or consumes an explicit interface contract, e.g. API, event, file format)*

No external interface contract is specified for this feature.

## References

- [Business Requirements Document](../BRD.md).
