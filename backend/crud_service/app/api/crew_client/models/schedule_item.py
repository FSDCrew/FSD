from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.schedule_item_post_type import ScheduleItemPostType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ScheduleItem")


@_attrs_define
class ScheduleItem:
    """Represents a single scheduled Instagram content unit (post, story, reel).
    This is derived from the HTML table but stored in a structured way
    for UI, analytics, or downstream processing.

        Attributes:
            week (int): Week number within the campaign (1-based).
            date (datetime.date): Calendar date for this content.
            post_type (ScheduleItemPostType): Type of content.
            theme_concept (str): Theme or concept for this content unit.
            objective (str): Objective for this content (e.g., awareness, engagement, CTA).
            description (str): Detailed description to guide copy and visual creation.
            phase_name (None | str | Unset): Name of the strategy phase this item belongs to, if available.
            notes (None | str | Unset): Optional notes such as tags, CTA, stickers, collaborators, or audio suggestions.
    """

    week: int
    date: datetime.date
    post_type: ScheduleItemPostType
    theme_concept: str
    objective: str
    description: str
    phase_name: None | str | Unset = UNSET
    notes: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        week = self.week

        date = self.date.isoformat()

        post_type = self.post_type.value

        theme_concept = self.theme_concept

        objective = self.objective

        description = self.description

        phase_name: None | str | Unset
        if isinstance(self.phase_name, Unset):
            phase_name = UNSET
        else:
            phase_name = self.phase_name

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "week": week,
                "date": date,
                "post_type": post_type,
                "theme_concept": theme_concept,
                "objective": objective,
                "description": description,
            }
        )
        if phase_name is not UNSET:
            field_dict["phase_name"] = phase_name
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        week = d.pop("week")

        date = isoparse(d.pop("date")).date()

        post_type = ScheduleItemPostType(d.pop("post_type"))

        theme_concept = d.pop("theme_concept")

        objective = d.pop("objective")

        description = d.pop("description")

        def _parse_phase_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phase_name = _parse_phase_name(d.pop("phase_name", UNSET))

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        schedule_item = cls(
            week=week,
            date=date,
            post_type=post_type,
            theme_concept=theme_concept,
            objective=objective,
            description=description,
            phase_name=phase_name,
            notes=notes,
        )

        return schedule_item
