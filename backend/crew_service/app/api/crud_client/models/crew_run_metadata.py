from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.crew_run_metadata_inputs import CrewRunMetadataInputs
    from ..models.task_info import TaskInfo


T = TypeVar("T", bound="CrewRunMetadata")


@_attrs_define
class CrewRunMetadata:
    """
    Attributes:
        inputs (CrewRunMetadataInputs):
        task_snapshot (list[TaskInfo] | None | Unset):
    """

    inputs: CrewRunMetadataInputs
    task_snapshot: list[TaskInfo] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        inputs = self.inputs.to_dict()

        task_snapshot: list[dict[str, Any]] | None | Unset
        if isinstance(self.task_snapshot, Unset):
            task_snapshot = UNSET
        elif isinstance(self.task_snapshot, list):
            task_snapshot = []
            for task_snapshot_type_0_item_data in self.task_snapshot:
                task_snapshot_type_0_item = task_snapshot_type_0_item_data.to_dict()
                task_snapshot.append(task_snapshot_type_0_item)

        else:
            task_snapshot = self.task_snapshot

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "inputs": inputs,
            }
        )
        if task_snapshot is not UNSET:
            field_dict["task_snapshot"] = task_snapshot

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.crew_run_metadata_inputs import CrewRunMetadataInputs
        from ..models.task_info import TaskInfo

        d = dict(src_dict)
        inputs = CrewRunMetadataInputs.from_dict(d.pop("inputs"))

        def _parse_task_snapshot(data: object) -> list[TaskInfo] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                task_snapshot_type_0 = []
                _task_snapshot_type_0 = data
                for task_snapshot_type_0_item_data in _task_snapshot_type_0:
                    task_snapshot_type_0_item = TaskInfo.from_dict(
                        task_snapshot_type_0_item_data
                    )

                    task_snapshot_type_0.append(task_snapshot_type_0_item)

                return task_snapshot_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[TaskInfo] | None | Unset, data)

        task_snapshot = _parse_task_snapshot(d.pop("task_snapshot", UNSET))

        crew_run_metadata = cls(
            inputs=inputs,
            task_snapshot=task_snapshot,
        )

        crew_run_metadata.additional_properties = d
        return crew_run_metadata

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
