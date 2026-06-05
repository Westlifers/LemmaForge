from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session


TYPE_PREFIXES = {
    "Definition": "def",
    "Proposition": "prop",
    "Lemma": "lem",
    "Theorem": "thm",
    "Corollary": "cor",
    "Proof": "proof",
    "ProofSketch": "proof_sketch",
    "Example": "ex",
    "Counterexample": "counterex",
    "Construction": "constr",
    "Question": "q",
    "Conjecture": "conj",
    "Remark": "rem",
    "TODO": "todo",
    "PaperNote": "paper_note",
    "ReadingNote": "reading_note",
    "ExternalDefinition": "ext_def",
    "ExternalTheorem": "ext_thm",
    "ExternalNotation": "ext_notation",
    "LiteratureClaim": "lit_claim",
    "ContextNote": "context",
}


def slugify(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return slug[:80] or fallback


def fragment_id_base(fragment_type: str, title: str) -> str:
    prefix = TYPE_PREFIXES.get(fragment_type, "frag")
    return f"{prefix}_{slugify(title, fallback='fragment')}"


def short_uuid() -> str:
    return uuid.uuid4().hex[:12]


def unique_model_id(db: Session, model: Any, base: str) -> str:
    candidate = slugify(base)
    index = 2
    while db.execute(select(model).where(model.id == candidate)).scalar_one_or_none() is not None:
        candidate = f"{slugify(base)}_{index}"
        index += 1
    return candidate

