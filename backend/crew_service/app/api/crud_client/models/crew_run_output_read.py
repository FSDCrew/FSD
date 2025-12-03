from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.crew_run_output_read_flow_state_type_0 import (
        CrewRunOutputReadFlowStateType0,
    )
    from ..models.crew_run_output_read_task_states import CrewRunOutputReadTaskStates


T = TypeVar("T", bound="CrewRunOutputRead")


@_attrs_define
class CrewRunOutputRead:
    """
    Attributes:
        flow_state (CrewRunOutputReadFlowStateType0 | None | Unset):
        task_states (CrewRunOutputReadTaskStates | Unset):
    """

    flow_state: CrewRunOutputReadFlowStateType0 | None | Unset = UNSET
    task_states: CrewRunOutputReadTaskStates | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.crew_run_output_read_flow_state_type_0 import (
            CrewRunOutputReadFlowStateType0,
        )

        flow_state: dict[str, Any] | None | Unset
        if isinstance(self.flow_state, Unset):
            flow_state = UNSET
        elif isinstance(self.flow_state, CrewRunOutputReadFlowStateType0):
            flow_state = self.flow_state.to_dict()
        else:
            flow_state = self.flow_state

        task_states: dict[str, Any] | Unset = UNSET
        if not isinstance(self.task_states, Unset):
            task_states = self.task_states.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if flow_state is not UNSET:
            field_dict["flow_state"] = flow_state
        if task_states is not UNSET:
            field_dict["task_states"] = task_states

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.crew_run_output_read_flow_state_type_0 import (
            CrewRunOutputReadFlowStateType0,
        )
        from ..models.crew_run_output_read_task_states import (
            CrewRunOutputReadTaskStates,
        )

        d = dict(src_dict)

        def _parse_flow_state(
            data: object,
        ) -> CrewRunOutputReadFlowStateType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                flow_state_type_0 = CrewRunOutputReadFlowStateType0.from_dict(data)

                return flow_state_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CrewRunOutputReadFlowStateType0 | None | Unset, data)

        flow_state = _parse_flow_state(d.pop("flow_state", UNSET))

        _task_states = d.pop("task_states", UNSET)
        task_states: CrewRunOutputReadTaskStates | Unset
        if isinstance(_task_states, Unset):
            task_states = UNSET
        else:
            task_states = CrewRunOutputReadTaskStates.from_dict(_task_states)

        crew_run_output_read = cls(
            flow_state=flow_state,
            task_states=task_states,
        )

        crew_run_output_read.additional_properties = d
        return crew_run_output_read

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
