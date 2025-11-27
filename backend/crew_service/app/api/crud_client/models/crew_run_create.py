from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.crew_run_create_output_type_0 import CrewRunCreateOutputType0
    from ..models.crew_run_metadata import CrewRunMetadata


T = TypeVar("T", bound="CrewRunCreate")


@_attrs_define
class CrewRunCreate:
    """
    Attributes:
        crew_id (UUID):
        output (CrewRunCreateOutputType0 | None | Unset):
        run_metadata (CrewRunMetadata | None | Unset):
    """

    crew_id: UUID
    output: CrewRunCreateOutputType0 | None | Unset = UNSET
    run_metadata: CrewRunMetadata | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.crew_run_create_output_type_0 import CrewRunCreateOutputType0
        from ..models.crew_run_metadata import CrewRunMetadata

        crew_id = str(self.crew_id)

        output: dict[str, Any] | None | Unset
        if isinstance(self.output, Unset):
            output = UNSET
        elif isinstance(self.output, CrewRunCreateOutputType0):
            output = self.output.to_dict()
        else:
            output = self.output

        run_metadata: dict[str, Any] | None | Unset
        if isinstance(self.run_metadata, Unset):
            run_metadata = UNSET
        elif isinstance(self.run_metadata, CrewRunMetadata):
            run_metadata = self.run_metadata.to_dict()
        else:
            run_metadata = self.run_metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "crew_id": crew_id,
            }
        )
        if output is not UNSET:
            field_dict["output"] = output
        if run_metadata is not UNSET:
            field_dict["run_metadata"] = run_metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.crew_run_create_output_type_0 import CrewRunCreateOutputType0
        from ..models.crew_run_metadata import CrewRunMetadata

        d = dict(src_dict)
        crew_id = UUID(d.pop("crew_id"))

        def _parse_output(data: object) -> CrewRunCreateOutputType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                output_type_0 = CrewRunCreateOutputType0.from_dict(data)

                return output_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CrewRunCreateOutputType0 | None | Unset, data)

        output = _parse_output(d.pop("output", UNSET))

        def _parse_run_metadata(data: object) -> CrewRunMetadata | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                run_metadata_type_0 = CrewRunMetadata.from_dict(data)

                return run_metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CrewRunMetadata | None | Unset, data)

        run_metadata = _parse_run_metadata(d.pop("run_metadata", UNSET))

        crew_run_create = cls(
            crew_id=crew_id,
            output=output,
            run_metadata=run_metadata,
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
