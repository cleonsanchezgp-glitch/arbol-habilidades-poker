## Document Control

| Field | Value |
| --- | --- |
| Requirement Name | Classification and learning tree |
| ID | FRD-TREE |
| Version | 0.1 |
| Author | Consultor |
| Last Updated | 2026-10-31 |

## 1. Overview

Classify imported topics by strategic context and display a descending, editable progression of learning.

## 2. Actors

| Actor | Description |
| --- | --- |
| User | Explores and corrects the tree. |
| System | Proposes classifications and maintains valid relations. |

## 3. Functional Requirements

| ID | Description | Priority | Traces to (REQ-xxx) |
| --- | --- | --- | --- |
| FR-007 | Record extensible strategic facets including street, positions, pot type, in/out of position, board texture, and concept; leave unsupported facets unknown. | Must | REQ-004 |
| FR-008 | Assign basic, intermediate, or advanced difficulty independently of prerequisites and propose only pedagogically justified prerequisite links. | Must | REQ-004 |
| FR-009 | Reject any prerequisite change that would create a cycle and permit one topic to connect to several branches without duplicating its content. | Must | REQ-004 |
| FR-010 | Display a descending learning tree with difficulty, prerequisites, topic navigation, and a route back from a topic to its tree location. | Must | REQ-005 |

## 4. Workflow

1. The system proposes facets, difficulty, and prerequisites for new topics.
2. It validates prerequisite relations for cycles.
3. The tree places fundamentals above dependent and more complex material.
4. The user opens a topic, inspects its context, and returns to its tree location.

## 5. Inputs

| Input | Source |
| --- | --- |
| Topic content and source context | Imported knowledge |
| Manual relation corrections | User |

## 6. Outputs

| Output | Destination |
| --- | --- |
| Facets, difficulty, prerequisites | Persistent topic store |
| Descending tree and topic location | User interface |

## 7. Acceptance Criteria

| ID | Given | When | Then | Verifies |
| --- | --- | --- | --- | --- |
| AC-007 | A source names BTN and BB but omits pot type | Classification runs | Positions are recorded and pot type remains unknown | FR-007 |
| AC-008 | Two intermediate topics have a real learning dependency | They are classified | They may share difficulty while one is recorded as prerequisite of the other | FR-008 |
| AC-009 | A proposed link would complete a cycle | It is submitted | The link is rejected and the existing graph is preserved | FR-009 |
| AC-010 | A topic belongs to multiple branches | The tree is shown | Branches link to the same topic record | FR-009 |
| AC-011 | A user opens a topic from the tree | The user requests its location | The tree focuses or reveals the topic's position | FR-010 |

## 8. Error Handling

Unsupported classification values remain unknown. An invalid prerequisite edit explains the cycle and preserves the prior relation set. An empty tree displays a clear import prompt.

## 9. Interface Requirements *(optional — only when this feature exposes or consumes an explicit interface contract, e.g. API, event, file format)*

No external interface contract is specified for this feature.

## References

- [Business Requirements Document](../BRD.md).
