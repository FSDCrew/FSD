from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.task_field_read import TaskFieldRead
    from ..models.task_field_write import TaskFieldWrite


T = TypeVar("T", bound="TaskInfo")


@_attrs_define
class TaskInfo:
    """
    Attributes:
        key (str):
        name (str):
        task_description (str):
        description (str):
        expected_output (str):
        agent (str):
        reads (list[TaskFieldRead]):
        writes (list[TaskFieldWrite]):
    """

    key: str
    name: str
    task_description: str
    description: str
    expected_output: str
    agent: str
    reads: list[TaskFieldRead]
    writes: list[TaskFieldWrite]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        name = self.name

        task_description = self.task_description

        description = self.description

        expected_output = self.expected_output

        agent = self.agent

        reads = []
        for reads_item_data in self.reads:
            reads_item = reads_item_data.to_dict()
            reads.append(reads_item)

        writes = []
        for writes_item_data in self.writes:
            writes_item = writes_item_data.to_dict()
            writes.append(writes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "key": key,
                "name": name,
                "task_description": task_description,
                "description": description,
                "expected_output": expected_output,
                "agent": agent,
                "reads": reads,
                "writes": writes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_field_read import TaskFieldRead
        from ..models.task_field_write import TaskFieldWrite

        d = dict(src_dict)
        key = d.pop("key")

        name = d.pop("name")

        task_description = d.pop("task_description")

        description = d.pop("description")

        expected_output = d.pop("expected_output")

        agent = d.pop("agent")

        reads = []
        _reads = d.pop("reads")
        for reads_item_data in _reads:
            reads_item = TaskFieldRead.from_dict(reads_item_data)

            reads.append(reads_item)

        writes = []
        _writes = d.pop("writes")
        for writes_item_data in _writes:
            writes_item = TaskFieldWrite.from_dict(writes_item_data)

            writes.append(writes_item)

        task_info = cls(
            key=key,
            name=name,
            task_description=task_description,
            description=description,
            expected_output=expected_output,
            agent=agent,
            reads=reads,
            writes=writes,
        )

        task_info.additional_properties = d
        return task_info

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
