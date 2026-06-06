from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.research_patch import ResearchPatch


def valid_patch_dict():
    return {
        "patch_type": "ResearchPatch",
        "metadata": {
            "source_kind": "chatgpt_excerpt",
            "topic_hint": "Yoneda structures",
            "created_by": "codex_import_agent",
            "requires_user_review": True,
        },
        "fragments": [
            {
                "local_id": "def_test",
                "type": "Definition",
                "title": "Test definition",
                "status": "candidate",
                "origin_classification": "assistant_generated",
                "exactness": "interpretation",
                "body": "A test definition is a definition used in a test.",
                "assumptions": [],
                "conclusion": None,
                "confidence": 0.8,
                "source_excerpt": "A test definition is ...",
            }
        ],
        "relations": [],
        "source_pointers": [],
        "warnings": [],
    }


def test_valid_research_patch_passes_validation():
    patch = ResearchPatch.model_validate(valid_patch_dict())

    assert patch.patch_type == "ResearchPatch"
    assert patch.fragments[0].status == "candidate"


def test_stable_import_status_is_rejected():
    data = valid_patch_dict()
    data["fragments"][0]["status"] = "stable"

    with pytest.raises(ValidationError):
        ResearchPatch.model_validate(data)


def test_invalid_relation_kind_is_rejected():
    data = valid_patch_dict()
    data["fragments"].append(
        {
            "local_id": "prop_test",
            "type": "Proposition",
            "title": "Test proposition",
            "status": "candidate",
            "origin_classification": "assistant_generated",
            "exactness": "interpretation",
            "body": "The test definition has a test proposition.",
            "assumptions": [],
            "conclusion": None,
            "confidence": 0.7,
            "source_excerpt": None,
        }
    )
    data["relations"] = [{"source": "prop_test", "kind": "not_a_kind", "target": "def_test"}]

    with pytest.raises(ValidationError):
        ResearchPatch.model_validate(data)


def test_research_patch_schema_is_strict_response_format_compatible():
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "research_patch.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    problems: list[str] = []

    def walk(node: object, path: str) -> None:
        if isinstance(node, dict):
            if "default" in node:
                problems.append(f"{path}: default is not allowed")
            properties = node.get("properties")
            if node.get("type") == "object" and isinstance(properties, dict):
                missing = sorted(set(properties) - set(node.get("required") or []))
                if missing:
                    problems.append(f"{path}: missing required keys {missing}")
            for key, value in node.items():
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(schema, "$")

    assert problems == []


def test_skill_schema_matches_root_schema():
    repo_root = Path(__file__).resolve().parents[2]
    root_schema = json.loads((repo_root / "schemas" / "research_patch.schema.json").read_text())
    skill_schema = json.loads(
        (repo_root / ".codex" / "skills" / "research-import" / "research_patch.schema.json").read_text()
    )

    assert skill_schema == root_schema
