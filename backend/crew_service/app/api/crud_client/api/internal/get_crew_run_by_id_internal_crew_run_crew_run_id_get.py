from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.crew_run_read import CrewRunRead
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    crew_run_id: UUID,
    *,
    x_internal_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_internal_api_key, Unset):
        headers["X-Internal-Api-Key"] = x_internal_api_key

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/internal/crew-run/{crew_run_id}".format(
            crew_run_id=crew_run_id,
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CrewRunRead | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CrewRunRead.from_dict(response.json())

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
) -> Response[CrewRunRead | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    crew_run_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> Response[CrewRunRead | HTTPValidationError]:
    """Get Crew Run By Id

     Get a single crew run by ID (internal use only).

    Args:
        crew_run_id (UUID): Crew Run ID to retrieve
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CrewRunRead | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        crew_run_id=crew_run_id,
        x_internal_api_key=x_internal_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    crew_run_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> CrewRunRead | HTTPValidationError | None:
    """Get Crew Run By Id

     Get a single crew run by ID (internal use only).

    Args:
        crew_run_id (UUID): Crew Run ID to retrieve
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CrewRunRead | HTTPValidationError
    """

    return sync_detailed(
        crew_run_id=crew_run_id,
        client=client,
        x_internal_api_key=x_internal_api_key,
    ).parsed


async def asyncio_detailed(
    crew_run_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> Response[CrewRunRead | HTTPValidationError]:
    """Get Crew Run By Id

     Get a single crew run by ID (internal use only).

    Args:
        crew_run_id (UUID): Crew Run ID to retrieve
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CrewRunRead | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        crew_run_id=crew_run_id,
        x_internal_api_key=x_internal_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    crew_run_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> CrewRunRead | HTTPValidationError | None:
    """Get Crew Run By Id

     Get a single crew run by ID (internal use only).

    Args:
        crew_run_id (UUID): Crew Run ID to retrieve
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CrewRunRead | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            crew_run_id=crew_run_id,
            client=client,
            x_internal_api_key=x_internal_api_key,
        )
    ).parsed
