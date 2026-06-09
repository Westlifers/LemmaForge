# LemmaForge Baseline Audit

Date: 2026-06-10

This audit closes Milestone 0. It records the current baseline before adding the
ResearchProblem layer.

## Current Core System

LemmaForge is currently a local-first mathematical research fragment system. The
database is the structured source of truth, while the Markdown vault is an
inspectable output surface for fragments and context packs.

- `Fragment` stores atomic mathematical notes: definitions, claims, proof
  sketches, examples, questions, reading notes, and related units.
- `Topic` groups fragments by subject and supports a graph workspace with saved
  layout positions.
- `Relation` stores fragment-to-fragment mathematical structure only. The active
  relation enum is compact: `depends_on`, `proof_of`, `refines`, `replaces`,
  `contradicts`, `generalizes`, `is_example_of`, `is_counterexample_to`,
  `uses_notation`, `questions`, `compares_with`, and `inspired_by`.
- `Source` and `SourcePointer` store provenance. Citation, quote, paraphrase, and
  import-origin information belongs here or in import metadata, not in active
  mathematical relations.
- `ImportBatch` gives AI/manual imports a durable review state before committing
  fragments.
- `ContextPack` exports selected fragments in user-controlled order for future
  AI work, preserving original fragment bodies.
- Zotero integration reads the Zotero Local API and syncs selected live items
  into LemmaForge `Source` records without writing to Zotero.
- AI jobs are advisory: AI import creates proposals/drafts, and AI context pack
  suggestion proposes selection/order/reasons without directly mutating stable
  mathematical knowledge.

## Stabilized Invariants

- Imported `ResearchPatch` fragments may only use `raw` or `candidate`; imported
  patches cannot mark fragments as `stable`.
- `ResearchPatch` relations must use the compact mathematical relation enum.
  Removed provenance-style relation kinds such as `quotes` and `came_from` are
  rejected.
- Source pointers must target a patch fragment and must include durable source
  identity through either a `citekey` or inline source metadata.
- Import rejection does not create fragments.
- Import commit creates fragments, mathematical relations, source pointers, and
  vault Markdown output through validated schemas.
- Context pack export keeps selected fragment bodies verbatim and includes only
  relations among selected fragments.
- Zotero sync deduplicates by `zotero_item_key` and then `citekey`; unavailable
  Zotero remains a clear local status, not a hard app failure.

## Regression Coverage

The backend suite currently covers:

- `ResearchPatch` schema validation, strict output-schema compatibility, source
  pointer rules, import-only statuses, and removed relation kind rejection.
- Import batch create/list/read/update/validate/reject/commit and duplicate
  suggestions without mutating existing fragments.
- Patch commit creation of fragments, relations, source pointers, and Markdown
  vault files.
- Fragment CRUD, version creation, bulk topic assignment, bulk delete cleanup,
  and related record cleanup.
- Relation kind migration from legacy rows, including archival of provenance
  relations and direction swaps for specialization relations.
- Topic graph layout validation.
- Context pack suggestion as an advisory AI flow, context pack save/export/topic
  history, rename, delete, and vault cleanup.
- Zotero Local API status/search/sync behavior, attachment filtering, source
  deduplication, and saved local API URL loading.
- CLI coverage for import list/show/reject.

Frontend build verification remains the primary UI regression check for this
milestone.

## Remaining Risks For Later Milestones

- There is no `ResearchProblem` model yet, so the app still organizes research
  primarily by topic and fragment rather than concrete mathematical objective.
- Fragment review status is not yet separated from mathematical claim truth
  status. Claim/proof state should be added in a later milestone.
- Attempts, impact reports, action tasks, literature cards, and test-case labs
  are not modeled yet.
- AI suggestions are available for import and context packs, but broader AI
  participation such as problem summaries, proof-gap review, attempt suggestion,
  and impact analysis is still future work.
- Markdown vault output is generated for committed fragments and exported context
  packs, but the database remains the authoritative editable state.

## Next Milestone

The next planned milestone is `ResearchProblem Model and Problem Workspace`.
That work should introduce the problem as the research unit above fragments and
topics, with explicit links from problems to topics and fragments.
