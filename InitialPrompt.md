# Initial Prompt for Codex: Local-First Mathematical Research Fragment System

You are helping me build a local-first research knowledge system for mathematical learning and research.

The system is not a generic note-taking app and not a fully autonomous research agent. Its purpose is to store, structure, version, search, and export mathematical research fragments such as definitions, propositions, proofs, examples, counterexamples, constructions, questions, conjectures, reading notes, and literature-dependent notations.

The main user workflow is:

1. I have mathematical conversations with ChatGPT or read papers/books.
2. Useful ideas, definitions, propositions, proof sketches, examples, or literature references appear.
3. I paste a short natural-language excerpt into this system.
4. The system imports the excerpt as a structured candidate patch.
5. The patch is validated and shown in a preview UI.
6. I manually accept, edit, reject, or merge the proposed fragments.
7. Accepted fragments are stored in a local fragment graph.
8. Later, I can build and export context packs for ChatGPT, Codex, or paper writing.

The system should be designed as a local-first, inspectable, version-controlled mathematical research database.

---

## Core Design Principles

### 1. Local-first

The system should run locally.

Use:

* local FastAPI backend
* local Vue frontend
* local SQLite database
* local Markdown vault
* local Git version control

Do not design this as a cloud-first app.

### 2. Structured mathematical fragments

The system stores mathematical objects, not just notes.

Important fragment types include:

* Definition
* Proposition
* Lemma
* Theorem
* Corollary
* Proof
* ProofSketch
* Example
* Counterexample
* Construction
* Question
* Conjecture
* Remark
* TODO
* PaperNote
* ReadingNote
* ExternalDefinition
* ExternalTheorem
* ExternalNotation
* LiteratureClaim
* ContextNote

Each fragment must have:

* stable id
* type
* title
* body
* status
* origin classification
* exactness classification
* timestamps
* optional topic
* optional source pointers
* version history

### 3. Candidate import, not truth import

When importing natural-language excerpts, the system should produce candidate fragments only.

Imported fragments must have status:

* raw
* candidate

Never automatically mark imported content as stable.

The system must not treat agent-generated mathematical content as verified truth.

### 4. Provenance matters

The system must distinguish:

* my original ideas
* assistant-generated ideas
* external literature facts
* mixed ideas depending on external sources
* my interpretation of external literature
* direct quotations
* paraphrases
* reconstructions

Use provenance metadata aggressively.

### 5. Codex should generate patches, not directly mutate the research database

Codex or any import agent should produce a structured `ResearchPatch`.

The backend validates the patch.

The frontend shows a preview.

The user confirms before the data is committed.

### 6. Markdown vault plus SQLite

SQLite stores structured metadata, relations, versions, search indexes, and source pointers.

Markdown files store human-readable fragment bodies and context packs.

Git tracks the Markdown vault.

Accepted imports should optionally create a Git commit.

---

## Recommended Tech Stack

Frontend:

* Vue 3
* TypeScript
* Vite
* Pinia
* Vue Router
* Markdown rendering
* KaTeX for LaTeX rendering

Backend:

* Python 3.12+
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic
* SQLite
* Typer for CLI commands

Storage:

* SQLite database
* Markdown vault
* Git
* SQLite FTS5 for full-text search

Optional later:

* vector search
* Zotero Web API
* Tauri desktop packaging

Do not use LangChain in the first version.

Do not use Neo4j in the first version.

Do not use PostgreSQL in the first version unless SQLite becomes insufficient.

Do not use Electron in the first version.

---

## Repository Structure

Create a monorepo with approximately this structure:

```text
research-os/
  AGENTS.md
  README.md
  pyproject.toml
  package.json
  pnpm-workspace.yaml

  backend/
    app/
      main.py
      config.py

      api/
        fragments.py
        relations.py
        sources.py
        import_patch.py
        context_packs.py
        zotero.py
        agent.py

      models/
        fragment.py
        relation.py
        source.py
        context_pack.py

      schemas/
        fragment.py
        research_patch.py
        source.py
        context_pack.py

      services/
        fragment_service.py
        import_service.py
        context_builder.py
        search_service.py
        markdown_vault.py
        git_service.py
        zotero_service.py

    alembic/
    tests/

  frontend/
    src/
      pages/
        Dashboard.vue
        InboxImport.vue
        FragmentList.vue
        FragmentDetail.vue
        TopicWorkspace.vue
        ContextPackBuilder.vue
        ZoteroSettings.vue
        AgentConsole.vue

      components/
        FragmentCard.vue
        FragmentEditor.vue
        PatchPreview.vue
        MarkdownLatexRenderer.vue
        SourcePointerView.vue
        RelationList.vue
        ContextPackPreview.vue

      stores/
      api/
      types/

    vite.config.ts

  cli/
    research_cli/
      main.py

  vault/
    fragments/
    sources/
    context_packs/
    imports/

  schemas/
    research_patch.schema.json

  references/
    references.bib

  data/
    research.db

  .codex/
    skills/
      research-import/
        SKILL.md
        research_patch.schema.json
        examples/
```

The `data/` directory should be gitignored.

The `vault/` directory should be tracked by Git unless the user chooses otherwise.

---

## Core Database Models

Implement the first database schema around the following entities.

### Fragment

Fields:

* id
* type
* title
* status
* body
* topic_id nullable
* origin_classification
* exactness
* current_version_id nullable
* created_at
* updated_at

Allowed statuses:

* raw
* candidate
* working
* stable
* superseded
* rejected

Allowed origin classifications:

* user_original
* assistant_generated
* external_source
* mixed
* unknown

Allowed exactness values:

* quote
* close_paraphrase
* paraphrase
* interpretation
* reconstruction
* original

### FragmentVersion

Fields:

* id
* fragment_id
* version_number
* body
* change_note nullable
* created_at

### Relation

Fields:

* id
* source_fragment_id
* relation_kind
* target_fragment_id
* confidence nullable
* created_at

Allowed relation kinds:

* depends_on
* uses
* proves
* proof_of
* refines
* replaces
* contradicts
* generalizes
* specializes_to
* is_example_of
* is_counterexample_to
* cites
* quotes
* paraphrases
* restates
* adopts_notation_from
* depends_on_notation
* inspired_by
* generalizes_external_result
* specializes_external_result
* questions_external_claim
* compares_with
* came_from

### Source

Fields:

* id
* source_type
* title
* authors
* year
* citekey
* zotero_item_key nullable
* url nullable
* created_at
* updated_at

Allowed source types:

* paper
* book
* lecture_note
* webpage
* conversation
* personal_note
* unknown

### SourcePointer

Fields:

* id
* fragment_id
* source_id
* locator nullable
* exactness
* quote_text nullable
* note nullable

Examples of locator:

* "p. 354"
* "Section 2"
* "Definition 3.1"
* "Theorem 4.2"

### Topic

Fields:

* id
* title
* description nullable
* created_at
* updated_at

### ContextPack

Fields:

* id
* title
* objective
* body
* created_at
* updated_at

### ContextPackItem

Fields:

* context_pack_id
* fragment_id
* order_index
* reason nullable

---

## ResearchPatch Format

The import workflow is centered on a `ResearchPatch`.

Create a Pydantic schema and a JSON Schema for this structure.

A minimal version:

```json
{
  "patch_type": "ResearchPatch",
  "metadata": {
    "source_kind": "chatgpt_excerpt",
    "topic_hint": "optional string",
    "created_by": "codex_import_agent",
    "requires_user_review": true
  },
  "fragments": [
    {
      "local_id": "def_good_quantaloid_candidate",
      "type": "Definition",
      "title": "Good quantaloid",
      "status": "candidate",
      "origin_classification": "mixed",
      "exactness": "interpretation",
      "body": "A good quantaloid is ...",
      "assumptions": [],
      "conclusion": null,
      "confidence": 0.78,
      "source_excerpt": "..."
    }
  ],
  "relations": [
    {
      "source": "def_good_quantaloid_candidate",
      "kind": "refines",
      "target": "def_good_quantaloid"
    }
  ],
  "source_pointers": [
    {
      "fragment_local_id": "def_yoneda_structure",
      "citekey": "StreetWalters1978",
      "locator": "p. 354",
      "exactness": "paraphrase",
      "quote_text": null,
      "note": "Imported from a reading excerpt."
    }
  ],
  "warnings": [
    "The source text appears provisional. Do not mark as stable."
  ]
}
```

All imported fragments must be `raw` or `candidate`.

The backend must reject a patch that tries to import a fragment as `stable`.

---

## Backend API Requirements

Implement at least these API endpoints.

### Fragments

* `GET /api/fragments`
* `POST /api/fragments`
* `GET /api/fragments/{id}`
* `PATCH /api/fragments/{id}`
* `GET /api/fragments/{id}/versions`
* `POST /api/fragments/{id}/versions`

### Relations

* `GET /api/fragments/{id}/relations`
* `POST /api/relations`
* `DELETE /api/relations/{id}`

### Import Patch

* `POST /api/import/validate`
* `POST /api/import/preview`
* `POST /api/import/commit`

The commit endpoint should write to SQLite and Markdown vault.

It should not bypass validation.

### Sources

* `GET /api/sources`
* `POST /api/sources`
* `GET /api/sources/{id}`
* `PATCH /api/sources/{id}`

### Context Packs

* `GET /api/context-packs`
* `POST /api/context-packs`
* `GET /api/context-packs/{id}`
* `POST /api/context-packs/{id}/export`

### Zotero Settings

First version only needs local configuration, not full Zotero API.

* `GET /api/zotero/status`
* `POST /api/zotero/settings`
* `GET /api/zotero/search?query=...`

---

## CLI Requirements

Create a `research` CLI with Typer.

Commands:

```bash
research status
research db init
research db migrate
research import validate path/to/patch.json
research import commit path/to/patch.json
research zotero status
research zotero search "Yoneda structures"
research context export CONTEXT_PACK_ID
```

Codex should prefer CLI commands over directly manipulating database files.

---

## Markdown Vault Format

Each fragment should have a Markdown file.

Example:

```markdown
---
id: def_good_quantaloid
type: Definition
status: candidate
origin_classification: mixed
exactness: interpretation
topic: Quantaloid-enriched category
created_at: 2026-06-05T00:00:00
updated_at: 2026-06-05T00:00:00
---

# Good quantaloid

A good quantaloid is ...

## Notes

This name is provisional.

## Provenance

- Origin: mixed
- Exactness: interpretation
```

The Markdown vault is for human inspection and Git diff.

The database remains the source of truth for structured relations.

---

## Zotero Integration

First version:

* User manually configures Zotero data directory.
* User manually configures Better BibTeX exported `references.bib`.
* The system can parse `references.bib`.
* The system can map citekeys to source records.
* The system can attach fragments to citekeys and locators.

Do not write to Zotero's SQLite database.

Do not assume all Zotero files are stored attachments.

Support this abstraction later:

```ts
type AttachmentLocation =
  | { kind: "zotero_stored"; itemKey: string; localPath: string }
  | { kind: "linked_file"; itemKey: string; localPath: string }
  | { kind: "remote_zotero_storage"; itemKey: string; apiUrl: string }
  | { kind: "missing_or_unsynced"; itemKey: string };
```

For now, focus on citekeys and source pointers.

---

## Frontend MVP Pages

Implement these pages first.

### Dashboard

Show:

* number of fragments
* number of candidate imports
* recent fragments
* recent context packs

### Inbox Import

A page where the user pastes:

* raw excerpt
* topic hint
* optional source/citekey
* optional locator

The page should allow either:

1. manual creation of a ResearchPatch, or
2. pasting a ResearchPatch JSON directly.

First version may skip live Codex invocation. It only needs patch validation and preview.

### Patch Preview

Show:

* proposed fragments
* proposed relations
* source pointers
* warnings

Actions:

* accept
* edit
* reject

### Fragment List

Search and filter by:

* title
* type
* status
* topic
* origin classification

### Fragment Detail

Show:

* rendered Markdown/LaTeX
* metadata
* relations
* source pointers
* versions

### Context Pack Builder

Allow the user to select fragments and export a Markdown context pack.

The exported context pack should separate:

* current objective
* original ideas
* external definitions/results
* notation dependencies
* proof sketches
* open questions
* warnings/provenance notes

---

## Codex Skill: Research Import

Create `.codex/skills/research-import/SKILL.md`.

The skill should say:

```markdown
# Research Import Skill

You convert short mathematical research notes, ChatGPT excerpts, or paper-reading notes into a structured ResearchPatch.

## Goal

Given a natural-language excerpt, produce a JSON object conforming to `research_patch.schema.json`.

## Fragment Types

Allowed fragment types:

- Definition
- Proposition
- Lemma
- Theorem
- Corollary
- Proof
- ProofSketch
- Example
- Counterexample
- Construction
- Question
- Conjecture
- Remark
- TODO
- PaperNote
- ReadingNote
- ExternalDefinition
- ExternalTheorem
- ExternalNotation
- LiteratureClaim
- ContextNote

## Status Policy

All imported fragments must have status `raw` or `candidate`.

Never assign `stable` during import.

## Mathematical Fidelity

Preserve the mathematical content of the source.

Do not strengthen hypotheses.

Do not silently simplify away assumptions.

Do not invent proofs.

If the source is ambiguous, add a warning.

## Provenance Policy

Classify origin as one of:

- user_original
- assistant_generated
- external_source
- mixed
- unknown

Classify exactness as one of:

- quote
- close_paraphrase
- paraphrase
- interpretation
- reconstruction
- original

External source material requires citation metadata whenever available.

## Output Policy

Return only valid JSON.

No Markdown.

No commentary outside JSON.
```

---

## AGENTS.md Requirements

Create an `AGENTS.md` at the repo root.

It should instruct coding agents:

1. Do not directly mutate the research database unless implementing backend services or tests.
2. Do not bypass Pydantic validation.
3. Do not mark imported fragments as stable.
4. Do not write directly to Zotero's SQLite database.
5. Prefer CLI commands for local operations.
6. Keep Markdown vault output human-readable.
7. Add tests for schema validation and import commit behavior.
8. Do not introduce LangChain, Neo4j, PostgreSQL, or Electron without explicit user request.

---

## First Implementation Goal

Do not try to implement the entire final system immediately.

First implement MVP 1 and MVP 2:

### MVP 1

* project scaffold
* FastAPI backend
* SQLite database
* SQLAlchemy models
* Alembic setup
* fragment CRUD
* relation CRUD
* source CRUD
* Markdown vault writing
* basic Vue frontend
* fragment list/detail/editor

### MVP 2

* ResearchPatch schema
* import validation endpoint
* import preview endpoint
* import commit endpoint
* patch preview UI
* accepted patch writes fragments and relations
* accepted patch writes Markdown files
* import status remains raw/candidate
* basic tests

After this, stop and report:

* what has been implemented
* how to run backend
* how to run frontend
* how to run tests
* what remains unfinished

---

## Testing Requirements

Backend tests should cover:

* valid ResearchPatch passes validation
* invalid status `stable` in imported fragment is rejected
* invalid relation kind is rejected
* importing a patch creates fragments
* importing a patch creates relations
* importing a patch creates source pointers when provided
* Markdown files are generated
* fragment version is created on update

Frontend tests are optional for the first pass, but the frontend should compile.

---

## Development Commands

Use reasonable commands such as:

```bash
# backend
cd backend
uvicorn app.main:app --reload

# frontend
cd frontend
pnpm install
pnpm dev

# tests
cd backend
pytest
```

Use `pnpm` for frontend package management unless there is a good reason not to.

Use `uv` or standard Python tooling for backend if convenient.

---

## Output Expected from Codex

When implementing, provide:

1. a concise summary of created files
2. setup instructions
3. run instructions
4. test instructions
5. known limitations
6. next suggested milestone

Do not claim that unimplemented features are complete.

Do not implement speculative features beyond the MVP unless explicitly requested.
