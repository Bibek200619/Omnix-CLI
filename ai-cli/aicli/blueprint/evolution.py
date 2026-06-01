"""Blueprint evolution helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeGuard, cast

from pydantic import BaseModel

from aicli.schemas.blueprint import (
    ArchitectureNote,
    EntityDefinition,
    FeatureDefinition,
    GoalDefinition,
    ModuleDefinition,
    PageDefinition,
    ProjectBlueprint,
)


def evolve_blueprint(
    existing: ProjectBlueprint,
    proposed: ProjectBlueprint,
) -> ProjectBlueprint:
    """Merge an architect proposal into the existing blueprint."""

    payload = existing.model_dump(mode="python")
    if proposed.project_name.strip():
        payload["project_name"] = proposed.project_name
    if proposed.description.strip():
        payload["description"] = proposed.description

    payload["metadata"] = _merge_model(existing.metadata, proposed.metadata).model_dump(
        mode="python"
    )
    payload["goals"] = [
        item.model_dump(mode="python")
        for item in _merge_model_lists(
            existing.goals,
            proposed.goals,
            lambda goal: goal.title,
        )
    ]
    payload["pages"] = [
        item.model_dump(mode="python")
        for item in _merge_model_lists(existing.pages, proposed.pages, _page_key)
    ]
    payload["features"] = [
        item.model_dump(mode="python")
        for item in _merge_model_lists(
            existing.features,
            proposed.features,
            lambda feature: feature.name,
        )
    ]
    payload["entities"] = [
        item.model_dump(mode="python")
        for item in _merge_model_lists(
            existing.entities,
            proposed.entities,
            lambda entity: entity.name,
        )
    ]
    payload["modules"] = [
        item.model_dump(mode="python")
        for item in _merge_model_lists(
            existing.modules,
            proposed.modules,
            lambda module: module.name,
        )
    ]
    payload["architecture_notes"] = [
        item.model_dump(mode="python")
        for item in _merge_model_lists(
            existing.architecture_notes,
            proposed.architecture_notes,
            _architecture_note_key,
        )
    ]
    payload["assumptions"] = _merge_text_lists(existing.assumptions, proposed.assumptions)
    payload["constraints"] = _merge_text_lists(existing.constraints, proposed.constraints)
    payload["future_enhancements"] = _merge_text_lists(
        existing.future_enhancements,
        proposed.future_enhancements,
    )

    return ProjectBlueprint.model_validate(payload)


def _merge_model_lists[ModelT: BaseModel](
    existing_items: Sequence[ModelT],
    proposed_items: Sequence[ModelT],
    key_factory: Callable[[ModelT], str],
) -> list[ModelT]:
    merged_items: list[ModelT] = list(existing_items)
    key_to_index = {
        _normalize_lookup(key_factory(item)): index
        for index, item in enumerate(merged_items)
    }

    for proposed_item in proposed_items:
        key = _normalize_lookup(key_factory(proposed_item))
        if key not in key_to_index:
            key_to_index[key] = len(merged_items)
            merged_items.append(proposed_item)
            continue

        existing_index = key_to_index[key]
        merged_items[existing_index] = _merge_model(
            merged_items[existing_index],
            proposed_item,
        )

    return merged_items


def _merge_model[ModelT: BaseModel](existing: ModelT, proposed: ModelT) -> ModelT:
    existing_payload = cast(dict[str, object], existing.model_dump(mode="python"))
    proposed_payload = cast(dict[str, object], proposed.model_dump(mode="python"))
    merged_payload: dict[str, object] = dict(existing_payload)

    for key, proposed_value in proposed_payload.items():
        merged_payload[key] = _merge_value(existing_payload.get(key), proposed_value)

    return type(existing).model_validate(merged_payload)


def _merge_value(existing_value: object, proposed_value: object) -> object:
    if isinstance(proposed_value, str):
        return proposed_value if proposed_value.strip() else existing_value
    if isinstance(proposed_value, list):
        if _is_text_sequence(existing_value) and _is_text_sequence(proposed_value):
            return _merge_text_lists(existing_value, proposed_value)
        return proposed_value if proposed_value else existing_value
    if isinstance(proposed_value, dict):
        if isinstance(existing_value, dict):
            return {**existing_value, **proposed_value}
        return proposed_value
    if proposed_value is None:
        return existing_value
    return proposed_value


def _merge_text_lists(
    existing_items: Sequence[str],
    proposed_items: Sequence[str],
) -> list[str]:
    merged_items: list[str] = []
    seen: set[str] = set()
    for item in [*existing_items, *proposed_items]:
        normalized_item = item.strip()
        if not normalized_item:
            continue
        lookup_key = _normalize_lookup(normalized_item)
        if lookup_key in seen:
            continue
        seen.add(lookup_key)
        merged_items.append(normalized_item)
    return merged_items


def _is_text_sequence(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _page_key(page: PageDefinition) -> str:
    return page.name or page.path


def _architecture_note_key(note: ArchitectureNote) -> str:
    return note.title or note.content


def _normalize_lookup(value: str) -> str:
    return " ".join(value.casefold().split())


__all__ = [
    "ArchitectureNote",
    "EntityDefinition",
    "FeatureDefinition",
    "GoalDefinition",
    "ModuleDefinition",
    "evolve_blueprint",
]
