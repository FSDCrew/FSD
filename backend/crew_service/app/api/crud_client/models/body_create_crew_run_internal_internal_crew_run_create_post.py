from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.crew_run_create import CrewRunCreate


T = TypeVar("T", bound="BodyCreateCrewRunInternalInternalCrewRunCreatePost")


@_attrs_define
class BodyCreateCrewRunInternalInternalCrewRunCreatePost:
    """
    Attributes:
        crew_run_data (CrewRunCreate):
        user_token (str): User's JWT token for authentication
    """

    crew_run_data: CrewRunCreate
    user_token: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        crew_run_data = self.crew_run_data.to_dict()

        user_token = self.user_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "crew_run_data": crew_run_data,
                "user_token": user_token,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.crew_run_create import CrewRunCreate

        d = dict(src_dict)
        crew_run_data = CrewRunCreate.from_dict(d.pop("crew_run_data"))

        user_token = d.pop("user_token")

        body_create_crew_run_internal_internal_crew_run_create_post = cls(
            crew_run_data=crew_run_data,
            user_token=user_token,
        )

        body_create_crew_run_internal_internal_crew_run_create_post.additional_properties = d
        return body_create_crew_run_internal_internal_crew_run_create_post

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
