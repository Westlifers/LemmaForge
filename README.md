# LemmaForge

LemmaForge is a local-first mathematical research fragment system. It stores definitions, propositions, proofs, examples, literature notes, and context packs as structured local data with a human-readable Markdown vault.

The first implementation includes:

- FastAPI backend with SQLite and SQLAlchemy models.
- Fragment, relation, source, import, context pack, and Zotero placeholder APIs.
- `ResearchPatch` validation, preview, and commit services.
- Direct fragment import workflow that stores new notes as database-backed `draft` fragments.
- Durable `ResearchPatch` import review batches with draft, validated, committed, and rejected states.
- Duplicate suggestions for candidate fragments without automatic merging.
- Markdown vault generation for accepted fragments.
- Typer CLI entry point named `research`.
- Vue 3 frontend for draft import, review queues, fragment graph editing, topic management, source browsing, and context pack building.
- Backend tests for patch validation, import commit behavior, Markdown generation, and version creation.

## Layout

```text
backend/        FastAPI application, SQLAlchemy models, services, tests
frontend/       Vue 3 + TypeScript frontend
cli/            Typer CLI
schemas/        JSON Schema for ResearchPatch
vault/          Markdown vault tracked by Git
references/     Better BibTeX export placeholder
data/           Local SQLite database, ignored by Git
.codex/skills/  Research import Codex skill
```

## Backend

Install dependencies in your preferred Python 3.12 environment:

```bash
pip install -e ".[dev]"
```

Initialize the database:

```bash
research db init
```

Run the API:

```bash
cd backend
uvicorn app.main:app --reload
```

Run tests from the repository root:

```bash
pytest
```

## Frontend

This project is configured for `npm` workspaces.

```bash
npm install
npm --workspace @lemmaforge/frontend run dev
```

On Windows PowerShell, if `npm` is blocked by execution policy, use `npm.cmd` for the same commands.

## CLI

```bash
research status
research db init
research import validate path/to/patch.json
research import commit path/to/patch.json
research import list
research import show IMPORT_BATCH_ID
research import reject IMPORT_BATCH_ID
research zotero status
research zotero search "Yoneda structures"
research zotero sync
research context export CONTEXT_PACK_ID
research db backup data/research-backup.db
research vault check
```

## Fragment Workflow

The `/import` page is for writing one fragment at a time. Clicking `Store Draft` creates a real `Fragment` row in SQLite with status `draft`.

The `/fragments` page is the merged fragment collection. It shows all fragment statuses by default and uses in-page filters for topic, status, type, origin, exactness, search, and source citekey. Topic is the primary filter; `Unsorted` shows fragments without a topic.

From a fragment detail page, the status dropdown can move fragments between `draft`, `working`, `stable`, `rejected`, or another status.

Topics are stored separately and linked through `fragment.topic_id`. The fragment editor uses a topic dropdown, fragment cards show their topic when assigned, and the topic workspace lists linked fragments under each topic.

## TeX Support

Fragment bodies and context pack previews render Markdown with KaTeX. Supported math delimiters include inline `$...$` and `\(...\)`, display `$$...$$` and `\[...\]`, plus common display environments such as `equation`, `align`, `gather`, and `multline`.

Raw TeX is stored unchanged in SQLite and the Markdown vault. Code fences and inline code are not TeX-rendered.

## Current Limits

- Zotero support is local-first: the web app reads Zotero through the official Local API on `127.0.0.1:23119`, syncs selected items into LemmaForge `Source` rows, and keeps Better BibTeX sync as a fallback path.
- Import agents are not invoked from the frontend. The main frontend import flow creates direct draft fragments; `ResearchPatch` batches remain available through the backend and CLI.
- The database is local SQLite. The Markdown vault is written for inspection and Git diffs, while SQLite remains the structured source of truth.
- Duplicate handling is suggestion-only. The user must explicitly skip or link candidates before commit.
