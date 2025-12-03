from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.crew_run_metadata_read_inputs import CrewRunMetadataReadInputs
    from ..models.retry_feedback import RetryFeedback
    from ..models.task_info import TaskInfo


T = TypeVar("T", bound="CrewRunMetadataRead")


@_attrs_define
class CrewRunMetadataRead:
    """
    Attributes:
        inputs (CrewRunMetadataReadInputs):
        tasks_snapshot (list[TaskInfo]):
        retry_feedback (list[RetryFeedback] | None | Unset):
    """

    inputs: CrewRunMetadataReadInputs
    tasks_snapshot: list[TaskInfo]
    retry_feedback: list[RetryFeedback] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        inputs = self.inputs.to_dict()

        tasks_snapshot = []
        for tasks_snapshot_item_data in self.tasks_snapshot:
            tasks_snapshot_item = tasks_snapshot_item_data.to_dict()
            tasks_snapshot.append(tasks_snapshot_item)

        retry_feedback: list[dict[str, Any]] | None | Unset
        if isinstance(self.retry_feedback, Unset):
            retry_feedback = UNSET
        elif isinstance(self.retry_feedback, list):
            retry_feedback = []
            for retry_feedback_type_0_item_data in self.retry_feedback:
                retry_feedback_type_0_item = retry_feedback_type_0_item_data.to_dict()
                retry_feedback.append(retry_feedback_type_0_item)

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
        from ..models.crew_run_metadata_read_inputs import CrewRunMetadataReadInputs
        from ..models.retry_feedback import RetryFeedback
        from ..models.task_info import TaskInfo

        d = dict(src_dict)
        inputs = CrewRunMetadataReadInputs.from_dict(d.pop("inputs"))

        tasks_snapshot = []
        _tasks_snapshot = d.pop("tasks_snapshot")
        for tasks_snapshot_item_data in _tasks_snapshot:
            tasks_snapshot_item = TaskInfo.from_dict(tasks_snapshot_item_data)

            tasks_snapshot.append(tasks_snapshot_item)

        def _parse_retry_feedback(data: object) -> list[RetryFeedback] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                retry_feedback_type_0 = []
                _retry_feedback_type_0 = data
                for retry_feedback_type_0_item_data in _retry_feedback_type_0:
                    retry_feedback_type_0_item = RetryFeedback.from_dict(
                        retry_feedback_type_0_item_data
                    )

                    retry_feedback_type_0.append(retry_feedback_type_0_item)

                return retry_feedback_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[RetryFeedback] | None | Unset, data)

        retry_feedback = _parse_retry_feedback(d.pop("retry_feedback", UNSET))

        crew_run_metadata_read = cls(
            inputs=inputs,
            tasks_snapshot=tasks_snapshot,
            retry_feedback=retry_feedback,
        )

        crew_run_metadata_read.additional_properties = d
        return crew_run_metadata_read

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
