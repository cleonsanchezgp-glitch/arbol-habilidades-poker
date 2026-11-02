## Title

| Field | Value |
| --- | --- |
| Document | Vision and Scope Document — Texas Hold'em Theory Knowledge Tree |
| Initiative | Organize and study Mentopoker theory |
| Version | 0.1 |
| Status | Draft - for review |
| Author | Consultor, based on the user's project brief |
| Reviewers | Project owner |
| Organization | Aelium |
| Repository Type | Software Product |
| Last Updated | 2026-10-31 |

## 1. Vision

Build a local application that turns Texas Hold'em poker theory supplied by the user as DOCX documents into a navigable learning tree. Foundational concepts appear first, with more specialized strategies further down. The user can also ask natural-language questions and receive explanations grounded in the imported material, with links back to topics and source documents.

## 2. Problem Statement

The user's Mentopoker Texas Hold'em theory is collected in documents that are difficult to browse as a learning progression or search by an informal description of a situation. One document can cover several topics, and strategic advice depends on conditions such as position, stack depth, prior actions, and board texture. A study tool must preserve those conditions while making the material easier to find and understand.

## 3. Business Opportunity

Organizing the existing material into distinct, source-linked topics can reduce the effort of finding relevant theory and help the user study concepts in a useful order. This is a personal study and knowledge-organization outcome; the brief does not establish a commercial objective.

## 4. Stakeholders

| Stakeholder | Role | Interest |
| --- | --- | --- |
| Project owner and learner | Imports, reviews, edits, and studies theory | Clear learning progression, faithful explanations, useful search, durable data |
| Aelium | Product organization | A maintainable local application consistent with its test policy and strategy |

Mentopoker is identified as the source of the user's study documents. No direct role for the school in this project has been established.

## 5. Product Scope

The first functional version focuses on Texas Hold'em and will:

- Import DOCX files, show processing status and errors, and extract text, tables, and images where technically possible.
- Identify one or more topics per document; store structured explanations, relevant conditions, examples, classification, difficulty, prerequisites, and source references.
- Distinguish source-backed statements from generated teaching examples, expose missing information or conflicting documents, and avoid unsupported strategic numbers or conclusions.
- Arrange topics in a descending learning tree with meaningful, acyclic prerequisite relationships; allow topics to relate to multiple branches without duplicating their content.
- Let the user inspect and correct topic content, classification, placement, and dependencies, and return from a topic to its position in the tree.
- Support natural-language retrieval over imported material, source-grounded answers, related-topic links, and learning paths ordered by prerequisites. Ask for clarification when an ambiguity materially affects an answer.
- Detect repeated imports and similar existing theory for review, preserve documents, topics, and relationships across restarts, and keep a link to each original document.
- Use a locally executed AI model connected to retrieval over imported content. Document extraction, persistent storage, indexing/retrieval, and model inference are separate responsibilities.

The product is an organization and study tool. It will not present retrieved explanations as solver output or claim mathematical precision that the documents do not support. The brief does not require a specific deployment platform, local model, database, or visual format for every topic. The `poker-roots-boceto/poker-roots/` static prototype is a visual reference, not a source of poker theory or a finished application.

## 6. Objectives

| ID | Objective | Success Metric | Target |
| --- | --- | --- | --- |
| OBJ-001 | Turn user-supplied DOCX theory into reviewable, structured topics | An import produces topics with source links, and processing state and errors are visible | A DOCX containing multiple identifiable topics can produce more than one topic; imported material remains available after restart |
| OBJ-002 | Preserve strategic meaning and provenance | Explanations retain documented conditions and distinguish sourced claims from generated examples | Unsupported frequencies, ranges, bet sizes, and conclusions are not presented as sourced facts; missing or contradictory information is visible |
| OBJ-003 | Support a coherent learning progression | Topics have difficulty and editable, acyclic prerequisite links, and can be found in the tree | Basic topics appear above dependent advanced topics; a topic can relate to multiple branches without content duplication |
| OBJ-004 | Help the user find theory using informal language | Queries retrieve relevant imported topics and source-grounded explanations | A query such as “BB vs BTN en flop Axx” returns applicable available material or clearly states what context or content is missing |
| OBJ-005 | Recommend an achievable study sequence | Suggested topics come from available content and respect prerequisites | An introductory request yields a navigable sequence with a short reason for each recommendation |
| OBJ-006 | Keep the knowledge base correctable and durable | The user can edit topics and relationships and revisit original documents | Corrections and document/topic relationships survive an application restart |

## 7. Constraints

- The AI model must execute locally and use retrieval over imported documents for knowledge-grounded responses.
- Texas Hold'em is the poker modality in scope. Ollama, if used, is local AI runtime software and is not a poker modality.
- Source documents remain the primary knowledge authority; generated examples must be identified as such.
- Unknown strategic context must remain unknown rather than being inferred as fact.
- Topic dependencies must be pedagogically justified and cycle-free; difficulty and prerequisite relationships are separate.
- Storage must persist imported documents, processed topics, classifications, and relationships across restarts.
- The repository contains a static HTML/CSS/JavaScript interface prototype with four illustrated scenes and sample tree data. Its visuals and interaction patterns can be adapted; its sample poker explanations are not imported theory. No backend or persistent application architecture exists yet.
- The DOCX extraction capability for images and tables may be limited by document structure; failures or omissions must be visible to the user.
- The location and packaging of the final application have not been specified.

## References

- User's project brief in this conversation, 2026-10-31.
- `poker-roots-boceto/poker-roots/README.md`, `index.html`, `styles.css`, `app.js`, and illustrated assets, added 2026-10-31.
- Aelium Organizational Test Policy, QA-POL-001 v1.0, and Organizational Test Strategy, QA-STR-001 v1.0, copied from the user-designated CRM reference.
- ISO/IEC/IEEE 29148:2018, Requirements Engineering.
