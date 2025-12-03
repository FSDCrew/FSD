from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.task_status import TaskStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_task_status_request_task_inputs import (
        UpdateTaskStatusRequestTaskInputs,
    )
    from ..models.update_task_status_request_task_outputs import (
        UpdateTaskStatusRequestTaskOutputs,
    )


T = TypeVar("T", bound="UpdateTaskStatusRequest")


@_attrs_define
class UpdateTaskStatusRequest:
    """Request model for updating task status.

    Attributes:
        status (TaskStatus):
        task_inputs (UpdateTaskStatusRequestTaskInputs):
        task_outputs (UpdateTaskStatusRequestTaskOutputs):
        completed_at (datetime.datetime | None | Unset):
    """

    status: TaskStatus
    task_inputs: UpdateTaskStatusRequestTaskInputs
    task_outputs: UpdateTaskStatusRequestTaskOutputs
    completed_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        task_inputs = self.task_inputs.to_dict()

        task_outputs = self.task_outputs.to_dict()

        completed_at: None | str | Unset
        if isinstance(self.completed_at, Unset):
            completed_at = UNSET
        elif isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "task_inputs": task_inputs,
                "task_outputs": task_outputs,
            }
        )
        if completed_at is not UNSET:
            field_dict["completed_at"] = completed_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_task_status_request_task_inputs import (
            UpdateTaskStatusRequestTaskInputs,
        )
        from ..models.update_task_status_request_task_outputs import (
            UpdateTaskStatusRequestTaskOutputs,
        )

        d = dict(src_dict)
        status = TaskStatus(d.pop("status"))

        task_inputs = UpdateTaskStatusRequestTaskInputs.from_dict(d.pop("task_inputs"))

        task_outputs = UpdateTaskStatusRequestTaskOutputs.from_dict(
            d.pop("task_outputs")
        )

        def _parse_completed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = isoparse(data)

                return completed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        completed_at = _parse_completed_at(d.pop("completed_at", UNSET))

        update_task_status_request = cls(
            status=status,
            task_inputs=task_inputs,
            task_outputs=task_outputs,
            completed_at=completed_at,
        )

        update_task_status_request.additional_properties = d
        return update_task_status_request

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
