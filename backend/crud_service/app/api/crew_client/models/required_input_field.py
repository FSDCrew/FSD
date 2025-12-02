from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.field_type_info import FieldTypeInfo


T = TypeVar("T", bound="RequiredInputField")


@_attrs_define
class RequiredInputField:
    """Represents a single required input field.

    Attributes:
        field_name (str): Name of the field
        type_info (FieldTypeInfo):
        field_kind (str): Field kind: 'context' or 'data'
        required (bool | Unset): Whether this field is required (cannot be left blank) Default: True.
        placeholder (None | str | Unset): Placeholder text for the input field
    """

    field_name: str
    type_info: FieldTypeInfo
    field_kind: str
    required: bool | Unset = True
    placeholder: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_name = self.field_name

        type_info = self.type_info.to_dict()

        field_kind = self.field_kind

        required = self.required

        placeholder: None | str | Unset
        if isinstance(self.placeholder, Unset):
            placeholder = UNSET
        else:
            placeholder = self.placeholder

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "field_name": field_name,
                "type_info": type_info,
                "field_kind": field_kind,
            }
        )
        if required is not UNSET:
            field_dict["required"] = required
        if placeholder is not UNSET:
            field_dict["placeholder"] = placeholder

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.field_type_info import FieldTypeInfo

        d = dict(src_dict)
        field_name = d.pop("field_name")

        type_info = FieldTypeInfo.from_dict(d.pop("type_info"))

        field_kind = d.pop("field_kind")

        required = d.pop("required", UNSET)

        def _parse_placeholder(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        placeholder = _parse_placeholder(d.pop("placeholder", UNSET))

        required_input_field = cls(
            field_name=field_name,
            type_info=type_info,
            field_kind=field_kind,
            required=required,
            placeholder=placeholder,
        )

        required_input_field.additional_properties = d
        return required_input_field

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
