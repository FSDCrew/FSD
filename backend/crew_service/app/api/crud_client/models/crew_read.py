from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.crew_run_read import CrewRunRead
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
        crew_runs (list[CrewRunRead] | None | Unset):
    """

    name: str
    id: UUID
    user_id: UUID
    tasks: list[TaskRead]
    crew_runs: list[CrewRunRead] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id = str(self.id)

        user_id = str(self.user_id)

        tasks = []
        for tasks_item_data in self.tasks:
            tasks_item = tasks_item_data.to_dict()
            tasks.append(tasks_item)

        crew_runs: list[dict[str, Any]] | None | Unset
        if isinstance(self.crew_runs, Unset):
            crew_runs = UNSET
        elif isinstance(self.crew_runs, list):
            crew_runs = []
            for crew_runs_type_0_item_data in self.crew_runs:
                crew_runs_type_0_item = crew_runs_type_0_item_data.to_dict()
                crew_runs.append(crew_runs_type_0_item)

        else:
            crew_runs = self.crew_runs

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "id": id,
                "user_id": user_id,
                "tasks": tasks,
            }
        )
        if crew_runs is not UNSET:
            field_dict["crew_runs"] = crew_runs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.crew_run_read import CrewRunRead
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

        def _parse_crew_runs(data: object) -> list[CrewRunRead] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                crew_runs_type_0 = []
                _crew_runs_type_0 = data
                for crew_runs_type_0_item_data in _crew_runs_type_0:
                    crew_runs_type_0_item = CrewRunRead.from_dict(
                        crew_runs_type_0_item_data
                    )

                    crew_runs_type_0.append(crew_runs_type_0_item)

                return crew_runs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[CrewRunRead] | None | Unset, data)

        crew_runs = _parse_crew_runs(d.pop("crew_runs", UNSET))

        crew_read = cls(
            name=name,
            id=id,
            user_id=user_id,
            tasks=tasks,
            crew_runs=crew_runs,
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
