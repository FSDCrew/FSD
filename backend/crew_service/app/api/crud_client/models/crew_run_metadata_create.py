from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.crew_run_metadata_create_inputs import CrewRunMetadataCreateInputs
    from ..models.retry_feedback import RetryFeedback
    from ..models.task_info import TaskInfo


T = TypeVar("T", bound="CrewRunMetadataCreate")


@_attrs_define
class CrewRunMetadataCreate:
    """
    Attributes:
        inputs (CrewRunMetadataCreateInputs):
        tasks_snapshot (list[TaskInfo]):
        retry_feedback (None | RetryFeedback | Unset):
    """

    inputs: CrewRunMetadataCreateInputs
    tasks_snapshot: list[TaskInfo]
    retry_feedback: None | RetryFeedback | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.retry_feedback import RetryFeedback

        inputs = self.inputs.to_dict()

        tasks_snapshot = []
        for tasks_snapshot_item_data in self.tasks_snapshot:
            tasks_snapshot_item = tasks_snapshot_item_data.to_dict()
            tasks_snapshot.append(tasks_snapshot_item)

        retry_feedback: dict[str, Any] | None | Unset
        if isinstance(self.retry_feedback, Unset):
            retry_feedback = UNSET
        elif isinstance(self.retry_feedback, RetryFeedback):
            retry_feedback = self.retry_feedback.to_dict()
        else:
            retry_feedback = self.retry_feedback

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "inputs": inputs,
                "tasks_snapshot": tasks_snapshot,
            }
        )
        if retry_feedback is not UNSET:
            field_dict["retry_feedback"] = retry_feedback

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.crew_run_metadata_create_inputs import CrewRunMetadataCreateInputs
        from ..models.retry_feedback import RetryFeedback
        from ..models.task_info import TaskInfo

        d = dict(src_dict)
        inputs = CrewRunMetadataCreateInputs.from_dict(d.pop("inputs"))

        tasks_snapshot = []
        _tasks_snapshot = d.pop("tasks_snapshot")
        for tasks_snapshot_item_data in _tasks_snapshot:
            tasks_snapshot_item = TaskInfo.from_dict(tasks_snapshot_item_data)

            tasks_snapshot.append(tasks_snapshot_item)

        def _parse_retry_feedback(data: object) -> None | RetryFeedback | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                retry_feedback_type_0 = RetryFeedback.from_dict(data)

                return retry_feedback_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RetryFeedback | Unset, data)

        retry_feedback = _parse_retry_feedback(d.pop("retry_feedback", UNSET))

        crew_run_metadata_create = cls(
            inputs=inputs,
            tasks_snapshot=tasks_snapshot,
            retry_feedback=retry_feedback,
        )

        crew_run_metadata_create.additional_properties = d
        return crew_run_metadata_create

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
