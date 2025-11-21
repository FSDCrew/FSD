from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.crew_read import CrewRead
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    crew_id: None | Unset | UUID = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_crew_id: None | str | Unset
    if isinstance(crew_id, Unset):
        json_crew_id = UNSET
    elif isinstance(crew_id, UUID):
        json_crew_id = str(crew_id)
    else:
        json_crew_id = crew_id
    params["crew_id"] = json_crew_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/crew/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CrewRead | list[CrewRead] | HTTPValidationError | None:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> CrewRead | list[CrewRead]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = CrewRead.from_dict(data)

                return response_200_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, list):
                raise TypeError()
            response_200_type_1 = []
            _response_200_type_1 = data
            for response_200_type_1_item_data in _response_200_type_1:
                response_200_type_1_item = CrewRead.from_dict(
                    response_200_type_1_item_data
                )

                response_200_type_1.append(response_200_type_1_item)

            return response_200_type_1

        response_200 = _parse_response_200(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CrewRead | list[CrewRead] | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    crew_id: None | Unset | UUID = UNSET,
) -> Response[CrewRead | list[CrewRead] | HTTPValidationError]:
    """Get Crews

     Get crews, optionally filtered by crew_id.

    Args:
        crew_id (None | Unset | UUID): Optional Crew ID to filter

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CrewRead | list[CrewRead] | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        crew_id=crew_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    crew_id: None | Unset | UUID = UNSET,
) -> CrewRead | list[CrewRead] | HTTPValidationError | None:
    """Get Crews

     Get crews, optionally filtered by crew_id.

    Args:
        crew_id (None | Unset | UUID): Optional Crew ID to filter

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CrewRead | list[CrewRead] | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        crew_id=crew_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    crew_id: None | Unset | UUID = UNSET,
) -> Response[CrewRead | list[CrewRead] | HTTPValidationError]:
    """Get Crews

     Get crews, optionally filtered by crew_id.

    Args:
        crew_id (None | Unset | UUID): Optional Crew ID to filter

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CrewRead | list[CrewRead] | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        crew_id=crew_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    crew_id: None | Unset | UUID = UNSET,
) -> CrewRead | list[CrewRead] | HTTPValidationError | None:
    """Get Crews

     Get crews, optionally filtered by crew_id.

    Args:
        crew_id (None | Unset | UUID): Optional Crew ID to filter

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CrewRead | list[CrewRead] | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            crew_id=crew_id,
        )
    ).parsed
