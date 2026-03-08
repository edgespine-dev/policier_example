from __future__ import annotations

import json
from pathlib import Path
from string import Template
from typing import Any


TOPICS_PATH = Path(__file__).with_name("topics.json")


def _load_catalog() -> dict[str, Any]:
    raw = json.loads(TOPICS_PATH.read_text(encoding="utf-8"))
    topics = raw.get("topics")
    templates = raw.get("prompt_templates")
    if not isinstance(topics, list) or not isinstance(templates, dict):
        raise ValueError("Invalid topics.json format")
    return raw


def _render_prompts(
    topic: dict[str, Any],
    templates: dict[str, Any],
) -> dict[str, str]:
    start_template = Template(str(templates.get("start", "")))
    verify_template = Template(str(templates.get("verify", "")))

    values = {
        "topic": str(topic.get("topic", "")),
        "title": str(topic.get("title", "")),
        "scope": str(topic.get("scope", "")),
        "keywords": ", ".join(str(k) for k in topic.get("keywords", [])),
        # Keep loop placeholders for runtime.
        "source_text": "{source_text}",
        "output_schema": "{output_schema}",
        "candidate_answer": "{candidate_answer}",
    }

    return {
        "start": start_template.safe_substitute(values),
        "verify": verify_template.safe_substitute(values),
    }


def list_topics(include_prompts: bool = False) -> list[dict[str, Any]]:
    catalog = _load_catalog()
    templates = catalog.get("prompt_templates", {})
    variables = templates.get("variables", {})

    result: list[dict[str, Any]] = []
    for topic in catalog["topics"]:
        item: dict[str, Any] = {
            "id": topic.get("id"),
            "title": topic.get("title"),
            "topic": topic.get("topic"),
            "scope": topic.get("scope"),
            "keywords": topic.get("keywords", []),
        }
        if include_prompts:
            item["prompts"] = _render_prompts(topic, templates)
            item["prompt_variables"] = variables
        result.append(item)
    return result


def get_topic(topic_name: str, include_prompts: bool = False) -> dict[str, Any] | None:
    for topic in list_topics(include_prompts=include_prompts):
        if str(topic.get("topic")) == topic_name:
            return topic
    return None
