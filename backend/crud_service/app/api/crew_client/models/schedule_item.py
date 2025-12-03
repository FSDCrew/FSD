from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.post_type import PostType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ScheduleItem")


@_attrs_define
class ScheduleItem:
    """Represents a single scheduled Instagram content unit (post or story).
    This is derived from the HTML table but stored in a structured way
    for UI, analytics, or downstream processing.

        Attributes:
            id (int): Unique identifier for this schedule item within the schedule.
            date (datetime.date): Calendar date for the post's content.
            post_type (PostType): Enum for Instagram post types.
            theme_concept (str): Theme or concept for the post's content.
            objective (str): Objective for of the post's content (e.g., awareness, engagement, CTA).
            description (str): Detailed description to of the post's content. Will be used to guide copy and visual creation
                if tasks are added.
            phase_name (None | str | Unset): Name of the strategy phase this item belongs to, if available.
            week (int | None | Unset): Week number within the campaign.
    """

    id: int
    date: datetime.date
    post_type: PostType
    theme_concept: str
    objective: str
    description: str
    phase_name: None | str | Unset = UNSET
    week: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

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

        week: int | None | Unset
        if isinstance(self.week, Unset):
            week = UNSET
        else:
            week = self.week

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "date": date,
                "post_type": post_type,
                "theme_concept": theme_concept,
                "objective": objective,
                "description": description,
            }
        )
        if phase_name is not UNSET:
            field_dict["phase_name"] = phase_name
        if week is not UNSET:
            field_dict["week"] = week

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        date = isoparse(d.pop("date")).date()

        post_type = PostType(d.pop("post_type"))

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

        def _parse_week(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        week = _parse_week(d.pop("week", UNSET))

        schedule_item = cls(
            id=id,
            date=date,
            post_type=post_type,
            theme_concept=theme_concept,
            objective=objective,
            description=description,
            phase_name=phase_name,
            week=week,
        )

        return schedule_item
