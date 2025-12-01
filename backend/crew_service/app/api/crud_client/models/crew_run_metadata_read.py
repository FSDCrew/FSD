from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.crew_run_metadata_read_inputs import CrewRunMetadataReadInputs
    from ..models.task_info import TaskInfo


T = TypeVar("T", bound="CrewRunMetadataRead")


@_attrs_define
class CrewRunMetadataRead:
    """
    Attributes:
        inputs (CrewRunMetadataReadInputs):
        tasks_snapshot (list[TaskInfo]):
    """

    inputs: CrewRunMetadataReadInputs
    tasks_snapshot: list[TaskInfo]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        inputs = self.inputs.to_dict()

        tasks_snapshot = []
        for tasks_snapshot_item_data in self.tasks_snapshot:
            tasks_snapshot_item = tasks_snapshot_item_data.to_dict()
            tasks_snapshot.append(tasks_snapshot_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "inputs": inputs,
                "tasks_snapshot": tasks_snapshot,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.crew_run_metadata_read_inputs import CrewRunMetadataReadInputs
        from ..models.task_info import TaskInfo

        d = dict(src_dict)
        inputs = CrewRunMetadataReadInputs.from_dict(d.pop("inputs"))

        tasks_snapshot = []
        _tasks_snapshot = d.pop("tasks_snapshot")
        for tasks_snapshot_item_data in _tasks_snapshot:
            tasks_snapshot_item = TaskInfo.from_dict(tasks_snapshot_item_data)

            tasks_snapshot.append(tasks_snapshot_item)

        crew_run_metadata_read = cls(
            inputs=inputs,
            tasks_snapshot=tasks_snapshot,
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
