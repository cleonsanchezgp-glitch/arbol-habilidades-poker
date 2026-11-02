import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const context = join(root, '_context');
const read = (path) => readFileSync(join(context, path), 'utf8');
const section = (body, start, end) => {
  const after = body.split(start)[1];
  if (!after) throw new Error(`Missing section: ${start}`);
  return end ? after.split(end)[0] : after;
};
const rows = (body, pattern) => [...body.matchAll(pattern)];
const ids = (value, prefix) => [...value.matchAll(new RegExp(`${prefix}-\\d{3}`, 'g'))].map((match) => match[0]);
const unique = (values) => [...new Set(values)].sort();
const escape = (value) => String(value ?? '').replaceAll('|', '\\|').replaceAll('\n', ' ').trim();

const vsd = read('VSD.md');
const brd = read('_specification/BRD.md');
const nfrd = read('_specification/NFRD.md');
const add = read('_design/ADD.md');
const tmp = read('_verification/TMP.md');
const frdDir = join(context, '_specification', 'FRDs');
const frds = readdirSync(frdDir).filter((name) => name.endsWith('.md')).map((name) => read(`_specification/FRDs/${name}`));
const wpDir = join(context, '_planning');
const workPackages = readdirSync(wpDir).filter((name) => /^WP-\d{3}.*\.md$/.test(name)).map((name) => [name, read(`_planning/${name}`)]);

const entities = new Map();
const addEntity = (id, type, description, parents = []) => {
  if (entities.has(id)) throw new Error(`Duplicate entity: ${id}`);
  entities.set(id, { id, type, description, parents: unique(parents), decisions: [], work: [], tests: [], evidence: [], status: '' });
};

for (const match of rows(vsd, /^\| (OBJ-\d{3}) \| ([^|]+) \|/gm)) addEntity(match[1], 'Objective', match[2]);
for (const match of rows(section(brd, '## 4. Business Requirements', '## 5.'), /^\| (REQ-\d{3}) \| ([^|]+) \| [^|]+ \| ([^|]+) \|/gm)) addEntity(match[1], 'Requirement', match[2], ids(match[3], 'OBJ'));
for (const frd of frds) {
  for (const match of rows(section(frd, '## 3. Functional Requirements', '## 4.'), /^\| (FR-\d{3}) \| ([^|]+) \| [^|]+ \| ([^|]+) \|/gm)) addEntity(match[1], 'FR', match[2], ids(match[3], 'REQ'));
  for (const match of rows(section(frd, '## 7. Acceptance Criteria', '## 8.'), /^\| (AC-\d{3}) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/gm)) addEntity(match[1], 'AC', `${match[3].trim()} → ${match[4].trim()}`, ids(match[5], 'FR'));
}
for (const match of rows(nfrd, /^\| (NFR-\d{3}) \| ([^|]+) \| [^|]+ \| ([^|]+) \| [^|]+ \|/gm)) addEntity(match[1], 'NFR', match[2], ids(match[3], 'REQ'));
for (const match of rows(section(nfrd, '## 10. Acceptance Criteria', '## References'), /^\| (AC-\d{3}) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/gm)) addEntity(match[1], 'AC', `${match[3].trim()} → ${match[4].trim()}`, ids(match[5], 'NFR'));

const decisionSection = section(add, '## 10. Requirements Addressed');
const decisions = new Set(ids(section(add, '## 9. Architecture Decisions', '## 10.'), 'ADR'));
const dangling = [];
const attach = (target, kind, value) => {
  const entity = entities.get(target);
  if (!entity) dangling.push(`${kind} ${value} → ${target}`);
  else entity[kind].push(value);
};
for (const match of rows(decisionSection, /^\| (ADR-\d{3}) \| ([^|]+) \|/gm)) {
  if (!decisions.has(match[1])) dangling.push(`Unknown decision ${match[1]}`);
  for (const target of ids(match[2], '(?:REQ|FR|NFR)')) attach(target, 'decisions', match[1]);
}

const orphanWork = [];
const allTasks = [];
for (const [name, body] of workPackages) {
  const wp = name.match(/WP-\d{3}/)[0];
  const realizes = unique(ids(section(body, '## 3. Realizes', '## 4.'), '(?:FR|NFR)'));
  if (!realizes.length) orphanWork.push(wp);
  for (const target of realizes) attach(target, 'work', wp);
  allTasks.push(...ids(section(body, '## 4. Tasks', '## 5.'), 'TSK'));
}

const testRows = rows(section(tmp, '## 10. Traceability', '## References'), /^\| ((?:FR|NFR)-\d{3}) \| (TEST-\d{3})[^|]* \| ([^|]+) \| ([^|]+) \|/gm);
const testToRequirements = new Map();
for (const match of testRows) {
  const [target, test, evidence, status] = [match[1], match[2], match[3].trim(), match[4].trim()];
  attach(target, 'tests', test);
  if (!testToRequirements.has(test)) testToRequirements.set(test, new Set());
  testToRequirements.get(test).add(target);
  const entity = entities.get(target);
  if (entity) {
    if (evidence !== 'Pending' && evidence !== '—' && evidence !== '-') entity.evidence.push(...ids(evidence, 'EVD'));
    entity.status = status;
  }
}

for (const entity of entities.values()) for (const parent of entity.parents) if (!entities.has(parent)) dangling.push(`${entity.id} → missing parent ${parent}`);
const orphans = [...entities.values()].filter((entity) => entity.type !== 'Objective' && entity.parents.length === 0).map((entity) => entity.id);
const unimplemented = [...entities.values()].filter((entity) => ['FR', 'NFR'].includes(entity.type) && entity.work.length === 0).map((entity) => entity.id);
const untested = [...entities.values()].filter((entity) => ['FR', 'NFR'].includes(entity.type) && entity.tests.length === 0).map((entity) => entity.id);
const unevidenced = [...testToRequirements.keys()].filter((test) => ![...entities.values()].some((entity) => entity.tests.includes(test) && entity.evidence.length));
const orphanTests = [...testToRequirements].filter(([, targets]) => ![...targets].some((target) => entities.has(target))).map(([test]) => test);
const typeOrder = { Objective: 0, Requirement: 1, FR: 2, NFR: 3, AC: 4 };
const sorted = [...entities.values()].sort((a, b) => typeOrder[a.type] - typeOrder[b.type] || a.id.localeCompare(b.id));
const cell = (values) => unique(values).join(', ');
const matrix = sorted.map((entity) => `| ${entity.id} | ${entity.type} | ${escape(entity.description)} | ${cell(entity.parents)} | ${cell(entity.decisions)} | ${cell(entity.work)} | ${cell(entity.tests)} | ${cell(entity.evidence)} | ${entity.status} |`).join('\n');
const report = (values) => values.length ? values.join(', ') : 'None';
const currentDate = new Date().toISOString().slice(0, 10);

const output = `## Title

| Field | Value |
| --- | --- |
| Document | Requirements Traceability Matrix — Texas Hold'em learning library |
| Initiative | INI-001 / PRJ-001 |
| Version | 0.1 |
| Status | Derived projection - for review |
| Author | Vestigator (generated from authoritative Markdown) |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | ${currentDate} |

## 1. Purpose

This matrix projects relationships from the project's Specification, Design, Planning, Time, and Verification documents. It is not the authority for their content or execution status. No \`_context/MANAGEMENT-MODEL.yaml\` exists, so the backward-compatible \`classic\` vocabulary and Markdown authorities are assumed. Verification execution is external; all linked tests are currently \`Not Run\` and have no evidence.

Source counts: ${sorted.filter((x) => x.type === 'Objective').length} objectives, ${sorted.filter((x) => x.type === 'Requirement').length} business requirements, ${sorted.filter((x) => x.type === 'FR').length} functional requirements, ${sorted.filter((x) => x.type === 'NFR').length} quality requirements, ${sorted.filter((x) => x.type === 'AC').length} acceptance criteria, ${decisions.size} decisions, ${workPackages.length} work packages, ${allTasks.length} tasks, and ${testToRequirements.size} planned tests. Roadmap authority: \`_context/_time/ROADMAP.md\`, horizon H-001 and milestone MS-001, with no committed date.

## 2. ID Prefix Registry

The selected \`classic\` profile uses these identifiers. The target does not declare migration aliases.

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
${matrix}

## 4. Gap Checklist

| # | Check | Current finding |
| --- | --- | --- |
| 1 | Requirement with no implementation | ${report(unimplemented)} |
| 2 | Requirement with no test | ${report(untested)} |
| 3 | Orphan task | ${orphanWork.length ? `Tasks in work packages lacking Realizes: ${report(orphanWork)}` : 'None; all task-bearing work packages have a Realizes relation.'} |
| 4 | Requirement modified after verification | Unknown; no execution evidence or trustworthy evidence dates exist. |
| 5 | NFR with no evidence | All ${sorted.filter((x) => x.type === 'NFR').length} NFRs; tests are Not Run. |
| 6 | Work closed but requirement still open | None; no Work Package is marked Done. |

Additional bidirectional findings:

- Dangling references: ${report(unique(dangling))}.
- Orphan entities lacking upstream justification: ${report(orphans)}.
- Orphan Work Packages: ${report(orphanWork)}.
- Unimplemented FR/NFR requirements: ${report(unimplemented)}.
- Untested FR/NFR requirements: ${report(untested)}.
- Unevidenced tests: ${unevidenced.length} of ${testToRequirements.size} (${report(unevidenced)}); expected while Not Run, but no verified status is supported.
- Orphan tests: ${report(orphanTests)}.
- Stale verification: unknown because no execution evidence exists.

## References

- \`_context/VSD.md\`, \`_context/_specification/BRD.md\`, \`_context/_specification/FRDs/*.md\`, and \`_context/_specification/NFRD.md\` — Specification.
- \`_context/_design/ADD.md\` — Design.
- \`_context/_planning/INI-001-texas-holdem-learning-library.md\`, \`PRJ-001-local-mvp.md\`, and \`WP-*.md\` — Planning.
- \`_context/_time/ROADMAP.md\` — Time.
- \`_context/_verification/TMP.md\` — Verification definition; execution evidence remains external.
`;

writeFileSync(join(context, 'TRACEABILITY-MATRIX.md'), output, 'utf8');
process.stdout.write(JSON.stringify({ rows: sorted.length, byType: Object.fromEntries(Object.keys(typeOrder).map((type) => [type, sorted.filter((entity) => entity.type === type).length])), decisions: decisions.size, workPackages: workPackages.length, tasks: allTasks.length, tests: testToRequirements.size, dangling: unique(dangling), orphans, unimplemented, untested, unevidenced: unevidenced.length, orphanTests }, null, 2) + '\n');
