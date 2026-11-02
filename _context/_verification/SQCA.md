## Title

| Field | Value |
| --- | --- |
| Document | Software Quality Characteristics Analysis (SQCA) |
| Initiative | Texas Hold'em learning library, INI-001 |
| Version | 0.1 |
| Status | Draft - for owner review |
| Author | Quaestor |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

## 1. Purpose

Prioritize all 40 ISO/IEC 25010:2023 product-quality subcharacteristics against this single-user local study application. The stated priorities derive from the user's DOCX import, source-fidelity, tree, search, correction, and persistence requirements and from Aelium's risk-proportionate testing policy. They determine test depth in the TMP. No legal, multi-user, uptime, or physical-safety obligations have been asserted.

## 2. Priority Scale

| Priority | Meaning |
| --- | --- |
| High | Failure would undermine a core study outcome or risk losing or misrepresenting the user's knowledge; dedicated deep coverage. |
| Medium | Real but bounded impact; representative coverage. |
| Low | Limited impact in the confirmed first-version scope; spot checks or incidental coverage. |
| N/A | The characteristic has no applicable behavior in the confirmed local, single-user scope; rationale required. |

## 3. Characteristic Assessment

### 3.1 Functional Suitability

| Subcharacteristic | Priority | Rationale | Derived test types |
| --- | --- | --- | --- |
| Functional completeness | High | The first version is accepted only if import, tree, correction, search, and study paths all work (VSD OBJ-001–006). | End-to-end acceptance and requirements coverage. |
| Functional correctness | High | Incorrect extraction, invented strategic conditions, or wrong sources would make study material misleading (REQ-002–003, REQ-007). | Source comparison, data-validation, grounded-answer tests. |
| Functional appropriateness | High | The main purpose is finding and studying theory in a useful dependency order (REQ-005, REQ-007–008). | Task-based acceptance with realistic queries and paths. |

### 3.2 Performance Efficiency

| Subcharacteristic | Priority | Rationale | Derived test types |
| --- | --- | --- | --- |
| Time behaviour | Medium | Local model processing may be slow, but NFR-001 requires navigation and status to remain usable during it. | Responsive-navigation and import-progress checks. |
| Resource utilization | Medium | The local model and document processing share one user's machine; excessive resource use could interrupt study. | Representative CPU, memory, and storage observation. |
| Capacity | Low | No library-size or concurrent-user target is specified; first version is single-user. | Sample library volume smoke check. |

### 3.3 Compatibility

| Subcharacteristic | Priority | Rationale | Derived test types |
| --- | --- | --- | --- |
| Co-existence | Low | The application shares a local machine, but no neighboring system or resource guarantee is specified. | Local run smoke check alongside normal browser use. |
| Interoperability | Medium | DOCX input and the local model service are required system boundaries (REQ-001, REQ-011). | DOCX and model-adapter integration tests. |

### 3.4 Interaction Capability

| Subcharacteristic | Priority | Rationale | Derived test types |
| --- | --- | --- | --- |
| Appropriateness recognisability | Medium | The learner must recognize import, tree, and search as routes to studying available theory. | First-use interface review. |
| Learnability | Medium | The product organizes a learning progression, so its navigation and source cues must be understandable. | Task walkthrough with introductory path. |
| Operability | Medium | The user must navigate the tree, return to a topic location, and edit relations (REQ-005–006). | Keyboard and pointer task checks. |
| User error protection | High | A mistaken edit or cycle can damage the learning graph or source interpretation (FR-018, NFR-006). | Invalid-edit, cycle, and failed-save tests. |
| User engagement | Low | The four illustrated scenes aid progression, but their presentation is secondary to usable, faithful theory (NFR-004). | Visual legibility spot check. |
| Inclusivity | Medium | The interface must remain legible and navigable across responsive layouts (NFR-004); no broader audience requirement is specified. | Responsive and keyboard accessibility checks. |
| User assistance | Medium | Import omissions, model failures, and ambiguous questions need actionable explanations (REQ-001, REQ-007). | Error/help message review. |
| Self-descriptiveness | High | Users must distinguish sourced claims, generated examples, unknowns, and insufficient evidence without guessing (REQ-003, NFR-003). | Provenance-label and state-comprehension tests. |

### 3.5 Reliability

| Subcharacteristic | Priority | Rationale | Derived test types |
| --- | --- | --- | --- |
| Faultlessness | Medium | Repeated imports, search, and edits should work in normal single-user use. | Repeated-flow regression tests. |
| Availability | Low | A local single-user tool has no stated service-level uptime target. | Start/stop smoke check. |
| Fault tolerance | Medium | Model or index failure must leave stored knowledge usable and the error visible (FR-015, NFR-006). | Dependency-failure injection. |
| Recoverability | High | Imported documents and manual corrections must survive restart and failed operations (REQ-009, NFR-005–006). | Restart, failed-write, and reconciliation tests. |

### 3.6 Security

| Subcharacteristic | Priority | Rationale | Derived test types |
| --- | --- | --- | --- |
| Confidentiality | Medium | User-supplied study documents are intended to remain local (REQ-011, NFR-007), without an asserted regulatory classification. | Local-only processing and logging inspection. |
| Integrity | High | Source files, evidence links, and manual corrections are the knowledge authority (REQ-002–003, REQ-009). | Transaction, source-link, and malformed-input tests. |
| Non-repudiation | N/A | No signed transactions, disputed actions, or multi-party audit process is specified. | None in first version. |
| Accountability | Low | Single-user local edits have no multi-user attribution requirement, though errors must be diagnosable. | Basic operation/error logging review. |
| Authenticity | N/A | The confirmed local loopback design has no user accounts or remote identity claim. | None until access scope changes. |
| Resistance | Medium | DOCX is external input and malformed archives could disrupt local processing (NFR-002, ADD §8). | Invalid-file and extraction-limit checks. |

### 3.7 Maintainability

| Subcharacteristic | Priority | Rationale | Derived test types |
| --- | --- | --- | --- |
| Modularity | Medium | Extraction, storage, retrieval, and inference must fail independently (REQ-011, NFR-008). | Component-boundary and failure-isolation checks. |
| Reusability | Low | No reuse outside this application is required. | Incidental API review. |
| Analysability | Medium | The user needs to know which processing stage failed (FR-001, NFR-008). | Stage-specific diagnostic check. |
| Modifiability | Medium | Strategic facets and model configuration may evolve without losing existing topics (NFR-009, ADD ADR-006). | Schema/change regression tests. |
| Testability | Medium | Source fidelity and graph invariants need repeatable checks as the library grows. | Test-harness and deterministic-fixture assessment. |

### 3.8 Flexibility

| Subcharacteristic | Priority | Rationale | Derived test types |
| --- | --- | --- | --- |
| Adaptability | Medium | Classification fields and local model choices must be extensible (REQ-004, ADD ADR-006). | Added-facet and model-configuration tests. |
| Scalability | Low | Growth limits are not specified for the first single-user library. | Representative volume smoke check. |
| Installability | Medium | The first version must restart with its saved data; packaging for a particular OS is unconfirmed (REQ-009). | Clean local setup and restart check. |
| Replaceability | Low | No predecessor product or migration target has been named. | Incidental data-export design review; no dedicated replacement test. |

### 3.9 Safety

| Subcharacteristic | Priority | Rationale | Derived test types |
| --- | --- | --- | --- |
| Operational constraint | N/A | The study application does not control equipment or physical processes. | None. |
| Risk identification | N/A | No physical, health, property, or environmental hazard path is specified. | None. |
| Fail safe | N/A | No physical safe-state behavior is required. Data recovery is assessed under Reliability instead. | None. |
| Hazard warning | N/A | No physical hazard requires warning; study-evidence gaps are assessed under Interaction Capability. | None. |
| Safe integration | N/A | No safety-critical external system is integrated. | None. |

## 4. Summary — High Priority Only

| Characteristic | Subcharacteristic | Rationale | Derived test types |
| --- | --- | --- | --- |
| Functional Suitability | Functional completeness | All first-version study flows are acceptance-critical. | End-to-end acceptance and requirements coverage. |
| Functional Suitability | Functional correctness | Incorrect theory or citations mislead the learner. | Source comparison, validation, grounded-answer tests. |
| Functional Suitability | Functional appropriateness | Search and learning paths must serve the study goal. | Task-based acceptance tests. |
| Interaction Capability | User error protection | Bad edits or cycles can damage the graph. | Invalid-edit and failed-save tests. |
| Interaction Capability | Self-descriptiveness | Provenance and evidence gaps must be clear. | Provenance-label and state-comprehension tests. |
| Reliability | Recoverability | User documents and corrections must survive failures and restart. | Restart and recovery tests. |
| Security | Integrity | The stored source and its links are authoritative. | Transaction, source-link, and malformed-input tests. |

## References

- [VSD](../VSD.md), [BRD](../_specification/BRD.md), functional requirements in `../_specification/FRDs/`, and [NFRD](../_specification/NFRD.md).
- [Aelium Test Policy](Test-Policy.md) and [Test Strategy](Test-Strategy.md).
- ISO/IEC 25010:2023 product quality model, as summarized in the Qualitas reference document.
- ISO/IEC 29119-2:2021 §7.1, risk-based test planning.
