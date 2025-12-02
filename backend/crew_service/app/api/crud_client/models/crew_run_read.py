from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.queue_status import QueueStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.artifact_read import ArtifactRead
    from ..models.crew_run_metadata_read import CrewRunMetadataRead
    from ..models.crew_run_read_output_type_0 import CrewRunReadOutputType0


T = TypeVar("T", bound="CrewRunRead")


@_attrs_define
class CrewRunRead:
    """
    Attributes:
        id (UUID):
        crew_id (UUID):
        run_metadata (CrewRunMetadataRead):
        output (CrewRunReadOutputType0 | None | Unset):
        artifacts (list[ArtifactRead] | None | Unset):
        queue_status (None | QueueStatus | Unset):
        retry_count (int | None | Unset):
    """

    id: UUID
    crew_id: UUID
    run_metadata: CrewRunMetadataRead
    output: CrewRunReadOutputType0 | None | Unset = UNSET
    artifacts: list[ArtifactRead] | None | Unset = UNSET
    queue_status: None | QueueStatus | Unset = UNSET
    retry_count: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.crew_run_read_output_type_0 import CrewRunReadOutputType0

        id = str(self.id)

        crew_id = str(self.crew_id)

        run_metadata = self.run_metadata.to_dict()

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

        queue_status: None | str | Unset
        if isinstance(self.queue_status, Unset):
            queue_status = UNSET
        elif isinstance(self.queue_status, QueueStatus):
            queue_status = self.queue_status.value
        else:
            queue_status = self.queue_status

        retry_count: int | None | Unset
        if isinstance(self.retry_count, Unset):
            retry_count = UNSET
        else:
            retry_count = self.retry_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "crew_id": crew_id,
                "run_metadata": run_metadata,
            }
        )
        if output is not UNSET:
            field_dict["output"] = output
        if artifacts is not UNSET:
            field_dict["artifacts"] = artifacts
        if queue_status is not UNSET:
            field_dict["queue_status"] = queue_status
        if retry_count is not UNSET:
            field_dict["retry_count"] = retry_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.artifact_read import ArtifactRead
        from ..models.crew_run_metadata_read import CrewRunMetadataRead
        from ..models.crew_run_read_output_type_0 import CrewRunReadOutputType0

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        crew_id = UUID(d.pop("crew_id"))

        run_metadata = CrewRunMetadataRead.from_dict(d.pop("run_metadata"))

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

        def _parse_queue_status(data: object) -> None | QueueStatus | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                queue_status_type_0 = QueueStatus(data)

                return queue_status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | QueueStatus | Unset, data)

        queue_status = _parse_queue_status(d.pop("queue_status", UNSET))

        def _parse_retry_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        retry_count = _parse_retry_count(d.pop("retry_count", UNSET))

        crew_run_read = cls(
            id=id,
            crew_id=crew_id,
            run_metadata=run_metadata,
            output=output,
            artifacts=artifacts,
            queue_status=queue_status,
            retry_count=retry_count,
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
