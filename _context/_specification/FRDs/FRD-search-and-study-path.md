## Document Control

| Field | Value |
| --- | --- |
| Requirement Name | Natural-language theory search and study paths |
| ID | FRD-SEARCH |
| Version | 0.1 |
| Author | Consultor |
| Last Updated | 2026-10-31 |

## 1. Overview

Interpret informal study requests, retrieve relevant imported topics and fragments, and present grounded explanations or prerequisite-ordered paths.

## 2. Actors

| Actor | Description |
| --- | --- |
| User | Asks about theory or requests a learning path. |
| System | Retrieves material and composes a local-model response. |

## 3. Functional Requirements

| ID | Description | Priority | Traces to (REQ-xxx) |
| --- | --- | --- | --- |
| FR-011 | Interpret technical and everyday query terms, retrieve relevant imported topics and source fragments, and show links to topics and tree locations. | Must | REQ-007 |
| FR-012 | Produce explanations grounded in retrieved source fragments, with source links and strategic conditions preserved. | Must | REQ-007, REQ-003 |
| FR-013 | Request clarification when unresolved ambiguity materially changes the answer; otherwise show covered cases and state missing information or lack of coverage. | Must | REQ-007 |
| FR-014 | Recommend a study sequence using available topics, respecting prerequisite order, and briefly explain each recommendation. | Must | REQ-008 |
| FR-015 | Run model inference locally over retrieved material; keep extraction, storage, indexing, retrieval, and inference as distinct processing responsibilities. | Must | REQ-011 |

## 4. Workflow

1. The user enters an informal theory question or learning goal.
2. The system identifies relevant terms and retrieves indexed source fragments and topics.
3. It checks material ambiguity and evidence coverage.
4. The local model composes a grounded answer, asks a needed clarification, or reports insufficient content.
5. For a study goal, the system orders available topics by prerequisites and offers navigable links.

## 5. Inputs

| Input | Source |
| --- | --- |
| Natural-language query | User |
| Indexed topics and source fragments | Imported knowledge |
| Prerequisite relations | Topic store |

## 6. Outputs

| Output | Destination |
| --- | --- |
| Grounded explanation, source links, topic links, or clarification | Search interface |
| Prerequisite-ordered study path | Search interface and tree navigation |

## 7. Acceptance Criteria

| ID | Given | When | Then | Verifies |
| --- | --- | --- | --- | --- |
| AC-012 | Imported theory concerns BB vs BTN on A-high flops | The user asks informally about “BB vs BTN en flop Axx” | Relevant available topics and their tree locations are returned | FR-011 |
| AC-013 | A retrieved fragment limits advice to a specific preflop action | The system answers | It states that condition and links the supporting fragment | FR-012 |
| AC-014 | The missing preflop action changes which source applies | The user asks an underspecified question | The system asks for that action or explicitly separates the covered cases | FR-013 |
| AC-015 | No imported theory supports the exact question | The user searches | The system says coverage is insufficient and may show related available topics | FR-013 |
| AC-016 | Basic topics and prerequisites are available | The user requests a beginner path | Only available topics are proposed in prerequisite order, each with a reason and openable link | FR-014 |
| AC-017 | The local model is unavailable | The user searches | A clear error appears and stored imported content remains intact | FR-015 |

## 8. Error Handling

An empty index, failed retrieval, or unavailable local model must be distinguishable from a valid no-results answer. The system must not fill evidence gaps with unsupported strategic claims.

## 9. Interface Requirements *(optional — only when this feature exposes or consumes an explicit interface contract, e.g. API, event, file format)*

No external interface contract is specified for this feature.

## References

- [Business Requirements Document](../BRD.md).
