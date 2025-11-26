from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.crew_run_metadata_inputs import CrewRunMetadataInputs
    from ..models.crew_run_metadata_task_nodes_type_0_item import (
        CrewRunMetadataTaskNodesType0Item,
    )


T = TypeVar("T", bound="CrewRunMetadata")


@_attrs_define
class CrewRunMetadata:
    """
    Attributes:
        inputs (CrewRunMetadataInputs):
        task_nodes (list[CrewRunMetadataTaskNodesType0Item] | None | Unset):
    """

    inputs: CrewRunMetadataInputs
    task_nodes: list[CrewRunMetadataTaskNodesType0Item] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        inputs = self.inputs.to_dict()

        task_nodes: list[dict[str, Any]] | None | Unset
        if isinstance(self.task_nodes, Unset):
            task_nodes = UNSET
        elif isinstance(self.task_nodes, list):
            task_nodes = []
            for task_nodes_type_0_item_data in self.task_nodes:
                task_nodes_type_0_item = task_nodes_type_0_item_data.to_dict()
                task_nodes.append(task_nodes_type_0_item)

        else:
            task_nodes = self.task_nodes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "inputs": inputs,
            }
        )
        if task_nodes is not UNSET:
            field_dict["task_nodes"] = task_nodes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.crew_run_metadata_inputs import CrewRunMetadataInputs
        from ..models.crew_run_metadata_task_nodes_type_0_item import (
            CrewRunMetadataTaskNodesType0Item,
        )

        d = dict(src_dict)
        inputs = CrewRunMetadataInputs.from_dict(d.pop("inputs"))

        def _parse_task_nodes(
            data: object,
        ) -> list[CrewRunMetadataTaskNodesType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                task_nodes_type_0 = []
                _task_nodes_type_0 = data
                for task_nodes_type_0_item_data in _task_nodes_type_0:
                    task_nodes_type_0_item = (
                        CrewRunMetadataTaskNodesType0Item.from_dict(
                            task_nodes_type_0_item_data
                        )
                    )

                    task_nodes_type_0.append(task_nodes_type_0_item)

                return task_nodes_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[CrewRunMetadataTaskNodesType0Item] | None | Unset, data)

        task_nodes = _parse_task_nodes(d.pop("task_nodes", UNSET))

        crew_run_metadata = cls(
            inputs=inputs,
            task_nodes=task_nodes,
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
