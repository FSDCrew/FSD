from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="HeartbeatResponse")


@_attrs_define
class HeartbeatResponse:
    """
    Attributes:
        cancel_requested (bool):
        queue_id (UUID):
        visible_at (datetime.datetime):
        status (str):
    """

    cancel_requested: bool
    queue_id: UUID
    visible_at: datetime.datetime
    status: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cancel_requested = self.cancel_requested

        queue_id = str(self.queue_id)

        visible_at = self.visible_at.isoformat()

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "cancel_requested": cancel_requested,
                "queue_id": queue_id,
                "visible_at": visible_at,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cancel_requested = d.pop("cancel_requested")

        queue_id = UUID(d.pop("queue_id"))

        visible_at = isoparse(d.pop("visible_at"))

        status = d.pop("status")

        heartbeat_response = cls(
            cancel_requested=cancel_requested,
            queue_id=queue_id,
            visible_at=visible_at,
            status=status,
        )

        heartbeat_response.additional_properties = d
        return heartbeat_response

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
