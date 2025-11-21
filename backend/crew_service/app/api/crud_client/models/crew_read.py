from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.agent import Agent
    from ..models.task_read import TaskRead


T = TypeVar("T", bound="CrewRead")


@_attrs_define
class CrewRead:
    """
    Attributes:
        name (str):
        id (UUID):
        user_id (UUID):
        tasks (list[TaskRead]):
        agents (list[Agent]):
    """

    name: str
    id: UUID
    user_id: UUID
    tasks: list[TaskRead]
    agents: list[Agent]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id = str(self.id)

        user_id = str(self.user_id)

        tasks = []
        for tasks_item_data in self.tasks:
            tasks_item = tasks_item_data.to_dict()
            tasks.append(tasks_item)

        agents = []
        for agents_item_data in self.agents:
            agents_item = agents_item_data.to_dict()
            agents.append(agents_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "id": id,
                "user_id": user_id,
                "tasks": tasks,
                "agents": agents,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent import Agent
        from ..models.task_read import TaskRead

        d = dict(src_dict)
        name = d.pop("name")

        id = UUID(d.pop("id"))

        user_id = UUID(d.pop("user_id"))

        tasks = []
        _tasks = d.pop("tasks")
        for tasks_item_data in _tasks:
            tasks_item = TaskRead.from_dict(tasks_item_data)

            tasks.append(tasks_item)

        agents = []
        _agents = d.pop("agents")
        for agents_item_data in _agents:
            agents_item = Agent.from_dict(agents_item_data)

            agents.append(agents_item)

        crew_read = cls(
            name=name,
            id=id,
            user_id=user_id,
            tasks=tasks,
            agents=agents,
        )

        crew_read.additional_properties = d
        return crew_read

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
