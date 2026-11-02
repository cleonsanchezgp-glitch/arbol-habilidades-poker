## Title

| Field | Value |
| --- | --- |
| Document | Non-Functional Requirements Document — Texas Hold'em Theory Knowledge Tree |
| Initiative | Organize and study Mentopoker theory |
| Version | 0.1 |
| Status | Draft - for review |
| Author | Consultor |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Overview

Quality requirements for the first version, grouped by ISO/IEC 25010:2023 characteristics. Numeric latency and capacity targets were not provided; observable behavior is stated without inventing thresholds. Every requirement traces to the BRD.

## 2. Performance Efficiency

| ID | Requirement | Target / Threshold | Traces to (REQ-xxx) | Verifies (AC-xxx) |
| --- | --- | --- | --- | --- |
| NFR-001 | Import and local-model operations must report progress without freezing tree navigation. | Navigation remains usable while processing; no numeric time target specified. | REQ-001, REQ-007 | AC-023 |

## 3. Compatibility

| ID | Requirement | Target / Threshold | Traces to (REQ-xxx) | Verifies (AC-xxx) |
| --- | --- | --- | --- | --- |
| NFR-002 | The importer must recognize valid DOCX input and clearly reject unsupported or unreadable files. | Valid DOCX enters processing; unsupported input receives an explicit error. | REQ-001, REQ-002 | AC-024 |

## 4. Interaction Capability

| ID | Requirement | Target / Threshold | Traces to (REQ-xxx) | Verifies (AC-xxx) |
| --- | --- | --- | --- | --- |
| NFR-003 | Import, search, empty, error, and insufficient-evidence states must be understandable from the interface. | Each state has visible text explaining its meaning and available next action. | REQ-001, REQ-005, REQ-007 | AC-025 |
| NFR-004 | The tree's visual change with increasing difficulty must retain legibility and navigability. | Basic, intermediate, and advanced areas remain readable and operable. | REQ-005 | AC-026 |

## 5. Reliability

| ID | Requirement | Target / Threshold | Traces to (REQ-xxx) | Verifies (AC-xxx) |
| --- | --- | --- | --- | --- |
| NFR-005 | Documents, topics, source links, manual edits, and prerequisite relations must survive application restart. | Previously completed data and corrections are available after restart. | REQ-009 | AC-027 |
| NFR-006 | An import or edit failure must not corrupt previously saved knowledge. | Existing records remain usable after a failed operation. | REQ-001, REQ-006, REQ-009 | AC-028 |

## 6. Security

| ID | Requirement | Target / Threshold | Traces to (REQ-xxx) | Verifies (AC-xxx) |
| --- | --- | --- | --- | --- |
| NFR-007 | User documents and their extracted content must be processed by the local application and local AI model. | A standard import and query do not require sending content to a remote AI service. | REQ-011 | AC-029 |

## 7. Maintainability

| ID | Requirement | Target / Threshold | Traces to (REQ-xxx) | Verifies (AC-xxx) |
| --- | --- | --- | --- | --- |
| NFR-008 | Extraction, persistent storage, indexing/retrieval, and model inference must remain distinct responsibilities. | Each responsibility has an identifiable interface and can fail with a distinguishable error. | REQ-011 | AC-030 |

## 8. Flexibility

| ID | Requirement | Target / Threshold | Traces to (REQ-xxx) | Verifies (AC-xxx) |
| --- | --- | --- | --- | --- |
| NFR-009 | Strategic classification must accept additional facets or values without reauthoring existing topics. | An added facet leaves existing classifications readable and unknown values explicit. | REQ-004 | AC-031 |

## 9. Safety

No separate physical-safety requirement is supported by the project brief. The risk of misleading study advice is covered by source fidelity and evidence-gap requirements in the BRD and FRDs; this section does not imply solver-grade accuracy.

## 10. Acceptance Criteria

| ID | Given | When | Then | Verifies |
| --- | --- | --- | --- | --- |
| AC-023 | An import or local-model query is running | The user navigates the tree | Navigation remains usable and processing status is visible | NFR-001 |
| AC-024 | An unsupported or unreadable file is selected | The user imports it | An explicit file error appears without creating a completed import | NFR-002 |
| AC-025 | There is no imported content or retrieval has insufficient support | The user opens the tree or searches | A clear empty or insufficient-evidence message and next action appear | NFR-003 |
| AC-026 | The tree contains all three difficulty levels | The user explores it | Each level remains readable and navigable | NFR-004 |
| AC-027 | An import and manual correction have been saved | The application restarts | Documents, topics, corrections, and links remain available | NFR-005 |
| AC-028 | Existing topics are saved | A later import or edit fails | Existing topics and relations remain accessible and unchanged | NFR-006 |
| AC-029 | The application is configured for normal local operation | The user imports and queries theory | Processing uses local extraction and model inference without requiring remote AI | NFR-007 |
| AC-030 | A processing stage fails | The user inspects the failure | The failed responsibility is identifiable and other stored material remains usable | NFR-008 |
| AC-031 | Topics already have classifications | A new strategic facet is introduced | Existing topics remain readable and can represent the facet as unknown | NFR-009 |

## References

- [Business Requirements Document](BRD.md).
- [Aelium Organizational Test Policy](../_verification/Test-Policy.md).
- ISO/IEC 25010:2023, Systems and Software Quality Models.
