from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.crew_run_metadata_create import CrewRunMetadataCreate
    from ..models.crew_run_output_create import CrewRunOutputCreate


T = TypeVar("T", bound="CrewRunCreate")


@_attrs_define
class CrewRunCreate:
    """
    Attributes:
        crew_id (UUID):
        run_metadata (CrewRunMetadataCreate):
        output (CrewRunOutputCreate):
    """

    crew_id: UUID
    run_metadata: CrewRunMetadataCreate
    output: CrewRunOutputCreate
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        crew_id = str(self.crew_id)

        run_metadata = self.run_metadata.to_dict()

        output = self.output.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "crew_id": crew_id,
                "run_metadata": run_metadata,
                "output": output,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.crew_run_metadata_create import CrewRunMetadataCreate
        from ..models.crew_run_output_create import CrewRunOutputCreate

        d = dict(src_dict)
        crew_id = UUID(d.pop("crew_id"))

        run_metadata = CrewRunMetadataCreate.from_dict(d.pop("run_metadata"))

        output = CrewRunOutputCreate.from_dict(d.pop("output"))

        crew_run_create = cls(
            crew_id=crew_id,
            run_metadata=run_metadata,
            output=output,
        )

        crew_run_create.additional_properties = d
        return crew_run_create

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
