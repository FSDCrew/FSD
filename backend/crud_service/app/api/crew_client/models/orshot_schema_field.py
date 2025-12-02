from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.orshot_data_type import OrshotDataType

T = TypeVar("T", bound="OrshotSchemaField")


@_attrs_define
class OrshotSchemaField:
    """Represents a single configurable field in an Orshot Template.
    User inputs a list of these objects to define the 'rules' for the template.

        Attributes:
            field (str): The exact parameter key to modify in the Orshot template (e.g., 'headline', 'background_image')
            data_type (OrshotDataType):
            description (str): Contextual description of the field (e.g., 'Main title, max 20 chars', 'Product shot in
                portrait mode')
    """

    field: str
    data_type: OrshotDataType
    description: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field = self.field

        data_type = self.data_type.value

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "field": field,
                "dataType": data_type,
                "description": description,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        field = d.pop("field")

        data_type = OrshotDataType(d.pop("dataType"))

        description = d.pop("description")

        orshot_schema_field = cls(
            field=field,
            data_type=data_type,
            description=description,
        )

        orshot_schema_field.additional_properties = d
        return orshot_schema_field

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
