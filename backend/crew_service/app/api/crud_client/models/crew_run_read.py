from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.artifact_read import ArtifactRead
    from ..models.crew_run_read_output_type_0 import CrewRunReadOutputType0


T = TypeVar("T", bound="CrewRunRead")


@_attrs_define
class CrewRunRead:
    """
    Attributes:
        id (UUID):
        output (CrewRunReadOutputType0 | None | Unset):
        artifacts (list[ArtifactRead] | None | Unset):
    """

    id: UUID
    output: CrewRunReadOutputType0 | None | Unset = UNSET
    artifacts: list[ArtifactRead] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.crew_run_read_output_type_0 import CrewRunReadOutputType0

        id = str(self.id)

        output: dict[str, Any] | None | Unset
        if isinstance(self.output, Unset):
            output = UNSET
        elif isinstance(self.output, CrewRunReadOutputType0):
            output = self.output.to_dict()
        else:
            output = self.output

        artifacts: list[dict[str, Any]] | None | Unset
        if isinstance(self.artifacts, Unset):
            artifacts = UNSET
        elif isinstance(self.artifacts, list):
            artifacts = []
            for artifacts_type_0_item_data in self.artifacts:
                artifacts_type_0_item = artifacts_type_0_item_data.to_dict()
                artifacts.append(artifacts_type_0_item)

        else:
            artifacts = self.artifacts

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if output is not UNSET:
            field_dict["output"] = output
        if artifacts is not UNSET:
            field_dict["artifacts"] = artifacts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.artifact_read import ArtifactRead
        from ..models.crew_run_read_output_type_0 import CrewRunReadOutputType0

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        def _parse_output(data: object) -> CrewRunReadOutputType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                output_type_0 = CrewRunReadOutputType0.from_dict(data)

                return output_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CrewRunReadOutputType0 | None | Unset, data)

        output = _parse_output(d.pop("output", UNSET))

        def _parse_artifacts(data: object) -> list[ArtifactRead] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                artifacts_type_0 = []
                _artifacts_type_0 = data
                for artifacts_type_0_item_data in _artifacts_type_0:
                    artifacts_type_0_item = ArtifactRead.from_dict(
                        artifacts_type_0_item_data
                    )

                    artifacts_type_0.append(artifacts_type_0_item)

                return artifacts_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ArtifactRead] | None | Unset, data)

        artifacts = _parse_artifacts(d.pop("artifacts", UNSET))

        crew_run_read = cls(
            id=id,
            output=output,
            artifacts=artifacts,
        )

        crew_run_read.additional_properties = d
        return crew_run_read

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
