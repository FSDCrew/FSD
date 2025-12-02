from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.content_strategy_global_settings import ContentStrategyGlobalSettings
    from ..models.strategy_phase import StrategyPhase


T = TypeVar("T", bound="ContentStrategy")


@_attrs_define
class ContentStrategy:
    r"""Complete content strategy output.

    - `content`: Human-readable markdown summary
    - `global_settings`: Tone, voice, brand alignment, audience considerations
    - `phases`: Structured, agent-parsable strategy blocks (no dates!)
    - `metadata`: Version, timestamps, etc.

        Example:
            {'content': '# Content Strategy\n\n## Executive Summary\nHigh-level strategy...', 'global_settings':
                {'content_pillars': ['Education', 'Brand Story', 'Engagement'], 'tone': 'Friendly, confident, aspirational',
                'voice': 'Conversational but informative'}, 'phases': [{'duration_in_weeks': 2, 'messaging_guidelines':
                ['Highlight core value', 'Use simple, clear language'], 'name': 'Awareness', 'objectives': ['Build recognition',
                'Warm up audience'], 'posting_cadence': {'posts_per_week': 3, 'stories_per_week': 2},
                'recommended_content_types': ['posts', 'reels', 'stories'], 'themes': ['Brand Intro', 'Problem Awareness']}]}

        Attributes:
            content (str): Full content strategy rendered as markdown
            global_settings (ContentStrategyGlobalSettings): High-level settings: tone, voice, brand alignment, messaging
                principles, content pillars
            phases (list[StrategyPhase]): List of strategic phases that define themes, cadence, and objectives without
                assigning dates
    """

    content: str
    global_settings: ContentStrategyGlobalSettings
    phases: list[StrategyPhase]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        content = self.content

        global_settings = self.global_settings.to_dict()

        phases = []
        for phases_item_data in self.phases:
            phases_item = phases_item_data.to_dict()
            phases.append(phases_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "content": content,
                "global_settings": global_settings,
                "phases": phases,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.content_strategy_global_settings import (
            ContentStrategyGlobalSettings,
        )
        from ..models.strategy_phase import StrategyPhase

        d = dict(src_dict)
        content = d.pop("content")

        global_settings = ContentStrategyGlobalSettings.from_dict(
            d.pop("global_settings")
        )

        phases = []
        _phases = d.pop("phases")
        for phases_item_data in _phases:
            phases_item = StrategyPhase.from_dict(phases_item_data)

            phases.append(phases_item)

        content_strategy = cls(
            content=content,
            global_settings=global_settings,
            phases=phases,
        )

        content_strategy.additional_properties = d
        return content_strategy

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
