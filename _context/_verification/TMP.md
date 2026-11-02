## Title

| Field | Value |
| --- | --- |
| Document | Test Management Plan — Texas Hold'em learning library |
| Initiative | INI-001 / PRJ-001 local first version |
| Version | 0.1 |
| Status | Draft - for owner review |
| Author | Quaestor |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Introduction

### 1.1 Purpose

Plan risk-based verification of the local application against its Specification and Aelium Organizational Test Strategy. This plan defines scope, depth, test conditions, and evidence expectations. It does not report execution or certify readiness. The owner develops and manages the project alone for approximately 12 hours weekly; no delivery date or separate test infrastructure is committed.

## 2. Test Objectives

| Objective | Description |
| --- | --- |
| Faithful imported knowledge | Check topic boundaries, source links, strategic conditions, unknowns, and generated-example labels against representative DOCX source material. |
| Correctable learning graph | Check difficulty, branch placement, prerequisite order, cycle prevention, manual correction, and tree navigation. |
| Grounded retrieval | Check informal queries, source-backed answers, material ambiguity, insufficient evidence, and introductory study paths. |
| Durable local operation | Check persistence across restart, failure recovery, local-only model calls, and visible import/search/error states. |

## 3. Test Scope

### In Scope

- All 20 functional and 9 quality requirements in the current first-version Specification receive planned coverage. Depth is risk-based, as justified by [SQCA](SQCA.md), rather than identical for every requirement.
- **Deep coverage:** source and answer correctness, end-to-end study flows, invalid edits and cycles, provenance/unknown-state clarity, stored-data integrity, and recovery. Use multiple representative DOCX structures, strategic qualifiers, missing context, and failure cases.
- **Representative coverage:** model availability, performance responsiveness, DOCX compatibility, modular failures, facet extension, navigation, and accessible responsive use.
- **Spot checks:** duplicate-candidate presentation and visual scene transitions where failure has bounded impact.

### Out of Scope

- Solver mathematics or correctness of undocumented poker strategies; the application must not claim these.
- Cloud AI, remote hosting, multi-user access, authentication, and physical-safety testing, which are outside the confirmed product scope.
- Formal performance thresholds or library capacity certification; none are specified. Observations can inform a later requirement.

## 4. Test Strategy

The Aelium Organizational Test Strategy sets unit, integration, system/end-to-end, and acceptance levels. Selection below follows the SQCA's seven High priorities. Normal functional correctness and local-data integrity are high-risk paths; failure to meet their exit conditions prevents first-version acceptance until fixed or explicitly recorded as residual risk. With one owner, independent review is not assumed to have occurred.

| Level | Description |
| --- | --- |
| Unit Testing | Exercise DOCX fragment ordering, structured-output validation, evidence-link rules, graph cycle checks, topological sort, query term handling, and persistence transactions. |
| Integration Testing | Exercise upload through extraction and storage; model adapter through topic proposal and indexing; retrieval through cited answers; edited topics through tree and search refresh. |
| System Testing | Exercise invalid DOCX, unavailable model, failed index, restart, mobile/desktop navigation, duplicate review, and visible error states. |
| End-to-End Testing | Import a representative multi-topic DOCX, correct a topic, navigate its prerequisites, ask a grounded question, request a study path, restart, and verify all saved relationships. |
| Acceptance Testing | The project owner reviews representative sourced explanations and source links against the original documents, then records acceptance or remaining risk. |

## 5. Test Environment

| Environment | Description |
| --- | --- |
| Local development and test | Browser, local API, local model service, and disposable application data directory on the owner's machine. Keep test data separate from the study library. |
| Local user library | Used only after disposable-data checks pass; verify restart and source viewing without altering original test fixtures. |

No separate test-infrastructure workstream is required, as confirmed by the owner. If a dedicated environment, model evaluation corpus, or test-data generation system becomes necessary, route it to Rector rather than treating this section as its build plan.

## 6. Test Data

Use small synthetic DOCX fixtures covering paragraphs, headings, tables, extractable images, multiple topics, duplicate content, malformed/unsupported files, and strategically distinct contexts. Use user-supplied Mentopoker documents for owner acceptance only when available; preserve originals and record document/fragment references. Include queries such as “BB vs BTN en flop Axx” with differing preflop actions, missing stack depth, no matching source, and introductory study goals. Expected strategic claims must be written from the fixture's actual content; no invented ranges or frequencies are treated as truth. Retain fixture and expected-result versions with the tests.

## 7. Automation Strategy

Automate deterministic unit and API/integration checks, including cycle rejection, import status, source links, storage restart, and retrieval evidence IDs. Keep a small browser flow for the main import/tree/search path and perform manual source-fidelity acceptance against real documents. The chosen framework and CI service are not fixed by the Specification; local repeatability is the immediate requirement. A future CI pipeline may run the deterministic subset. External test execution and its evidence, not this Markdown file, are authoritative for actual results.

## 8. Defect Management

Record each failed check with the test ID, requirement ID, environment, fixture or document reference, expected and actual result, severity, and reproduction steps. Fix and retest before marking resolved; run regression checks around neighboring import, graph, and retrieval behavior. Treat loss or corruption of original material, unsupported strategy presented as sourced fact, or broken evidence links as release-blocking until corrected or explicitly accepted with a recorded risk decision. No issue tracker is declared; the owner selects where defect records live before execution.

## 9. Metrics and Reporting

| Metric | Description |
| --- | --- |
| Test Coverage | Planned and executed requirement coverage, reported separately; current plan covers 29 of 29 FR/NFR identifiers but has no execution evidence. |
| High-risk coverage | Execution status of tests for the seven High SQCA subcharacteristics, especially source correctness, data integrity, and recovery. |
| Pass/Fail/Blocked/Not Run | Count each state from actual execution evidence; do not infer PASS from a planned row. |
| Open defects and residual risk | Count by severity, with explicit owner decision for any accepted remaining risk. |
| Import fidelity observations | Record extracted/omitted paragraphs, tables, images, and verified source links for representative files. |

## 10. Traceability

Every listed test is planned and **Not Run**. The `Evidence` column is `Pending` until an execution record exists; assign a stable `EVD-xxx` ID then and link its fixture, environment, result, and artifact location. Planned evidence can be kept under a project `tests/evidence/` directory or the owner's chosen execution authority, but no evidence file is claimed here. Repeated test IDs indicate one scenario verifies several requirements. Deep tests are identified below by `Deep`; representative and spot-check tests use smaller fixture sets, according to the SQCA risk basis.

| Requirement (FR-xxx / NFR-xxx) | Test (TEST-xxx) | Evidence | Status |
| --- | --- | --- | --- |
| FR-001 | TEST-001 — Representative: import valid and invalid DOCX; observe queued, extraction, completion, and specific failure states. | Pending | Not Run |
| NFR-001 | TEST-001 — Representative: navigate the tree during an import and local-model query; status stays visible. | Pending | Not Run |
| FR-002 | TEST-002 — Deep: compare ordered paragraphs, table cells, and extractable images with original DOCX; inspect omission warnings. | Pending | Not Run |
| NFR-002 | TEST-002 — Representative: reject unsupported and malformed files without marking an import complete. | Pending | Not Run |
| FR-003 | TEST-003 — Deep: import a fixture with two distinct Texas Hold'em strategies; verify separate structured topics and source references. | Pending | Not Run |
| FR-004 | TEST-004 — Deep: inspect positions, actions, stack and board conditions, missing values, contradictions, and generated-example labels against source. | Pending | Not Run |
| FR-005 | TEST-005 — Spot check: reimport an identical DOCX and import similar theory; inspect exact and candidate warnings. | Pending | Not Run |
| FR-006 | TEST-006 — Deep: restart after import and verify original file, fragments, topics, and relations remain accessible. | Pending | Not Run |
| NFR-005 | TEST-006 — Deep: repeat restart after a manual correction and check saved data and source links. | Pending | Not Run |
| FR-007 | TEST-007 — Representative: classify a source with known BTN/BB positions and unknown pot type; add a new facet without changing prior topics. | Pending | Not Run |
| NFR-009 | TEST-007 — Representative: existing topics remain readable after adding a facet; unknown values remain explicit. | Pending | Not Run |
| FR-008 | TEST-008 — Representative: give two topics the same difficulty while one is a real prerequisite of the other. | Pending | Not Run |
| FR-009 | TEST-009 — Deep: reject a cycle atomically and link one topic from two branches without duplicating its record. | Pending | Not Run |
| FR-010 | TEST-010 — Representative: traverse all difficulty levels, open a topic, and return to its exact tree location. | Pending | Not Run |
| NFR-004 | TEST-010 — Representative: verify tree labels and controls remain legible across the four illustrated scenes at desktop and narrow widths. | Pending | Not Run |
| FR-011 | TEST-011 — Representative: search technical and colloquial variants of a BB vs BTN A-high flop question; inspect retrieved topics and fragment IDs. | Pending | Not Run |
| FR-012 | TEST-012 — Deep: compare a generated answer with cited fragments and verify all strategic conditions and unsupported-number avoidance. | Pending | Not Run |
| FR-013 | TEST-013 — Deep: test missing preflop action, ambiguous initiative, and absent coverage; expect clarification or explicit covered cases. | Pending | Not Run |
| FR-014 | TEST-014 — Deep: request a beginner path and verify all items exist, follow prerequisite order, and have reasons and links. | Pending | Not Run |
| FR-015 | TEST-015 — Representative: disable local model and index in turn; distinguish failures and preserve stored topics. | Pending | Not Run |
| NFR-007 | TEST-015 — Representative: inspect normal import and query traffic for local inference with no required remote AI call. | Pending | Not Run |
| NFR-008 | TEST-015 — Representative: identify whether extraction, storage, indexing, or inference failed. | Pending | Not Run |
| FR-016 | TEST-016 — Deep: open a topic's original document and associated fragment; check provenance and labels. | Pending | Not Run |
| FR-017 | TEST-017 — Deep: correct an explanation, difficulty, and facet; save and reopen. | Pending | Not Run |
| FR-018 | TEST-018 — Deep: edit prerequisite and placement links; reject a cycle without partial change. | Pending | Not Run |
| FR-019 | TEST-019 — Deep: edit a topic, restart, and confirm tree and search use current saved content. | Pending | Not Run |
| NFR-006 | TEST-019 — Deep: force a failed edit or import and confirm previously saved knowledge remains intact. | Pending | Not Run |
| FR-020 | TEST-020 — Spot check: show a similar-topic candidate for review without silent merge or duplicate. | Pending | Not Run |
| NFR-003 | TEST-021 — Deep: show empty, loading, failed, and insufficient-evidence states with an understandable next action. | Pending | Not Run |

The consolidated Traceability Matrix is not authored here. It should be generated or refreshed after this TMP; until then its absence is a documented cross-dimensional gap.

## References

- [Aelium Test Strategy](Test-Strategy.md) and [Test Policy](Test-Policy.md).
- [SQCA](SQCA.md), [VSD](../VSD.md), [BRD](../_specification/BRD.md), functional requirements in `../_specification/FRDs/`, and [NFRD](../_specification/NFRD.md).
- ISO/IEC 29119-2:2021 §7.1 and ISO/IEC 29119-3:2021 §11.
