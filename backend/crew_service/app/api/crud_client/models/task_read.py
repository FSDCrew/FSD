from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TaskRead")


@_attrs_define
class TaskRead:
    """
    Attributes:
        key (str):
        description (str):
        expected_output (str):
        order (int):
        id (UUID):
        agent_key (str):
    """

    key: str
    description: str
    expected_output: str
    order: int
    id: UUID
    agent_key: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        description = self.description

        expected_output = self.expected_output

        order = self.order

        id = str(self.id)

        agent_key = self.agent_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "key": key,
                "description": description,
                "expected_output": expected_output,
                "order": order,
                "id": id,
                "agent_key": agent_key,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key")

        description = d.pop("description")

        expected_output = d.pop("expected_output")

        order = d.pop("order")

        id = UUID(d.pop("id"))

        agent_key = d.pop("agent_key")

        task_read = cls(
            key=key,
            description=description,
            expected_output=expected_output,
            order=order,
            id=id,
            agent_key=agent_key,
        )

        task_read.additional_properties = d
        return task_read

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
