---
name: research-import
description: Convert mathematical research notes, ChatGPT conversations, or paper-reading notes into LemmaForge ResearchPatch JSON.
---

# Research Import Skill

Convert the excerpt into one valid `ResearchPatch` JSON object for LemmaForge. The patch is only a proposal: LemmaForge validates it, then the user chooses which extracted fragments to save as database drafts.

## Hard Constraints

- Return JSON only. No Markdown, no code fences, no commentary.
- Conform to `research_patch.schema.json`.
- Include every schema field. Use `null` for absent nullable values and `[]` for empty arrays.
- Patch fragment status must be only `raw` or `candidate`.
- Never output database-only statuses: `draft`, `working`, `stable`, `superseded`, or `rejected`.
- Use `metadata.topic_hint`; do not invent `topic_id`.
- Do not invent existing database fragment IDs.
- Relations must use patch `local_id`s, unless the input explicitly provides a real existing fragment ID.
- Source pointers must include either `citekey` or inline `source` metadata when external provenance is asserted.

## Extraction Policy

Extract useful mathematical units conservatively:

- ambient setting or notation -> `ContextNote` or `ExternalNotation`
- definition -> `Definition`
- smaller claim -> `Proposition`
- major stated result -> `Theorem`
- proof idea -> `ProofSketch`
- construction -> `Construction`
- limitation or caveat -> `Remark`
- open problem -> `Question`
- speculative claim -> `Conjecture`

Do not merge distinct mathematical roles into one fragment when the excerpt clearly separates them. Do not over-split one coherent definition unless it names separate subconditions.

Use `candidate` for clear definitions, claims, constructions, or questions. Use `raw` for vague, fragmentary, mostly contextual, or uncertain material.

## Mathematical Fidelity

- Preserve hypotheses, assumptions, and uncertainty.
- Do not strengthen claims.
- Do not invent proofs or missing arguments.
- Do not turn tentative constructions into established theorems.
- If assumptions are placeholders, such as "under suitable assumptions" or "this should produce", keep that wording and add a warning.
- For theorem-like fragments, put hypotheses in `assumptions`, the conclusion in `conclusion`, and the full statement in `body`.

## Provenance

Origin values:

- `user_original`: presented as the user's own note, idea, conjecture, construction, or proof attempt
- `assistant_generated`: clearly from an assistant response
- `external_source`: quote, paraphrase, summary, or reconstruction of literature
- `mixed`: explicitly combines user, assistant, or external sources
- `unknown`: source cannot be inferred

Exactness values:

- `quote`: direct quotation
- `close_paraphrase`: close wording or sentence structure
- `paraphrase`: same content in different wording
- `interpretation`: reframed or extracted idea
- `reconstruction`: implicit mathematics reconstructed from context
- `original`: presented as original rather than sourced

If external material lacks citation metadata, add a warning.

## Relations

Relations are proposals only. Output high-confidence structural relations among extracted fragments:

- theorem-like fragments usually `depends_on` relevant definitions
- constructions usually `uses` context or notation
- proof sketches usually `proof_of` their claim
- remarks/questions usually `depends_on`, `refines`, or `compares_with` the claim they concern
- notation use may `depends_on_notation` or `adopts_notation_from`

Use only relation kinds allowed by the schema. Do not output unsupported kinds such as `questions`. Do not relate fragments to source pointers; provenance belongs in `source_pointers`.

Every relation must include `confidence`.

## Required Empty Fields

Every fragment must include:

- `assumptions`
- `conclusion`
- `confidence`
- `source_excerpt`

Every source pointer must include:

- `citekey`
- `source`
- `locator`
- `quote_text`
- `note`

Every inline source object must include:

- `source_type`
- `title`
- `authors`
- `year`
- `citekey`
- `zotero_item_key`
- `url`

## Style

- Use stable lowercase snake_case `local_id`s.
- Titles should be clear and should not overstate certainty.
- For tentative content, include words like `tentative`, `conditional`, `possible`, `expected`, or `candidate`.
- Warnings should be concise and actionable.
