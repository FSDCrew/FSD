from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.crew_run_create_request_inputs_type_0 import (
        CrewRunCreateRequestInputsType0,
    )


T = TypeVar("T", bound="CrewRunCreateRequest")


@_attrs_define
class CrewRunCreateRequest:
    """
    Attributes:
        crew_id (UUID):
        inputs (CrewRunCreateRequestInputsType0 | None | Unset):
    """

    crew_id: UUID
    inputs: CrewRunCreateRequestInputsType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.crew_run_create_request_inputs_type_0 import (
            CrewRunCreateRequestInputsType0,
        )

        crew_id = str(self.crew_id)

        inputs: dict[str, Any] | None | Unset
        if isinstance(self.inputs, Unset):
            inputs = UNSET
        elif isinstance(self.inputs, CrewRunCreateRequestInputsType0):
            inputs = self.inputs.to_dict()
        else:
            inputs = self.inputs

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "crew_id": crew_id,
            }
        )
        if inputs is not UNSET:
            field_dict["inputs"] = inputs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.crew_run_create_request_inputs_type_0 import (
            CrewRunCreateRequestInputsType0,
        )

        d = dict(src_dict)
        crew_id = UUID(d.pop("crew_id"))

        def _parse_inputs(
            data: object,
        ) -> CrewRunCreateRequestInputsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                inputs_type_0 = CrewRunCreateRequestInputsType0.from_dict(data)

                return inputs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CrewRunCreateRequestInputsType0 | None | Unset, data)

        inputs = _parse_inputs(d.pop("inputs", UNSET))

        crew_run_create_request = cls(
            crew_id=crew_id,
            inputs=inputs,
        )

        crew_run_create_request.additional_properties = d
        return crew_run_create_request

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
