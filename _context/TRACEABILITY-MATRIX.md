## Title

| Field | Value |
| --- | --- |
| Document | Requirements Traceability Matrix — Texas Hold'em learning library |
| Initiative | INI-001 / PRJ-001 |
| Version | 0.1 |
| Status | Derived projection - for review |
| Author | Vestigator (generated from authoritative Markdown) |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Purpose

This matrix projects relationships from the project's Specification, Design, Planning, Time, and Verification documents. It is not the authority for their content or execution status. No `_context/MANAGEMENT-MODEL.yaml` exists, so the backward-compatible `classic` vocabulary and Markdown authorities are assumed. Verification execution is external; all linked tests are currently `Not Run` and have no evidence.

Source counts: 6 objectives, 11 business requirements, 20 functional requirements, 9 quality requirements, 31 acceptance criteria, 7 decisions, 6 work packages, 18 tasks, and 21 planned tests. Roadmap authority: `_context/_time/ROADMAP.md`, horizon H-001 and milestone MS-001, with no committed date.

## 2. ID Prefix Registry

The selected `classic` profile uses these identifiers. The target does not declare migration aliases.

| Semantic entity | Prefix | Dimension |
| --- | --- | --- |
| Objective | OBJ | Specification |
| Requirement | REQ | Specification |
| Functional Requirement | FR | Specification |
| Quality Requirement | NFR | Specification |
| Acceptance Criterion | AC | Specification |
| Architecture Decision | ADR | Design |
| Initiative / Project / Work Package / Task | INI / PRJ / WP / TSK | Planning |
| Horizon / Milestone | H / MS | Time |
| Test / Evidence | TEST / EVD | Verification |

## 3. Matrix

| ID | Type | Description | Parent | Addressed by (decision) | Realized by (work package) | Verified by (test) | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OBJ-001 | Objective | Turn user-supplied DOCX theory into reviewable, structured topics |  |  |  |  |  |  |
| OBJ-002 | Objective | Preserve strategic meaning and provenance |  |  |  |  |  |  |
| OBJ-003 | Objective | Support a coherent learning progression |  |  |  |  |  |  |
| OBJ-004 | Objective | Help the user find theory using informal language |  |  |  |  |  |  |
| OBJ-005 | Objective | Recommend an achievable study sequence |  |  |  |  |  |  |
| OBJ-006 | Objective | Keep the knowledge base correctable and durable |  |  |  |  |  |  |
| REQ-001 | Requirement | The user can import a DOCX and see processing progress, completion, and failure information. | OBJ-001 | ADR-002 |  |  |  |  |
| REQ-002 | Requirement | An import can produce several distinct, structured topics while preserving links to the original document and supporting fragments. | OBJ-001, OBJ-002 | ADR-002, ADR-005 |  |  |  |  |
| REQ-003 | Requirement | Processed topics retain strategic conditions and distinguish sourced content, generated teaching examples, unknowns, and contradictions. | OBJ-002 | ADR-005, ADR-006 |  |  |  |  |
| REQ-004 | Requirement | The system proposes extensible strategic classification, difficulty, and pedagogically justified, acyclic prerequisites without filling unknown fields by invention. | OBJ-002, OBJ-003 | ADR-004 |  |  |  |  |
| REQ-005 | Requirement | The user can explore a descending learning tree, open topics, inspect sources and prerequisites, and return to the topic's location. | OBJ-003, OBJ-006 | ADR-001, ADR-004 |  |  |  |  |
| REQ-006 | Requirement | The user can edit topic content, classification, placement, and prerequisite relations. | OBJ-003, OBJ-006 | ADR-001, ADR-004 |  |  |  |  |
| REQ-007 | Requirement | The user can query imported theory in natural language and receive relevant topics and a source-grounded explanation, or a clear lack-of-evidence or ambiguity response. | OBJ-002, OBJ-004 | ADR-003, ADR-006 |  |  |  |  |
| REQ-008 | Requirement | The user can request a basic learning path ordered by prerequisites and limited to available topics. | OBJ-003, OBJ-005 | ADR-004 |  |  |  |  |
| REQ-009 | Requirement | The system preserves imported documents, topics, relationships, and searchability after restart. | OBJ-001, OBJ-006 | ADR-003, ADR-005, ADR-007 |  |  |  |  |
| REQ-010 | Requirement | The system detects exact repeat imports and flags similar theory for review before avoidable duplication. | OBJ-001, OBJ-006 | ADR-005 |  |  |  |  |
| REQ-011 | Requirement | The application uses locally executed AI and retrieval over imported content, with separate document extraction, storage, indexing, and inference responsibilities. | OBJ-002, OBJ-004 | ADR-002, ADR-003, ADR-006, ADR-007 |  |  |  |  |
| FR-001 | FR | Accept DOCX upload and display queued, extracting, analyzing, completed, and failed states with actionable error information. | REQ-001 |  | WP-002, WP-006 | TEST-001 |  | Not Run |
| FR-002 | FR | Preserve the original file and extract ordered text and tables, plus images where extraction is possible; record omissions. | REQ-002 |  | WP-002 | TEST-002 |  | Not Run |
| FR-003 | FR | Identify distinct topics within one document and generate a title, summary, developed explanation, conditions, applicable examples, visuals, tags, difficulty, prerequisites, and source references when supported. | REQ-002, REQ-003 |  | WP-003 | TEST-003 |  | Not Run |
| FR-004 | FR | Preserve strategic qualifiers, mark unknown facts, report conflicting sources, and label generated teaching examples separately from source-backed claims. | REQ-003 |  | WP-003 | TEST-004 |  | Not Run |
| FR-005 | FR | Detect identical file imports and flag potentially similar existing topics for review. | REQ-010 |  | WP-003 | TEST-005 |  | Not Run |
| FR-006 | FR | Save documents, topics, source fragments, and relationships so they remain available after restart. | REQ-009 |  | WP-001 | TEST-006 |  | Not Run |
| FR-007 | FR | Record extensible strategic facets including street, positions, pot type, in/out of position, board texture, and concept; leave unsupported facets unknown. | REQ-004 |  | WP-004 | TEST-007 |  | Not Run |
| FR-008 | FR | Assign basic, intermediate, or advanced difficulty independently of prerequisites and propose only pedagogically justified prerequisite links. | REQ-004 |  | WP-004 | TEST-008 |  | Not Run |
| FR-009 | FR | Reject any prerequisite change that would create a cycle and permit one topic to connect to several branches without duplicating its content. | REQ-004 |  | WP-004 | TEST-009 |  | Not Run |
| FR-010 | FR | Display a descending learning tree with difficulty, prerequisites, topic navigation, and a route back from a topic to its tree location. | REQ-005 |  | WP-004, WP-006 | TEST-010 |  | Not Run |
| FR-011 | FR | Interpret technical and everyday query terms, retrieve relevant imported topics and source fragments, and show links to topics and tree locations. | REQ-007 |  | WP-005 | TEST-011 |  | Not Run |
| FR-012 | FR | Produce explanations grounded in retrieved source fragments, with source links and strategic conditions preserved. | REQ-003, REQ-007 |  | WP-005 | TEST-012 |  | Not Run |
| FR-013 | FR | Request clarification when unresolved ambiguity materially changes the answer; otherwise show covered cases and state missing information or lack of coverage. | REQ-007 |  | WP-005 | TEST-013 |  | Not Run |
| FR-014 | FR | Recommend a study sequence using available topics, respecting prerequisite order, and briefly explain each recommendation. | REQ-008 |  | WP-005 | TEST-014 |  | Not Run |
| FR-015 | FR | Run model inference locally over retrieved material; keep extraction, storage, indexing, retrieval, and inference as distinct processing responsibilities. | REQ-011 |  | WP-005 | TEST-015 |  | Not Run |
| FR-016 | FR | Display the topic's structured content, source document, and supporting fragment references. | REQ-003, REQ-005 |  | WP-006 | TEST-016 |  | Not Run |
| FR-017 | FR | Let the user edit a topic's explanatory fields, examples, tags, difficulty, and strategic facets. | REQ-006 |  | WP-004, WP-006 | TEST-017 |  | Not Run |
| FR-018 | FR | Let the user add, remove, or correct prerequisite and branch relations, subject to cycle validation. | REQ-006 |  | WP-004 | TEST-018 |  | Not Run |
| FR-019 | FR | Persist edits and update tree and search results to reflect the current topic. | REQ-006, REQ-009 |  | WP-004 | TEST-019 |  | Not Run |
| FR-020 | FR | Present exact-duplicate and similar-topic candidates for the user to review before keeping both. | REQ-010 |  | WP-006 | TEST-020 |  | Not Run |
| NFR-001 | NFR | Import and local-model operations must report progress without freezing tree navigation. | REQ-001, REQ-007 |  | WP-002, WP-005 | TEST-001 |  | Not Run |
| NFR-002 | NFR | The importer must recognize valid DOCX input and clearly reject unsupported or unreadable files. | REQ-001, REQ-002 |  | WP-002 | TEST-002 |  | Not Run |
| NFR-003 | NFR | Import, search, empty, error, and insufficient-evidence states must be understandable from the interface. | REQ-001, REQ-005, REQ-007 | ADR-001 | WP-006 | TEST-021 |  | Not Run |
| NFR-004 | NFR | The tree's visual change with increasing difficulty must retain legibility and navigability. | REQ-005 | ADR-001 | WP-006 | TEST-010 |  | Not Run |
| NFR-005 | NFR | Documents, topics, source links, manual edits, and prerequisite relations must survive application restart. | REQ-009 | ADR-003, ADR-007 | WP-001 | TEST-006 |  | Not Run |
| NFR-006 | NFR | An import or edit failure must not corrupt previously saved knowledge. | REQ-001, REQ-006, REQ-009 | ADR-005 | WP-001 | TEST-019 |  | Not Run |
| NFR-007 | NFR | User documents and their extracted content must be processed by the local application and local AI model. | REQ-011 | ADR-006, ADR-007 | WP-003, WP-005 | TEST-015 |  | Not Run |
| NFR-008 | NFR | Extraction, persistent storage, indexing/retrieval, and model inference must remain distinct responsibilities. | REQ-011 | ADR-002 | WP-001, WP-005 | TEST-015 |  | Not Run |
| NFR-009 | NFR | Strategic classification must accept additional facets or values without reauthoring existing topics. | REQ-004 | ADR-004 | WP-004 | TEST-007 |  | Not Run |
| AC-001 | AC | The user imports it → Processing states advance to completed or show a specific failure | FR-001 |  |  |  |  |  |
| AC-002 | AC | Extraction runs → The original is retained and extracted items or explicit omissions are available for review | FR-002 |  |  |  |  |  |
| AC-003 | AC | Analysis completes → Two separately openable topics exist with source references and supported structured fields | FR-003 |  |  |  |  |  |
| AC-004 | AC | A topic is generated → Those details remain unknown and any generated example is visibly labeled | FR-004 |  |  |  |  |  |
| AC-005 | AC | The user uploads it again → The application identifies the prior import and offers review before creating duplicates | FR-005 |  |  |  |  |  |
| AC-006 | AC | The application restarts → The original document, extracted topics, and source links remain accessible | FR-006 |  |  |  |  |  |
| AC-007 | AC | Classification runs → Positions are recorded and pot type remains unknown | FR-007 |  |  |  |  |  |
| AC-008 | AC | They are classified → They may share difficulty while one is recorded as prerequisite of the other | FR-008 |  |  |  |  |  |
| AC-009 | AC | It is submitted → The link is rejected and the existing graph is preserved | FR-009 |  |  |  |  |  |
| AC-010 | AC | The tree is shown → Branches link to the same topic record | FR-009 |  |  |  |  |  |
| AC-011 | AC | The user requests its location → The tree focuses or reveals the topic's position | FR-010 |  |  |  |  |  |
| AC-012 | AC | The user asks informally about “BB vs BTN en flop Axx” → Relevant available topics and their tree locations are returned | FR-011 |  |  |  |  |  |
| AC-013 | AC | The system answers → It states that condition and links the supporting fragment | FR-012 |  |  |  |  |  |
| AC-014 | AC | The user asks an underspecified question → The system asks for that action or explicitly separates the covered cases | FR-013 |  |  |  |  |  |
| AC-015 | AC | The user searches → The system says coverage is insufficient and may show related available topics | FR-013 |  |  |  |  |  |
| AC-016 | AC | The user requests a beginner path → Only available topics are proposed in prerequisite order, each with a reason and openable link | FR-014 |  |  |  |  |  |
| AC-017 | AC | The user searches → A clear error appears and stored imported content remains intact | FR-015 |  |  |  |  |  |
| AC-018 | AC | The user opens its source → The original document and the associated reference are accessible | FR-016 |  |  |  |  |  |
| AC-019 | AC | The user saves a correction → The corrected fields are shown on reopening the topic | FR-017 |  |  |  |  |  |
| AC-020 | AC | The user saves it → The edit is rejected with an explanation and prior links remain | FR-018 |  |  |  |  |  |
| AC-021 | AC | The application restarts and the user searches → The edit remains and tree and search show the current content | FR-019 |  |  |  |  |  |
| AC-022 | AC | A new topic is processed → The candidate is shown for review without silently merging or duplicating it | FR-020 |  |  |  |  |  |
| AC-023 | AC | The user navigates the tree → Navigation remains usable and processing status is visible | NFR-001 |  |  |  |  |  |
| AC-024 | AC | The user imports it → An explicit file error appears without creating a completed import | NFR-002 |  |  |  |  |  |
| AC-025 | AC | The user opens the tree or searches → A clear empty or insufficient-evidence message and next action appear | NFR-003 |  |  |  |  |  |
| AC-026 | AC | The user explores it → Each level remains readable and navigable | NFR-004 |  |  |  |  |  |
| AC-027 | AC | The application restarts → Documents, topics, corrections, and links remain available | NFR-005 |  |  |  |  |  |
| AC-028 | AC | A later import or edit fails → Existing topics and relations remain accessible and unchanged | NFR-006 |  |  |  |  |  |
| AC-029 | AC | The user imports and queries theory → Processing uses local extraction and model inference without requiring remote AI | NFR-007 |  |  |  |  |  |
| AC-030 | AC | The user inspects the failure → The failed responsibility is identifiable and other stored material remains usable | NFR-008 |  |  |  |  |  |
| AC-031 | AC | A new strategic facet is introduced → Existing topics remain readable and can represent the facet as unknown | NFR-009 |  |  |  |  |  |

## 4. Gap Checklist

| # | Check | Current finding |
| --- | --- | --- |
| 1 | Requirement with no implementation | None |
| 2 | Requirement with no test | None |
| 3 | Orphan task | None; all task-bearing work packages have a Realizes relation. |
| 4 | Requirement modified after verification | Unknown; no execution evidence or trustworthy evidence dates exist. |
| 5 | NFR with no evidence | All 9 NFRs; tests are Not Run. |
| 6 | Work closed but requirement still open | None; no Work Package is marked Done. |

Additional bidirectional findings:

- Dangling references: None.
- Orphan entities lacking upstream justification: None.
- Orphan Work Packages: None.
- Unimplemented FR/NFR requirements: None.
- Untested FR/NFR requirements: None.
- Unevidenced tests: 21 of 21 (TEST-001, TEST-002, TEST-003, TEST-004, TEST-005, TEST-006, TEST-007, TEST-008, TEST-009, TEST-010, TEST-011, TEST-012, TEST-013, TEST-014, TEST-015, TEST-016, TEST-017, TEST-018, TEST-019, TEST-020, TEST-021); expected while Not Run, but no verified status is supported.
- Orphan tests: None.
- Stale verification: unknown because no execution evidence exists.

## References

- `_context/VSD.md`, `_context/_specification/BRD.md`, `_context/_specification/FRDs/*.md`, and `_context/_specification/NFRD.md` — Specification.
- `_context/_design/ADD.md` — Design.
- `_context/_planning/INI-001-texas-holdem-learning-library.md`, `PRJ-001-local-mvp.md`, and `WP-*.md` — Planning.
- `_context/_time/ROADMAP.md` — Time.
- `_context/_verification/TMP.md` — Verification definition; execution evidence remains external.
