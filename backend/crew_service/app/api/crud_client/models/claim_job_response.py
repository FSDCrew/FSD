from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.queue_status import QueueStatus

T = TypeVar("T", bound="ClaimJobResponse")


@_attrs_define
class ClaimJobResponse:
    """
    Attributes:
        id (UUID):
        crew_run_id (UUID):
        crew_id (UUID):
        status (QueueStatus):
        lease_token (str):
        visible_at (str):
    """

    id: UUID
    crew_run_id: UUID
    crew_id: UUID
    status: QueueStatus
    lease_token: str
    visible_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        crew_run_id = str(self.crew_run_id)

        crew_id = str(self.crew_id)

        status = self.status.value

        lease_token = self.lease_token

        visible_at = self.visible_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "crew_run_id": crew_run_id,
                "crew_id": crew_id,
                "status": status,
                "lease_token": lease_token,
                "visible_at": visible_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        crew_run_id = UUID(d.pop("crew_run_id"))

        crew_id = UUID(d.pop("crew_id"))

        status = QueueStatus(d.pop("status"))

        lease_token = d.pop("lease_token")

        visible_at = d.pop("visible_at")

        claim_job_response = cls(
            id=id,
            crew_run_id=crew_run_id,
            crew_id=crew_id,
            status=status,
            lease_token=lease_token,
            visible_at=visible_at,
        )

        claim_job_response.additional_properties = d
        return claim_job_response

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
