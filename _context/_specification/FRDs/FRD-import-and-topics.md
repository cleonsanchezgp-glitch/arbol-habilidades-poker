## Document Control

| Field | Value |
| --- | --- |
| Requirement Name | DOCX import and topic generation |
| ID | FRD-IMPORT |
| Version | 0.1 |
| Author | Consultor |
| Last Updated | 2026-10-31 |

## 1. Overview

Import a user DOCX, preserve the original, extract its content, and produce one or more reviewable topics grounded in source fragments.

## 2. Actors

| Actor | Description |
| --- | --- |
| User | Submits documents and reviews the resulting topics. |
| System | Extracts, analyzes, stores, and indexes content. |

## 3. Functional Requirements

| ID | Description | Priority | Traces to (REQ-xxx) |
| --- | --- | --- | --- |
| FR-001 | Accept DOCX upload and display queued, extracting, analyzing, completed, and failed states with actionable error information. | Must | REQ-001 |
| FR-002 | Preserve the original file and extract ordered text and tables, plus images where extraction is possible; record omissions. | Must | REQ-002 |
| FR-003 | Identify distinct topics within one document and generate a title, summary, developed explanation, conditions, applicable examples, visuals, tags, difficulty, prerequisites, and source references when supported. | Must | REQ-002, REQ-003 |
| FR-004 | Preserve strategic qualifiers, mark unknown facts, report conflicting sources, and label generated teaching examples separately from source-backed claims. | Must | REQ-003 |
| FR-005 | Detect identical file imports and flag potentially similar existing topics for review. | Should | REQ-010 |
| FR-006 | Save documents, topics, source fragments, and relationships so they remain available after restart. | Must | REQ-009 |

## 4. Workflow

1. The user selects a DOCX and submits it.
2. The system records the file and shows processing status.
3. Extraction captures document content and reports unreadable or omitted elements.
4. Analysis separates topics, generates structured explanations, and links source fragments.
5. The system proposes classification, difficulty, and prerequisites, stores the result, and indexes searchable content.
6. The user reviews topics and any duplicate warnings.

## 5. Inputs

| Input | Source |
| --- | --- |
| DOCX file | User |
| Existing documents and topics | Persistent knowledge store |

## 6. Outputs

| Output | Destination |
| --- | --- |
| Import status, warnings, and errors | Import interface |
| Original document and extracted fragments | Persistent knowledge store |
| Structured topics and source links | Topic store and search index |
| Duplicate and similarity candidates | Review interface |

## 7. Acceptance Criteria

| ID | Given | When | Then | Verifies |
| --- | --- | --- | --- | --- |
| AC-001 | A valid DOCX is selected | The user imports it | Processing states advance to completed or show a specific failure | FR-001 |
| AC-002 | A DOCX contains paragraphs, a table, and an extractable image | Extraction runs | The original is retained and extracted items or explicit omissions are available for review | FR-002 |
| AC-003 | A DOCX contains two identifiable strategies | Analysis completes | Two separately openable topics exist with source references and supported structured fields | FR-003 |
| AC-004 | A source omits stack depth or documented bet size | A topic is generated | Those details remain unknown and any generated example is visibly labeled | FR-004 |
| AC-005 | An identical file was imported earlier | The user uploads it again | The application identifies the prior import and offers review before creating duplicates | FR-005 |
| AC-006 | An import completed | The application restarts | The original document, extracted topics, and source links remain accessible | FR-006 |

## 8. Error Handling

Invalid or unreadable DOCX files, extraction gaps, local model failure, and indexing failure produce visible states. The original file and any successfully extracted material remain available for review; a partial import is not silently presented as complete.

## 9. Interface Requirements *(optional — only when this feature exposes or consumes an explicit interface contract, e.g. API, event, file format)*

| ID | Interface | Description | Traces to (REQ-xxx) |
| --- | --- | --- | --- |
| INT-001 | DOCX file input | Accepts a DOCX document from the user. | REQ-001 |

## References

- [Business Requirements Document](../BRD.md).
- User's project brief in this conversation, 2026-10-31.
