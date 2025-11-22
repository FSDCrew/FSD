from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """
    Attributes:
        id (UUID):
        email (str):
        name (str):
        given_name (str):
        family_name (str):
        picture (None | str):
    """

    id: UUID
    email: str
    name: str
    given_name: str
    family_name: str
    picture: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        email = self.email

        name = self.name

        given_name = self.given_name

        family_name = self.family_name

        picture: None | str
        picture = self.picture

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "email": email,
                "name": name,
                "given_name": given_name,
                "family_name": family_name,
                "picture": picture,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        email = d.pop("email")

        name = d.pop("name")

        given_name = d.pop("given_name")

        family_name = d.pop("family_name")

        def _parse_picture(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        picture = _parse_picture(d.pop("picture"))

        user = cls(
            id=id,
            email=email,
            name=name,
            given_name=given_name,
            family_name=family_name,
            picture=picture,
        )

        user.additional_properties = d
        return user

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
