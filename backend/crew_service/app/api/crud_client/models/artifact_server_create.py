from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.artifact_type import ArtifactType

T = TypeVar("T", bound="ArtifactServerCreate")


@_attrs_define
class ArtifactServerCreate:
    """
    Attributes:
        type_ (ArtifactType):
        file_name (None | str):
        file_content_base64 (str):
    """

    type_: ArtifactType
    file_name: None | str
    file_content_base64: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        file_name: None | str
        file_name = self.file_name

        file_content_base64 = self.file_content_base64

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "file_name": file_name,
                "file_content_base64": file_content_base64,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = ArtifactType(d.pop("type"))

        def _parse_file_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        file_name = _parse_file_name(d.pop("file_name"))

        file_content_base64 = d.pop("file_content_base64")

        artifact_server_create = cls(
            type_=type_,
            file_name=file_name,
            file_content_base64=file_content_base64,
        )

        artifact_server_create.additional_properties = d
        return artifact_server_create

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
