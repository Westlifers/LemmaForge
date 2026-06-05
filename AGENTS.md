# Agent Instructions

This repository is a local-first mathematical research fragment system.

Coding agents must follow these rules:

1. Do not directly mutate the research database unless implementing backend services, CLI operations, migrations, or tests.
2. Do not bypass Pydantic validation for `ResearchPatch` import data.
3. Do not mark imported fragments as `stable`; imports may only create `raw` or `candidate` fragments.
4. Do not write directly to Zotero's SQLite database.
5. Prefer the `research` CLI for local operations such as validation, import, and context export.
6. Keep Markdown vault output human-readable and suitable for Git diffs.
7. Add tests for schema validation and import commit behavior when touching import logic.
8. Do not introduce LangChain, Neo4j, PostgreSQL, or Electron without an explicit user request.

