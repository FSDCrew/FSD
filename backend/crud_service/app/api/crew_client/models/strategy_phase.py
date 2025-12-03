from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.post_type import PostType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.strategy_phase_posting_cadence import StrategyPhasePostingCadence


T = TypeVar("T", bound="StrategyPhase")


@_attrs_define
class StrategyPhase:
    """Non-date-specific strategic phase definition.
    The scheduler will later map these phases to calendar weeks.

        Attributes:
            name (str): Phase name, e.g., 'Awareness', 'Engagement', etc.
            duration_in_weeks (int): How long the phase should run, without calendar dates.
            themes (list[str]): Core themes emphasized in this phase.
            objectives (list[str]): Strategic objectives for the phase.
            recommended_content_types (list[PostType]): Content formats recommended here (e.g., POST, STORY).
            posting_cadence (StrategyPhasePostingCadence): Cadence expressed as counts, e.g., {'posts_per_week': 3,
                'stories_per_week': 2}
            messaging_guidelines (list[str] | None | Unset): Tone & message guidelines specific to this phase.
    """

    name: str
    duration_in_weeks: int
    themes: list[str]
    objectives: list[str]
    recommended_content_types: list[PostType]
    posting_cadence: StrategyPhasePostingCadence
    messaging_guidelines: list[str] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        duration_in_weeks = self.duration_in_weeks

        themes = self.themes

        objectives = self.objectives

        recommended_content_types = []
        for recommended_content_types_item_data in self.recommended_content_types:
            recommended_content_types_item = recommended_content_types_item_data.value
            recommended_content_types.append(recommended_content_types_item)

        posting_cadence = self.posting_cadence.to_dict()

        messaging_guidelines: list[str] | None | Unset
        if isinstance(self.messaging_guidelines, Unset):
            messaging_guidelines = UNSET
        elif isinstance(self.messaging_guidelines, list):
            messaging_guidelines = self.messaging_guidelines

        else:
            messaging_guidelines = self.messaging_guidelines

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "duration_in_weeks": duration_in_weeks,
                "themes": themes,
                "objectives": objectives,
                "recommended_content_types": recommended_content_types,
                "posting_cadence": posting_cadence,
            }
        )
        if messaging_guidelines is not UNSET:
            field_dict["messaging_guidelines"] = messaging_guidelines

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.strategy_phase_posting_cadence import StrategyPhasePostingCadence

        d = dict(src_dict)
        name = d.pop("name")

        duration_in_weeks = d.pop("duration_in_weeks")

        themes = cast(list[str], d.pop("themes"))

        objectives = cast(list[str], d.pop("objectives"))

        recommended_content_types = []
        _recommended_content_types = d.pop("recommended_content_types")
        for recommended_content_types_item_data in _recommended_content_types:
            recommended_content_types_item = PostType(
                recommended_content_types_item_data
            )

            recommended_content_types.append(recommended_content_types_item)

        posting_cadence = StrategyPhasePostingCadence.from_dict(
            d.pop("posting_cadence")
        )

        def _parse_messaging_guidelines(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                messaging_guidelines_type_0 = cast(list[str], data)

                return messaging_guidelines_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        messaging_guidelines = _parse_messaging_guidelines(
            d.pop("messaging_guidelines", UNSET)
        )

        strategy_phase = cls(
            name=name,
            duration_in_weeks=duration_in_weeks,
            themes=themes,
            objectives=objectives,
            recommended_content_types=recommended_content_types,
            posting_cadence=posting_cadence,
            messaging_guidelines=messaging_guidelines,
        )

        return strategy_phase
