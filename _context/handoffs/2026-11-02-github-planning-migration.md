qualitas:handoff 2026-11-02 qualitas

Anchor: INI-001 / PRJ-001 — review the whole project and migrate local Planning and Time to GitHub
Repo: cleonsanchezgp-glitch/arbol-habilidades-poker · master · C:\Users\Usuario\Documents\empresa\repositorios\arbol-habilidades-poker
Findings:
- `_context/MANAGEMENT-MODEL.yaml` is absent; classic vocabulary and Markdown Planning/Time are the current defaults.
- Local sources contain INI-001, PRJ-001, WP-001..006, TSK-001..018, H-001 and undated MS-001.
- The documentation snapshot reports 13/13 applicable groups present; conformance, approval and provenance were not assessed.
- `python -m unittest discover -s tests -v` passed 11 tests. TMP traceability still marks planned tests Not Run without execution evidence.
- GitHub repository has no issues or milestones. The authenticated `GITHUB_TOKEN` can identify the owner but Projects REST returns 403 `Resource not accessible by personal access token`; `qualitas_token` is not visible in Process, User or Machine environment. Runners REST also returns 403.
Pending confirmations:
- Confirm interpretation: INI and PRJ as parent issues, six WPs as descendants, 18 TSKs as WP sub-issues, MS-001 as an undated milestone; preserve status and requirement links.
- Provide a token available to this process with Issues and Projects permissions, or explicitly choose an issues-only migration.
Uncommitted:
- `_context/handoffs/2026-11-02-github-planning-migration.md` created in this session.
Next: $qualitas:qualitas continue the review and GitHub migration for arbol-habilidades-poker; read this handoff, obtain the pending mapping and access decisions, inspect GitHub live state, then follow Rector's REST migration workflow and refresh traceability and documentation status.
Pending:
1. Reconcile live Project and issue state without duplicating canonical IDs.
2. Migrate and verify hierarchy, fields, milestone and links; declare GitHub Planning/Time authority only after successful reconciliation.
3. Refresh the matrix and documentation status snapshot, and report remaining CI runner and draft-document findings.
