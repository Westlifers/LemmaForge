from __future__ import annotations

from typing import Literal


FragmentType = Literal[
    "Definition",
    "Proposition",
    "Lemma",
    "Theorem",
    "Corollary",
    "Proof",
    "ProofSketch",
    "Example",
    "Counterexample",
    "Construction",
    "Question",
    "Conjecture",
    "Remark",
    "TODO",
    "PaperNote",
    "ReadingNote",
    "ExternalDefinition",
    "ExternalTheorem",
    "ExternalNotation",
    "LiteratureClaim",
    "ContextNote",
]

FragmentStatus = Literal["draft", "raw", "candidate", "working", "stable", "superseded", "rejected"]
ImportFragmentStatus = Literal["raw", "candidate"]
OriginClassification = Literal[
    "user_original",
    "assistant_generated",
    "external_source",
    "mixed",
    "unknown",
]
Exactness = Literal[
    "quote",
    "close_paraphrase",
    "paraphrase",
    "interpretation",
    "reconstruction",
    "original",
]
RelationKind = Literal[
    "depends_on",
    "uses",
    "proves",
    "proof_of",
    "refines",
    "replaces",
    "contradicts",
    "generalizes",
    "specializes_to",
    "is_example_of",
    "is_counterexample_to",
    "cites",
    "quotes",
    "paraphrases",
    "restates",
    "adopts_notation_from",
    "depends_on_notation",
    "inspired_by",
    "generalizes_external_result",
    "specializes_external_result",
    "questions_external_claim",
    "compares_with",
    "came_from",
]
SourceType = Literal[
    "paper",
    "book",
    "lecture_note",
    "webpage",
    "conversation",
    "personal_note",
    "unknown",
]


FRAGMENT_TYPES = set(FragmentType.__args__)
FRAGMENT_STATUSES = set(FragmentStatus.__args__)
IMPORT_FRAGMENT_STATUSES = set(ImportFragmentStatus.__args__)
ORIGIN_CLASSIFICATIONS = set(OriginClassification.__args__)
EXACTNESS_VALUES = set(Exactness.__args__)
RELATION_KINDS = set(RelationKind.__args__)
SOURCE_TYPES = set(SourceType.__args__)
