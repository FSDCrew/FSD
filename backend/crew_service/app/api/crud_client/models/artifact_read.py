from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.artifact_type import ArtifactType

T = TypeVar("T", bound="ArtifactRead")


@_attrs_define
class ArtifactRead:
    """
    Attributes:
        type_ (ArtifactType):
        file_name (None | str):
        id (UUID):
        crew_run_id (UUID):
    """

    type_: ArtifactType
    file_name: None | str
    id: UUID
    crew_run_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        file_name: None | str
        file_name = self.file_name

        id = str(self.id)

        crew_run_id = str(self.crew_run_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "file_name": file_name,
                "id": id,
                "crew_run_id": crew_run_id,
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

        id = UUID(d.pop("id"))

        crew_run_id = UUID(d.pop("crew_run_id"))

        artifact_read = cls(
            type_=type_,
            file_name=file_name,
            id=id,
            crew_run_id=crew_run_id,
        )

        artifact_read.additional_properties = d
        return artifact_read

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
