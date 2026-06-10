# Codex Handoff for LemmaForge

This document is a practical orientation note for a fresh Codex conversation. Read it together with `AGENTS.md` before making changes.

## What LemmaForge Is

LemmaForge is a local-first mathematical research workbench. Its goal is to help manage the real research process: collect fragments, organize them by topics and problems, track definitions/claims/proofs/gaps, run attempts, prepare context packs for AI discussion, and keep provenance visible.

The design center is:

- `Fragment` is the atomic knowledge unit.
- `Topic` is an area or theme.
- `ResearchProblem` is the active research unit.
- `Attempt` is one concrete try at solving or clarifying a problem.

AI is advisory and proposal-based. It may suggest fragments, relations, context ordering, problem summaries, or roles, but important writes should require user confirmation.

## Non-Negotiable Rules

Follow `AGENTS.md`.

Most important constraints:

- Do not directly mutate the user's research database except through backend services, CLI operations, migrations, or tests.
- Do not bypass Pydantic validation for `ResearchPatch`.
- Imported fragments must not be marked `stable`.
- Do not write to Zotero's SQLite database.
- Keep provenance/source information out of mathematical `Relation` rows.
- Do not introduce LangChain, Neo4j, PostgreSQL, or Electron unless the user explicitly asks.

## Tech Stack

Backend:

- FastAPI
- SQLite
- SQLAlchemy ORM
- Pydantic schemas
- Alembic migrations
- Pytest tests

Frontend:

- Vue 3
- TypeScript
- Vite
- Vue Flow for graph workspaces
- KaTeX/Markdown rendering
- `lucide-vue-next` icons

Local integrations:

- Markdown vault output for human-readable Git diffs
- Zotero Local API at `http://127.0.0.1:23119` by default
- Codex CLI bridge for AI jobs

## Repository Map

Backend:

- `backend/app/models/` - SQLAlchemy models.
- `backend/app/schemas/` - Pydantic request/response schemas.
- `backend/app/api/` - FastAPI route modules.
- `backend/app/services/` - business logic.
- `backend/app/db.py` - engine/session/init and lightweight SQLite migrations.
- `backend/alembic/versions/` - database migrations.
- `backend/tests/` - backend regression tests.

Frontend:

- `frontend/src/pages/` - main app pages.
- `frontend/src/components/` - shared Vue components.
- `frontend/src/api/client.ts` - frontend API client.
- `frontend/src/types/index.ts` - frontend type definitions.
- `frontend/src/styles.css` - global UI styling.
- `frontend/src/utils/texMarkdown.ts` - TeX/Markdown rendering helpers.

Docs and control files:

- `AGENTS.md` - hard rules for agents.
- `docs/baseline_audit.md` - baseline audit from Milestone 0.
- `lemmaforge_milestone_roadmap_for_codex.md` - long-term roadmap.
- `.codex/skills/research-import/SKILL.md` - skill prompt for AI import patches.
- `schemas/research_patch.schema.json` - JSON schema for AI import patches.

## Core Domain Concepts

### Fragment

A fragment is a mathematical unit: definition, theorem, proposition, proof sketch, construction, remark, question, conjecture, notation, or context note.

Important fields include:

- `type`
- `title`
- `status`
- `body`
- `topic_id`
- `origin_classification`
- `exactness`

Review status is not mathematical truth. A later milestone may introduce separate claim-truth status.

### Relation

Relations are mathematical graph edges between fragments. The current compact relation set is:

- `depends_on`
- `proof_of`
- `refines`
- `replaces`
- `contradicts`
- `generalizes`
- `is_example_of`
- `is_counterexample_to`
- `uses_notation`
- `questions`
- `compares_with`
- `inspired_by`

Do not reintroduce provenance relations such as `quotes`, `cites`, `paraphrases`, or `came_from` into active relations.

### Source and SourcePointer

Sources represent literature or external material. Source pointers attach provenance to fragments. Zotero sync reads Zotero through the Local API and creates/updates LemmaForge `Source` records only.

### Topic

Topics are broad areas. Topic pages use a graph workspace for fragments and relations, plus context pack building.

### ResearchProblem

Problems sit above topics. A problem can link to multiple topics and multiple fragments. Problem-fragment links have roles such as main question, candidate definition, claim, proof, example, gap, notation, background, and so on. These links are organizational metadata, not mathematical relations.

### Attempt

Attempts belong to a problem and represent a concrete strategy or try. Attempt-fragment links have roles such as input, assumption, produced, blocked_by, refuted_by, needs_revision, motivated, and other.

### Context Pack

Context packs prepare selected fragments for AI discussion or writing. AI can suggest selection/order/reasons, but exported prompt content should preserve the original fragment bodies rather than rewriting mathematics.

### Import and AI Jobs

AI import turns pasted text into a validated `ResearchPatch` proposal. Users choose what to save as drafts and which proposed relations to apply. Longer AI actions run as background jobs and should be visible through global AI logs.

## Current Milestone Status

Completed before this handoff:

- Baseline audit and tests.
- Compact relation system and migration from legacy relation kinds.
- Zotero Local API bridge.
- AI import and AI-assisted topic context packs.
- Dense dashboard UI and graph workspaces.
- `ResearchProblem` model and Problem Workspace.
- `Attempt` model and Attempt Workspace.
- Milestone 2.1 stabilization work is implemented in the working tree.

Current working tree includes uncommitted Milestone 2.1 changes:

- `backend/alembic/versions/0006_research_problems.py`
- `backend/app/api/attempts.py`
- `backend/app/models/__init__.py`
- `backend/app/models/problem.py`
- `backend/app/schemas/problem.py`
- `backend/app/services/attempt_service.py`
- `backend/app/services/problem_service.py`
- `backend/tests/test_problems.py`
- `frontend/src/api/client.ts`
- `frontend/src/pages/AttemptDetail.vue`
- `frontend/src/pages/ProblemDetail.vue`
- `frontend/src/styles.css`
- `frontend/src/types/index.ts`

Those changes add Attempt graph layout persistence, graph controls, edge visibility toggles, improved auto arrange, selected-problem-fragments-to-attempt creation, and related tests.

Latest verification after Milestone 2.1:

- `pytest backend/tests` passed: 61 tests.
- `cd frontend && npm run build` passed.
- `git status --short --branch` showed only source/test files listed above; no vault or database output was mixed in.

## Common Commands

Backend tests:

```powershell
pytest backend/tests
```

Focused problem/attempt tests:

```powershell
pytest backend/tests/test_problems.py
```

Frontend build:

```powershell
cd frontend
npm run build
```

Check status:

```powershell
git status --short --branch
```

## Development Style Notes

- Prefer existing service/API/schema patterns over inventing new abstractions.
- Add backend tests when touching data models, services, migrations, import, relation validation, Zotero, or AI job behavior.
- Use `apply_patch` for manual code edits.
- Keep UI dense and workbench-like, with light glass styling as the current visual direction.
- Use existing animation classes such as `modal-fade`, `drawer-fade`, `popover`, `collapse`, and `tab-fade`.
- Use `lucide-vue-next` icons for interactive controls.
- Keep graph edges readable. Topic, Problem, and Attempt graph pages use dynamic handles so each edge chooses the best side based on node positions.

## Recent UI/UX Direction

The user likes:

- Dense dashboard/admin-workbench layouts.
- Light glass UI, mostly light mode, dark mode usable.
- Graph-first research workspaces.
- Floating inspectors and panels instead of crowded permanent sidebars.
- Clear icons, compact tables, and visible status chips.
- TeX rendered by default, raw text shown only when editing.

The user dislikes:

- Sparse pages.
- Crowded toolbars that overflow.
- Dropdowns with too many relation kinds.
- AI results disappearing after navigation.
- Hidden or non-obvious discard/clear actions.
- Rigid graph connectors.

## Likely Next Work

The roadmap after Milestone 2.1 likely continues toward making `Problem` and `Attempt` more research-process aware. Candidate next milestones:

1. Attempt workflow deepening:
   - timeline view
   - notes/results tabs
   - produced fragments workflow
   - blocking issue review

2. AI assistant for attempts:
   - proposal-only attempt summaries
   - suggested next steps
   - gap detection
   - selected-fragment role suggestions

3. Problem-aware context packs:
   - start context pack from a problem or attempt
   - preserve problem objective and attempt strategy in prompt
   - keep fragment text unchanged

4. Research task board:
   - tasks generated from gaps and next steps
   - status tracking
   - link tasks to problem/attempt/fragments

5. Claim status / mathematical truth tracking:
   - separate from fragment review status
   - track conjectural, needs verification, proof sketch, proved, false

Do not jump ahead without the user's confirmation.

## Starting a Fresh Codex Conversation

Suggested first message for a new conversation:

```text
Please read AGENTS.md and docs/codex_handoff.md first, then continue LemmaForge development from the current working tree.
```

If continuing from a specific milestone, also mention the milestone name and whether the current working tree should be treated as already reviewed.
