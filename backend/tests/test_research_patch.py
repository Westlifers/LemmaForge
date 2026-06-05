from __future__ import annotations

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

