from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.allowed_template_id import AllowedTemplateId
from ..models.orshot_data_type import OrshotDataType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.content_strategy import ContentStrategy
    from ..models.marketing_research_report import MarketingResearchReport
    from ..models.orshot_schema_field import OrshotSchemaField
    from ..models.schedule_item import ScheduleItem
    from ..models.social_media_schedule import SocialMediaSchedule
    from ..models.strategy_phase import StrategyPhase


T = TypeVar("T", bound="CustomTypesResponse")


@_attrs_define
class CustomTypesResponse:
    """Response model exposing all custom types for OpenAPI schema generation.

    This model is used solely to ensure custom types appear in the OpenAPI schema
    so that client generation tools (e.g., openapi-ts) can generate TypeScript types.
    All fields are optional and default to None since this is only for schema exposure.

        Attributes:
            marketing_research_report (MarketingResearchReport | None | Unset): MarketingResearchReport type schema
                reference
            strategy_phase (None | StrategyPhase | Unset): StrategyPhase type schema reference
            content_strategy (ContentStrategy | None | Unset): ContentStrategy type schema reference
            schedule_item (None | ScheduleItem | Unset): ScheduleItem type schema reference
            social_media_schedule (None | SocialMediaSchedule | Unset): SocialMediaSchedule type schema reference
            orshot_schema_field (None | OrshotSchemaField | Unset): OrshotSchemaField type schema reference
            allowed_template_id (AllowedTemplateId | None | Unset): AllowedTemplateId enum schema reference
            orshot_data_type (None | OrshotDataType | Unset): OrshotDataType enum schema reference
    """

    marketing_research_report: MarketingResearchReport | None | Unset = UNSET
    strategy_phase: None | StrategyPhase | Unset = UNSET
    content_strategy: ContentStrategy | None | Unset = UNSET
    schedule_item: None | ScheduleItem | Unset = UNSET
    social_media_schedule: None | SocialMediaSchedule | Unset = UNSET
    orshot_schema_field: None | OrshotSchemaField | Unset = UNSET
    allowed_template_id: AllowedTemplateId | None | Unset = UNSET
    orshot_data_type: None | OrshotDataType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.content_strategy import ContentStrategy
        from ..models.marketing_research_report import MarketingResearchReport
        from ..models.orshot_schema_field import OrshotSchemaField
        from ..models.schedule_item import ScheduleItem
        from ..models.social_media_schedule import SocialMediaSchedule
        from ..models.strategy_phase import StrategyPhase

        marketing_research_report: dict[str, Any] | None | Unset
        if isinstance(self.marketing_research_report, Unset):
            marketing_research_report = UNSET
        elif isinstance(self.marketing_research_report, MarketingResearchReport):
            marketing_research_report = self.marketing_research_report.to_dict()
        else:
            marketing_research_report = self.marketing_research_report

        strategy_phase: dict[str, Any] | None | Unset
        if isinstance(self.strategy_phase, Unset):
            strategy_phase = UNSET
        elif isinstance(self.strategy_phase, StrategyPhase):
            strategy_phase = self.strategy_phase.to_dict()
        else:
            strategy_phase = self.strategy_phase

        content_strategy: dict[str, Any] | None | Unset
        if isinstance(self.content_strategy, Unset):
            content_strategy = UNSET
        elif isinstance(self.content_strategy, ContentStrategy):
            content_strategy = self.content_strategy.to_dict()
        else:
            content_strategy = self.content_strategy

        schedule_item: dict[str, Any] | None | Unset
        if isinstance(self.schedule_item, Unset):
            schedule_item = UNSET
        elif isinstance(self.schedule_item, ScheduleItem):
            schedule_item = self.schedule_item.to_dict()
        else:
            schedule_item = self.schedule_item

        social_media_schedule: dict[str, Any] | None | Unset
        if isinstance(self.social_media_schedule, Unset):
            social_media_schedule = UNSET
        elif isinstance(self.social_media_schedule, SocialMediaSchedule):
            social_media_schedule = self.social_media_schedule.to_dict()
        else:
            social_media_schedule = self.social_media_schedule

        orshot_schema_field: dict[str, Any] | None | Unset
        if isinstance(self.orshot_schema_field, Unset):
            orshot_schema_field = UNSET
        elif isinstance(self.orshot_schema_field, OrshotSchemaField):
            orshot_schema_field = self.orshot_schema_field.to_dict()
        else:
            orshot_schema_field = self.orshot_schema_field

        allowed_template_id: int | None | Unset
        if isinstance(self.allowed_template_id, Unset):
            allowed_template_id = UNSET
        elif isinstance(self.allowed_template_id, AllowedTemplateId):
            allowed_template_id = self.allowed_template_id.value
        else:
            allowed_template_id = self.allowed_template_id

        orshot_data_type: None | str | Unset
        if isinstance(self.orshot_data_type, Unset):
            orshot_data_type = UNSET
        elif isinstance(self.orshot_data_type, OrshotDataType):
            orshot_data_type = self.orshot_data_type.value
        else:
            orshot_data_type = self.orshot_data_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if marketing_research_report is not UNSET:
            field_dict["marketing_research_report"] = marketing_research_report
        if strategy_phase is not UNSET:
            field_dict["strategy_phase"] = strategy_phase
        if content_strategy is not UNSET:
            field_dict["content_strategy"] = content_strategy
        if schedule_item is not UNSET:
            field_dict["schedule_item"] = schedule_item
        if social_media_schedule is not UNSET:
            field_dict["social_media_schedule"] = social_media_schedule
        if orshot_schema_field is not UNSET:
            field_dict["orshot_schema_field"] = orshot_schema_field
        if allowed_template_id is not UNSET:
            field_dict["allowed_template_id"] = allowed_template_id
        if orshot_data_type is not UNSET:
            field_dict["orshot_data_type"] = orshot_data_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.content_strategy import ContentStrategy
        from ..models.marketing_research_report import MarketingResearchReport
        from ..models.orshot_schema_field import OrshotSchemaField
        from ..models.schedule_item import ScheduleItem
        from ..models.social_media_schedule import SocialMediaSchedule
        from ..models.strategy_phase import StrategyPhase

        d = dict(src_dict)

        def _parse_marketing_research_report(
            data: object,
        ) -> MarketingResearchReport | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                marketing_research_report_type_0 = MarketingResearchReport.from_dict(
                    data
                )

                return marketing_research_report_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MarketingResearchReport | None | Unset, data)

        marketing_research_report = _parse_marketing_research_report(
            d.pop("marketing_research_report", UNSET)
        )

        def _parse_strategy_phase(data: object) -> None | StrategyPhase | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                strategy_phase_type_0 = StrategyPhase.from_dict(data)

                return strategy_phase_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | StrategyPhase | Unset, data)

        strategy_phase = _parse_strategy_phase(d.pop("strategy_phase", UNSET))

        def _parse_content_strategy(data: object) -> ContentStrategy | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                content_strategy_type_0 = ContentStrategy.from_dict(data)

                return content_strategy_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ContentStrategy | None | Unset, data)

        content_strategy = _parse_content_strategy(d.pop("content_strategy", UNSET))

        def _parse_schedule_item(data: object) -> None | ScheduleItem | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                schedule_item_type_0 = ScheduleItem.from_dict(data)

                return schedule_item_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ScheduleItem | Unset, data)

        schedule_item = _parse_schedule_item(d.pop("schedule_item", UNSET))

        def _parse_social_media_schedule(
            data: object,
        ) -> None | SocialMediaSchedule | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                social_media_schedule_type_0 = SocialMediaSchedule.from_dict(data)

                return social_media_schedule_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SocialMediaSchedule | Unset, data)

        social_media_schedule = _parse_social_media_schedule(
            d.pop("social_media_schedule", UNSET)
        )

        def _parse_orshot_schema_field(
            data: object,
        ) -> None | OrshotSchemaField | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                orshot_schema_field_type_0 = OrshotSchemaField.from_dict(data)

                return orshot_schema_field_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | OrshotSchemaField | Unset, data)

        orshot_schema_field = _parse_orshot_schema_field(
            d.pop("orshot_schema_field", UNSET)
        )

        def _parse_allowed_template_id(
            data: object,
        ) -> AllowedTemplateId | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, int):
                    raise TypeError()
                allowed_template_id_type_0 = AllowedTemplateId(data)

                return allowed_template_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AllowedTemplateId | None | Unset, data)

        allowed_template_id = _parse_allowed_template_id(
            d.pop("allowed_template_id", UNSET)
        )

        def _parse_orshot_data_type(data: object) -> None | OrshotDataType | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                orshot_data_type_type_0 = OrshotDataType(data)

                return orshot_data_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | OrshotDataType | Unset, data)

        orshot_data_type = _parse_orshot_data_type(d.pop("orshot_data_type", UNSET))

        custom_types_response = cls(
            marketing_research_report=marketing_research_report,
            strategy_phase=strategy_phase,
            content_strategy=content_strategy,
            schedule_item=schedule_item,
            social_media_schedule=social_media_schedule,
            orshot_schema_field=orshot_schema_field,
            allowed_template_id=allowed_template_id,
            orshot_data_type=orshot_data_type,
        )

        custom_types_response.additional_properties = d
        return custom_types_response

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
