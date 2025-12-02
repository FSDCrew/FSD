from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.schedule_item import ScheduleItem


T = TypeVar("T", bound="SocialMediaSchedule")


@_attrs_define
class SocialMediaSchedule:
    """Represents the final social media posting schedule.

    - `html_table`: The fully-formed HTML table that is compatible with the html_table_to_excel tool.
    - `items`: Structured representation of each scheduled post/story/reel.

        Example:
            {'items': [{'date': '2025-11-01', 'description': 'Vibrant shots of campus, student groups & iconic spots.',
                'notes': 'Use Canva template; include hashtag #CampusLife', 'objective': 'Kickstart engagement; introduce
                semester vibe', 'phase_name': 'Awareness', 'post_type': 'Post', 'theme_concept': 'Welcome to Semester & Campus
                Life', 'week': 1}]}

        Attributes:
            items (list[ScheduleItem]): Flattened list of scheduled content items, one per row of the schedule (excluding
                header).
    """

    items: list[ScheduleItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "items": items,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule_item import ScheduleItem

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = ScheduleItem.from_dict(items_item_data)

            items.append(items_item)

        social_media_schedule = cls(
            items=items,
        )

        social_media_schedule.additional_properties = d
        return social_media_schedule

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
