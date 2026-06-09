# LemmaForge Roadmap Prompt for Codex

You are working on **LemmaForge**, a local-first mathematical research knowledge workbench.

The current system already has a usable baseline:

- fragment management
- topic graph
- relation graph
- source/Zotero integration
- AI import from natural-language excerpts
- review queue
- rejected fragments
- context pack builder
- local SQLite database
- Markdown vault
- local-first status indicators
- AI jobs

The next goal is to evolve LemmaForge from a **fragment manager** into a **mathematical research process manager**.

The central design shift is:

> Fragment is the atomic knowledge unit, but Problem is the research unit.

A real mathematical research workflow is not merely:

```text
collect fragments
```

It is closer to:

```text
read literature
→ formulate a problem
→ propose definitions
→ try constructions
→ state claims
→ attempt proofs
→ find gaps
→ search for examples/counterexamples
→ revise definitions
→ inspect affected downstream nodes
→ stabilize results
→ export context for AI discussion or writing
```

Implement the following milestones in order. Do not jump ahead. Each milestone should be independently useful and should preserve existing functionality.

---

## Global Design Principles

### 1. Local-first

LemmaForge should remain local-first.

Use local storage, local SQLite, local Markdown vault, local Zotero access, and local AI job orchestration where applicable.

Do not introduce cloud-first assumptions.

### 2. Proposal-based AI

Codex must not directly change stable mathematical knowledge.

AI-generated output should be one of:

- proposed fragment
- proposed relation
- proposed source pointer
- proposed problem summary
- proposed attempt
- proposed impact report
- proposed context pack
- proposed warning
- proposed task

The user must confirm before important writes.

### 3. Separate database review status from mathematical truth status

Fragment review status is not the same as mathematical validity.

For example:

```text
fragment.status = draft / candidate / working / stable / rejected
claim_status = stated / conjectural / proof_sketch / needs_verification / proved / false
```

Never conflate these.

### 4. Keep provenance separate from mathematical relations

Source/provenance relations such as citation, quote, paraphrase, and import origin should live in `source_pointers` or import provenance metadata, not in the ordinary mathematical relation graph.

### 5. Do not re-expand relation enum unnecessarily

The core relation set should remain compact:

```text
depends_on
proof_of
refines
replaces
contradicts
generalizes
is_example_of
is_counterexample_to
uses_notation
questions
compares_with
inspired_by
```

UI may display inverse labels, but the database should store canonical directional relations only.

---

# Milestone 0 — Baseline Audit and Stabilization

## Goal

Before adding new abstractions, audit the existing system and stabilize the current baseline.

## Tasks

1. Review current models:
   - Fragment
   - Relation
   - Source
   - SourcePointer
   - Topic
   - ContextPack
   - AIJob
   - Review Queue
   - Import batch or patch model

2. Confirm relation enum is compact and source/provenance relations are not mixed into the mathematical relation dropdown.

3. Confirm AI import:
   - extracts fragments
   - extracts relation proposals
   - extracts source pointers
   - attaches warnings
   - does not mark fragments as stable
   - does not write directly to stable data

4. Confirm context packs export selected fragments without rewriting mathematical content.

5. Add or update tests for:
   - importing ResearchPatch
   - rejecting invalid statuses
   - relation proposal validation
   - source pointer validation
   - Markdown vault generation
   - basic context pack export

## Acceptance Criteria

- Existing app starts successfully.
- Fragment CRUD still works.
- Import workflow still works.
- Topic graph still renders.
- Context pack export still works.
- No regression in Zotero/source handling.
- Tests pass.

---

# Milestone 1 — ResearchProblem Model and Problem Workspace

## Goal

Introduce `ResearchProblem` as the central research unit above fragments and topics.

A Topic is a subject area. A Problem is a concrete mathematical objective.

Example:

```text
Topic:
  Q-canonical extension

Problem:
  Find the correct enriched compactness condition for Q-canonical extensions.
```

## Data Model

Add `ResearchProblem`.

Suggested fields:

```ts
type ResearchProblem = {
  id: string;
  title: string;

  status:
    | "open"
    | "active"
    | "blocked"
    | "partially_solved"
    | "solved"
    | "abandoned";

  objective: string;
  current_formulation: string | null;
  motivation: string | null;
  why_it_matters: string | null;

  created_at: string;
  updated_at: string;
};
```

Add many-to-many relation between problems and topics:

```ts
type ProblemTopicLink = {
  problem_id: string;
  topic_id: string;
};
```

Add many-to-many relation between problems and fragments:

```ts
type ProblemFragmentLink = {
  id: string;
  problem_id: string;
  fragment_id: string;

  role:
    | "main_question"
    | "active_definition"
    | "candidate_definition"
    | "claim"
    | "proof"
    | "example"
    | "counterexample"
    | "background"
    | "source_note"
    | "gap"
    | "result"
    | "notation"
    | "other";

  note: string | null;
  created_at: string;
};
```

A fragment may belong to multiple problems with different roles.

## Backend

Add API endpoints:

```text
GET    /api/problems
POST   /api/problems
GET    /api/problems/{id}
PATCH  /api/problems/{id}
DELETE /api/problems/{id}

GET    /api/problems/{id}/fragments
POST   /api/problems/{id}/fragments
PATCH  /api/problems/{id}/fragments/{link_id}
DELETE /api/problems/{id}/fragments/{link_id}
```

## UI

Add a new sidebar item:

```text
Problems
```

Add:

1. Problems list page
2. Problem detail page / Problem Workspace
3. Problem creation/edit dialog
4. Fragment-to-problem linking UI

## Problem Workspace Layout

Use a layout like:

```text
Top:
  Problem title, status, objective

Left:
  Current formulation
  Active definitions
  Active claims
  Key sources
  Main question

Center:
  Problem graph or timeline area

Right:
  Open gaps
  tasks
  AI suggestions
  context pack button

Bottom or drawer:
  related fragments
  context pack builder
```

## Codex Participation

Add AI job type:

```text
problem_summary
```

Codex should be able to read selected topic fragments and propose:

```json
{
  "title": "...",
  "objective": "...",
  "current_formulation": "...",
  "motivation": "...",
  "suggested_fragment_roles": [...],
  "open_gaps": [...],
  "warnings": [...]
}
```

This is only a proposal. The user must confirm before creating/updating a Problem.

## Acceptance Criteria

- User can create, edit, and delete a ResearchProblem.
- User can link fragments to a problem with roles.
- Problem Workspace displays grouped fragments by role.
- Codex can propose a problem summary from selected fragments or a topic.
- User can accept/edit/reject the proposed problem summary.
- Existing Topic pages continue to work.

---

# Milestone 2 — Attempt Model and Attempt Timeline

## Goal

Introduce `Attempt` to record concrete research actions taken toward a problem.

Problem answers:

```text
What am I trying to solve?
```

Attempt answers:

```text
What did I try, why, and what happened?
```

Examples:

```text
Attempt:
  Try unrestricted compactness.

Result:
  Blocked, because the condition seems too strong for general quantaloids.

Produced:
  Remark: compactness may be too strong.
  Question: restrict compactness to a class Phi of weights?
```

## Data Model

Add `Attempt`.

```ts
type Attempt = {
  id: string;
  problem_id: string;

  title: string;

  status:
    | "planned"
    | "in_progress"
    | "succeeded"
    | "failed"
    | "blocked"
    | "superseded";

  strategy: string;
  expected_outcome: string | null;
  result_summary: string | null;
  failure_reason: string | null;
  next_step: string | null;

  created_at: string;
  updated_at: string;
};
```

Add `AttemptFragmentLink`.

```ts
type AttemptFragmentLink = {
  id: string;
  attempt_id: string;
  fragment_id: string;

  role:
    | "input"
    | "assumption"
    | "produced"
    | "blocked_by"
    | "motivated"
    | "refuted_by"
    | "needs_revision"
    | "other";

  note: string | null;
};
```

## Backend

Add endpoints:

```text
GET    /api/problems/{problem_id}/attempts
POST   /api/problems/{problem_id}/attempts
GET    /api/attempts/{id}
PATCH  /api/attempts/{id}
DELETE /api/attempts/{id}

GET    /api/attempts/{id}/fragments
POST   /api/attempts/{id}/fragments
PATCH  /api/attempts/{id}/fragments/{link_id}
DELETE /api/attempts/{id}/fragments/{link_id}
```

## UI

In Problem Workspace add:

1. Attempt Timeline view
2. Attempt Graph view
3. Attempt detail drawer
4. Create Attempt button
5. Link selected fragments to attempt
6. Show produced fragments and blocked-by fragments

Timeline example:

```text
2026-06-10
  Created tentative definition.

2026-06-11
  Attempted presheaf-closure construction.

2026-06-12
  Found compactness may be too strong.

2026-06-13
  Planned Phi-compactness attempt.
```

## Codex Participation

Add AI job types:

```text
attempt_suggestion
attempt_summary
```

### Attempt Suggestion

Given a problem and selected fragments, Codex proposes possible next attempts.

Output should include:

```json
{
  "attempts": [
    {
      "title": "...",
      "strategy": "...",
      "expected_outcome": "...",
      "risks": ["..."],
      "required_fragments": ["..."],
      "suggested_status": "planned"
    }
  ],
  "warnings": []
}
```

### Attempt Summary

Given an imported conversation or selected fragments, Codex proposes:

```json
{
  "title": "...",
  "strategy": "...",
  "status": "blocked",
  "result_summary": "...",
  "failure_reason": "...",
  "produced_fragment_links": [...],
  "next_step": "..."
}
```

User must confirm before creating/updating attempts.

## Acceptance Criteria

- User can create and edit attempts under a problem.
- User can link fragments to attempts with roles.
- Problem Workspace shows attempts as timeline.
- Attempt detail shows strategy, result, failure reason, produced fragments, next step.
- Codex can suggest next attempts.
- Codex can summarize an attempt from selected fragments or an import batch.

---

# Milestone 3 — Claim Status and Proof Gap Tracking

## Goal

Separate the mathematical state of a claim from the review state of a fragment.

A theorem fragment may be reviewed and clean, but mathematically still conjectural.

## Data Model

For theorem-like fragments, add optional `claim_status`.

Affected fragment types:

```text
Proposition
Lemma
Theorem
Corollary
Conjecture
```

Suggested enum:

```ts
type ClaimStatus =
  | "stated"
  | "plausible"
  | "conjectural"
  | "proof_sketch"
  | "needs_verification"
  | "proved"
  | "false"
  | "superseded";
```

Add fields:

```ts
claim_status: ClaimStatus | null;
proof_gap: string | null;
verification_notes: string | null;
```

If schema cleanliness is preferred, create a separate `ClaimMetadata` table keyed by fragment_id.

## UI

On claim fragment detail pages show:

```text
Claim status
Proof gap
Attached proof fragments
Verification notes
```

Add filters:

```text
Claims without proof
Claims with placeholder assumptions
Claims needing verification
Proved claims
False/superseded claims
```

Dashboard should show:

```text
Open claims
Claims needing proof
Claims with proof sketch only
Proved claims
```

## Codex Participation

Add AI job type:

```text
proof_gap_review
```

Given a claim fragment and its related proof fragments, Codex proposes:

```json
{
  "recommended_claim_status": "conjectural",
  "proof_gap": "...",
  "missing_assumptions": ["..."],
  "placeholder_terms": ["suitable exactness"],
  "suggested_tasks": ["formalize exactness assumptions on Q"],
  "warnings": []
}
```

Codex must not set `proved` automatically. It may recommend `proved` only if the user explicitly asks for a review of an existing complete proof, and even then it remains a proposal.

## Acceptance Criteria

- Claim fragments can store claim_status.
- Claims can be filtered by proof state.
- ProofSketch fragments can link via `proof_of`.
- Dashboard shows proof gap counts.
- Codex can propose proof gap reviews.
- User must confirm claim_status updates.

---

# Milestone 4 — Task-Specific Context Pack Templates

## Goal

Upgrade Context Packs from generic selected-fragment exports into task-specific AI context packages.

Different mathematical tasks need different context ordering.

## Context Pack Purposes

Add `purpose` to context packs:

```ts
type ContextPackPurpose =
  | "continue_chat"
  | "definition_refinement"
  | "proof_attempt"
  | "counterexample_search"
  | "literature_review"
  | "paper_writing"
  | "codex_task"
  | "seminar_preparation";
```

## Template Structures

### Definition Refinement

Export sections:

```text
Objective
Current candidate definitions
Known problems with current definitions
Design alternatives
Examples and counterexamples
Literature constraints
Open questions
Warnings
```

### Proof Attempt

Export sections:

```text
Objective
Target claim
Required definitions and notation
Known lemmas/propositions
Existing proof sketches
Open proof gaps
Forbidden assumptions
Relevant examples/counterexamples
Warnings
```

### Counterexample Search

Export sections:

```text
Objective
Target definition or claim
Known positive examples
Known negative examples
Suspicious hypotheses
Possible test domains
Open questions
Warnings
```

### Literature Review

Export sections:

```text
Objective
Sources
External definitions
External theorems
External notation
Reading notes
Open citation checks
Comparison with current project
Warnings
```

### Paper Writing

Export sections:

```text
Target section
Stable definitions
Proved claims
Proof sketches to expand
Required citations
Unstable claims excluded
Provenance warnings
```

## UI

In Context Pack Builder:

1. Add purpose selector.
2. Show purpose-specific required sections.
3. Let user include/exclude fragments.
4. Show warnings for missing required context.
5. Show stale-fragment warnings once Milestone 6 is implemented.

## Codex Participation

Add AI job type:

```text
context_pack_suggestion
```

Codex may propose:

```json
{
  "purpose": "proof_attempt",
  "selected_fragments": [...],
  "ordering": [...],
  "section_assignments": [...],
  "missing_context": [...],
  "warnings": [...]
}
```

Codex must not rewrite fragment bodies.

## Acceptance Criteria

- Context packs have a purpose.
- Export format changes according to purpose.
- User can manually override selection and order.
- Codex can suggest fragments, ordering, and warnings.
- Export preserves original mathematical content.

---

# Milestone 5 — ChangeEvent and Rule-Based Impact Reports

## Goal

Implement a general impact system for all fragment changes, not only definition lineage.

Any change to a fragment, relation, source pointer, problem, or attempt may affect downstream nodes.

## Data Model

Add `ChangeEvent`.

```ts
type ChangeEvent = {
  id: string;

  target_type:
    | "fragment"
    | "relation"
    | "source_pointer"
    | "problem"
    | "attempt"
    | "context_pack";

  target_id: string;

  change_kind:
    | "created"
    | "edited"
    | "status_changed"
    | "claim_status_changed"
    | "replaced"
    | "refined"
    | "relation_added"
    | "relation_removed"
    | "source_changed"
    | "problem_link_changed"
    | "attempt_link_changed";

  summary: string;
  before_snapshot_json: string | null;
  after_snapshot_json: string | null;

  created_by: "user" | "codex" | "system";
  created_at: string;
};
```

Add `ImpactReport`.

```ts
type ImpactReport = {
  id: string;
  change_event_id: string;

  status:
    | "proposed"
    | "accepted"
    | "dismissed"
    | "resolved";

  created_by: "system" | "codex";
  created_at: string;
};
```

Add `ImpactItem`.

```ts
type ImpactItem = {
  id: string;
  impact_report_id: string;

  target_type:
    | "fragment"
    | "problem"
    | "attempt"
    | "context_pack";

  target_id: string;

  impact_kind:
    | "possibly_invalid"
    | "needs_review"
    | "needs_restatement"
    | "proof_may_break"
    | "source_may_be_wrong"
    | "context_pack_stale"
    | "probably_unchanged";

  reason: string;
  confidence: number;

  status:
    | "open"
    | "accepted"
    | "dismissed"
    | "resolved";
};
```

## Rule-Based Impact Engine

Implement deterministic rules first.

Examples:

### If fragment A changed

Find all fragments B such that:

```text
B depends_on A
B uses_notation A
B questions A
B generalizes A
B is_example_of A
B is_counterexample_to A
```

Mark them `needs_review`.

### If claim C changed

Find proofs P such that:

```text
P proof_of C
```

Mark P `proof_may_break`.

### If notation N changed

Find fragments F such that:

```text
F uses_notation N
```

Mark F `needs_review`.

### If a fragment in a context pack changed

Mark the context pack `context_pack_stale`.

### If a definition-like fragment changed

Downstream claims depending on it are likely `needs_restatement`.

## UI

On saving an important edit, show Impact Preview:

```text
This change may affect:
- 5 downstream fragments
- 2 context packs
- 1 active problem

Actions:
- Mark affected as needs review
- Create impact report
- Ask Codex for analysis
- Ignore
```

Add:

```text
Impact Queue
```

Show unresolved impact reports.

Fragment detail page should have an `Impact` tab.

## Codex Participation

Not yet required in this milestone. This milestone is rule-based.

## Acceptance Criteria

- Change events are created for important modifications.
- Rule-based impact reports are generated.
- Impact preview appears after significant edits.
- Impact Queue lists unresolved reports.
- User can accept/dismiss/resolve impact items.
- Context packs can be marked stale.

---

# Milestone 6 — Codex Impact Analysis Assistant

## Goal

Use Codex to refine rule-based impact reports.

The system already knows which nodes are downstream. Codex helps explain how they are affected.

## Codex Job Type

Add:

```text
impact_analysis
```

Input:

```json
{
  "change_event": {...},
  "changed_fragment_before": "...",
  "changed_fragment_after": "...",
  "rule_based_affected_items": [...]
}
```

Output:

```json
{
  "impact_items": [
    {
      "target_id": "...",
      "impact_kind": "needs_restatement",
      "reason": "The claim uses unrestricted compactness, but the definition has been changed to Phi-compactness.",
      "confidence": 0.86,
      "suggested_action": "Restate the theorem using Phi-weighted limits and colimits."
    }
  ],
  "probably_unchanged": [...],
  "warnings": [...]
}
```

Codex must not directly rewrite affected fragments unless the user explicitly asks for a proposed patch.

## UI

In Impact Report detail:

```text
Ask Codex for impact analysis
```

Show Codex explanations next to rule-based items.

Actions:

```text
mark needs review
create task
dismiss
open affected fragment
```

## Acceptance Criteria

- Codex can analyze an impact report.
- Codex explanations are stored as proposed notes.
- User can accept/dismiss suggestions.
- No automatic stable data modification occurs.

---

# Milestone 7 — Generalized Fragment Evolution View

## Goal

Replace the narrow idea of “definition lineage” with generalized fragment evolution.

Every fragment can evolve, not only definitions.

Evolution answers:

```text
How did this fragment conceptually develop?
```

Impact answers:

```text
What did this fragment's change affect?
```

Do not confuse them.

## Evolution Relations

Use existing relation kinds:

```text
refines
replaces
generalizes
contradicts
```

Render them in an Evolution tab.

## UI

Fragment detail page tabs:

```text
Overview
Relations
Sources
Versions
Evolution
Impact
```

Evolution tab shows:

```text
Previous versions / replaced fragments
Refinements
Generalizations
Contradictions
Superseding fragments
```

Display conceptual lineage as a small graph or timeline.

## Codex Participation

Add optional AI job type:

```text
evolution_summary
```

Given two related fragments, Codex may propose:

```json
{
  "summary": "The newer definition restricts compactness to a class Phi of weights.",
  "breaking_changes": [
    "The initiality theorem must be restated using Phi-weighted limits/colimits."
  ],
  "unchanged_parts": [
    "The ambient Q-categorical setting remains unchanged."
  ],
  "warnings": []
}
```

This remains a proposal.

## Acceptance Criteria

- Every fragment has an Evolution tab.
- Evolution uses existing relations and version history.
- User can create `refines` and `replaces` relations from the Evolution tab.
- Codex can summarize conceptual differences between related fragments.

---

# Milestone 8 — Problem Health Review

## Goal

Add an AI-assisted “health check” for a ResearchProblem.

This helps the user see what is missing, unstable, or inconsistent.

## Rule-Based Checks

For a problem, detect:

```text
claims with no proof
claims with proof sketch only
claims with placeholder assumptions
active definitions with no examples
external claims with no source pointer
fragments with unknown origin
context packs marked stale
unresolved impact reports
attempts blocked without next step
```

## Codex Participation

Add AI job type:

```text
problem_health_review
```

Input:

```json
{
  "problem": {...},
  "linked_fragments": [...],
  "attempts": [...],
  "impact_reports": [...],
  "context_packs": [...]
}
```

Output:

```json
{
  "summary": "...",
  "open_gaps": [...],
  "unstable_claims": [...],
  "suggested_next_attempts": [...],
  "source_warnings": [...],
  "context_pack_warnings": [...],
  "recommended_tasks": [...]
}
```

## UI

Problem Workspace right panel should include:

```text
Problem Health
```

with:

```text
Run Health Check
```

Show:

```text
Gaps
Warnings
Suggested next attempts
Claims needing proof
Definitions needing examples
Stale context packs
```

## Acceptance Criteria

- System can run rule-based health checks.
- Codex can enrich health review.
- User can convert recommendations into ResearchTasks or Attempts.
- Health review does not automatically change stable data.

---

# Milestone 9 — ResearchTask and Action Board

## Goal

Introduce explicit tasks/gaps/blockers.

Not every research item should be a fragment. Some are actions:

```text
prove this theorem
find a counterexample
check a citation
formalize a definition
compare notation
read a paper
write a section
```

## Data Model

Add `ResearchTask`.

```ts
type ResearchTask = {
  id: string;

  kind:
    | "prove"
    | "disprove"
    | "find_example"
    | "find_counterexample"
    | "read_reference"
    | "check_citation"
    | "formalize_definition"
    | "compare_notation"
    | "write_section"
    | "review_impact"
    | "other";

  status:
    | "open"
    | "in_progress"
    | "blocked"
    | "done"
    | "abandoned";

  title: string;
  description: string;

  problem_id: string | null;
  fragment_id: string | null;
  attempt_id: string | null;
  source_id: string | null;

  blocker: string | null;
  created_at: string;
  updated_at: string;
};
```

## UI

Add:

```text
Tasks
```

or integrate into Problem Workspace as Action Board.

Board columns:

```text
Open
In Progress
Blocked
Done
Abandoned
```

Task cards should link to:

```text
problem
fragment
attempt
source
impact report
```

## Codex Participation

Codex can generate task proposals from:

```text
problem health review
impact report
proof gap review
literature card
import warnings
```

User confirms before creation.

## Acceptance Criteria

- User can create/edit tasks.
- Tasks can link to problems/fragments/attempts/sources.
- Problem Workspace shows related tasks.
- Codex suggestions can be converted into tasks.
- Dashboard shows open/blocked tasks.

---

# Milestone 10 — LiteratureCard and Reading Workspace

## Goal

Upgrade Sources into a research literature map.

A source should not merely be a citation record. It should record the role of the paper/book in the project.

## Data Model

Add `LiteratureCard`.

```ts
type LiteratureCard = {
  id: string;
  source_id: string;

  role:
    | "background"
    | "main_reference"
    | "notation_source"
    | "comparison"
    | "possible_gap"
    | "unread"
    | "to_check";

  reading_status:
    | "unread"
    | "skimmed"
    | "partially_read"
    | "read"
    | "needs_reread";

  summary: string | null;
  relevance_to_project: string | null;
  key_results: string | null;
  notation_imports: string | null;
  open_questions: string | null;

  created_at: string;
  updated_at: string;
};
```

Allow linking a LiteratureCard to Problems and Topics.

## UI

Add or upgrade:

```text
Literature
```

or:

```text
Reading Workspace
```

Display:

```text
Source metadata
Reading status
Role in project
Key external definitions
Key external theorems
Notation imported
Source pointers
Related fragments
Open citation checks
```

## Codex Participation

Add AI job type:

```text
literature_card_summary
```

Input:

```text
selected source
reading notes
external fragments
source pointers
```

Output:

```json
{
  "summary": "...",
  "role": "notation_source",
  "key_results": [...],
  "notation_imports": [...],
  "relevance_to_project": "...",
  "open_questions": [...],
  "warnings": [...]
}
```

Codex must not fabricate page numbers or citation locators.

## Acceptance Criteria

- LiteratureCard can be created for a source.
- User can set reading status and role.
- LiteratureCard links to external fragments/source pointers.
- Codex can propose a literature card from reading notes.
- Missing citation locator warnings are visible.

---

# Milestone 11 — Test Case and Counterexample Laboratory

## Goal

Support testing definitions and claims against examples and counterexamples.

This is central to mathematical research.

## Data Model

Add `TestCase`.

```ts
type TestCase = {
  id: string;
  title: string;
  body: string;

  target_fragment_id: string;

  result:
    | "satisfies"
    | "violates"
    | "unknown"
    | "partial"
    | "counterexample_candidate";

  notes: string | null;

  created_at: string;
  updated_at: string;
};
```

Optional: link TestCases to Problems.

## UI

For any Definition, Proposition, Theorem, or Conjecture, show:

```text
Test Cases
```

Matrix:

```text
Test case | Target | Result | Notes | Related fragments
```

Problem Workspace should show:

```text
Definitions with no test cases
Counterexample candidates
Claims with no examples
```

## Codex Participation

Add AI job type:

```text
test_case_suggestion
```

Given a definition or conjecture, Codex proposes possible examples/counterexamples to check.

Output:

```json
{
  "suggested_test_cases": [
    {
      "title": "...",
      "why_relevant": "...",
      "expected_result": "unknown",
      "risk": "May expose the compactness condition as too strong."
    }
  ],
  "warnings": []
}
```

Codex must not assert that a test case satisfies or violates a claim unless the excerpt explicitly proves it or the user confirms it.

## Acceptance Criteria

- User can add test cases to target fragments.
- Test case matrix displays results.
- Problem health review detects definitions with no test cases.
- Codex can propose test cases.
- Counterexample candidates can be promoted into Counterexample fragments after review.

---

# Milestone 12 — Writing Workspace

## Goal

Support moving stable research fragments into writing.

This should come after problem/attempt/impact/source systems are stable.

## UI

Add:

```text
Writing
```

or integrate with Context Packs.

Writing Workspace layout:

```text
Left:
  outline

Center:
  draft section

Right:
  stable fragments
  proved claims
  citation pointers
  unstable warnings
```

## Export Modes

Support:

```text
Markdown
LaTeX
context pack for paper writing
```

Paper writing export should include:

```text
stable definitions
proved claims
proof sketches to expand
source pointers
citation keys
unstable claims excluded
warnings
```

## Codex Participation

Codex can propose:

```text
section outline
paragraph skeleton
citation checklist
missing proof warnings
```

Codex must not silently include unstable claims in polished writing.

## Acceptance Criteria

- User can create a writing outline.
- User can attach fragments to sections.
- Export includes citation keys and provenance warnings.
- Unstable claims are flagged.
- Codex can propose a draft outline, not final truth.

---

# Suggested Implementation Order Summary

Implement in this exact order unless explicitly instructed otherwise:

```text
0. Baseline audit and stabilization
1. ResearchProblem model and Problem Workspace
2. Attempt model and Attempt Timeline
3. Claim status and proof gap tracking
4. Task-specific Context Pack templates
5. ChangeEvent and rule-based Impact Reports
6. Codex Impact Analysis Assistant
7. Generalized Fragment Evolution View
8. Problem Health Review
9. ResearchTask and Action Board
10. LiteratureCard and Reading Workspace
11. Test Case and Counterexample Laboratory
12. Writing Workspace
```

The first four milestones are the most important. They move LemmaForge from a fragment manager to a research process manager.

---

# Codex Permission Policy

Codex may do:

```text
extract fragments
suggest relations
suggest source pointers
summarize problems
suggest attempts
summarize attempts
review proof gaps
suggest context packs
analyze impact
suggest tasks
summarize literature cards
suggest test cases
suggest writing outlines
```

Codex must not do without explicit user confirmation:

```text
mark anything stable
mark a claim proved
delete fragments
overwrite stable fragments
replace definitions
change source provenance
invent citation locators
directly mutate Zotero
silently rewrite mathematical content
```

All Codex outputs that affect mathematical knowledge should be stored as proposals with review state.

---

# UI Direction

The app should become less like a generic admin dashboard and more like a mathematical research workspace.

Prioritize:

```text
Problem Workspace
Attempt Timeline
Impact Queue
Context Pack Builder
Reading Workspace
Test Case Matrix
Writing Workspace
```

Avoid stuffing too many panels into one page.

Each page should have one primary task.

---

# Final Product Vision

LemmaForge should become:

> A local-first mathematical research workbench that records mathematical objects as fragments, organizes them around research problems and attempts, tracks provenance and proof state, detects impact when ideas change, and uses Codex to generate reviewable suggestions for importing, organizing, testing, and exporting research context.

Short version:

> LemmaForge turns mathematical chats, notes, and literature excerpts into a traceable, reviewable, evolving research graph.
