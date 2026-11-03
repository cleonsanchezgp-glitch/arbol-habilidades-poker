qualitas:handoff 2026-11-03 rector

Anchor: INI-001 / PRJ-001 — migrate local development Planning and Time to GitHub tasks
Repo: cleonsanchezgp-glitch/arbol-habilidades-poker · master · C:\Users\Usuario\Documents\empresa\repositorios\arbol-habilidades-poker
Findings:
- The target has no `_context/MANAGEMENT-MODEL.yaml`; the audited backward-compatible authority remains classic + Markdown for Planning and Time.
- The owner confirmed the mapping INI-001 → PRJ-001 → WP-001..006 → TSK-001..018 and authorized an Issues-only migration plus undated MS-001 while a dedicated Project is unavailable.
- GitHub REST verification on 2026-11-03 found 26 unique canonical Issues (#1..#26), all attached to milestone #1, and 25 parent/sub-issue links. The milestone has no due date. Source statuses and requirement links are in issue bodies; the Issues remain open.
- Existing user Projects #3, #4, and #5 contain unrelated repository work. GitHub's selected REST API does not offer creating a new Project. No Project fields/items/views were created, and GitHub was not declared authoritative.
- `_context/TRACEABILITY-MATRIX.md` still projects the unchanged authoritative Markdown planning and is not stale from this Issues-only copy.
- Documentation snapshot refreshed at 2026-11-03T19:07:52.497Z, showing 13/13 applicable document groups present and Markdown Planning/Time authority.
Decisions:
- Preserve local planning files and management authority until a dedicated GitHub Project exists and its hierarchy, fields and items can be reconciled.
Uncommitted:
- This handoff and the refreshed `docs/qualitas/documentation-status.html` are local changes from this session.
- `_context/handoffs/2026-11-02-github-planning-migration.md` and `scripts/migrate-planning-github.py` predated this session; preserve them.
Next: $qualitas:qualitas continue the GitHub Planning migration for cleonsanchezgp-glitch/arbol-habilidades-poker at C:\Users\Usuario\Documents\empresa\repositorios\arbol-habilidades-poker; read _context/handoffs/2026-11-03-github-planning-issues.md, obtain the dedicated user-owned Project number after its creation, then route Rector to reconcile Project fields/items/views and declare GitHub Planning/Time authority only after verification.
Pending:
1. Create a dedicated GitHub Project through a supported operation outside Rector's REST-only creation path and record its number.
2. Reconcile all 26 Issues as Project items with canonical ID, status, requirement, horizon and PRJ lineage fields; inspect the available view state separately.
3. Declare the GitHub backend in `_context/MANAGEMENT-MODEL.yaml` only after the live Project is verified; refresh traceability and documentation status then.
