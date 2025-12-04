from http import HTTPStatus
from typing import Any, cast
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    artifact_id: UUID,
    *,
    x_internal_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_internal_api_key, Unset):
        headers["X-Internal-Api-Key"] = x_internal_api_key

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/internal/artifact/{artifact_id}".format(
            artifact_id=artifact_id,
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | str | None:
    if response.status_code == 200:
        response_200 = cast(str, response.json())
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
) -> Response[HTTPValidationError | str]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    artifact_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | str]:
    """Get Artifact Internal

     Retrieve an artifact by its ID (internal use only).

    Args:
        artifact_id (UUID): Artifact ID to retrieve
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | str]
    """

    kwargs = _get_kwargs(
        artifact_id=artifact_id,
        x_internal_api_key=x_internal_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    artifact_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | str | None:
    """Get Artifact Internal

     Retrieve an artifact by its ID (internal use only).

    Args:
        artifact_id (UUID): Artifact ID to retrieve
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | str
    """

    return sync_detailed(
        artifact_id=artifact_id,
        client=client,
        x_internal_api_key=x_internal_api_key,
    ).parsed


async def asyncio_detailed(
    artifact_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | str]:
    """Get Artifact Internal

     Retrieve an artifact by its ID (internal use only).

    Args:
        artifact_id (UUID): Artifact ID to retrieve
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | str]
    """

    kwargs = _get_kwargs(
        artifact_id=artifact_id,
        x_internal_api_key=x_internal_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    artifact_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | str | None:
    """Get Artifact Internal

     Retrieve an artifact by its ID (internal use only).

    Args:
        artifact_id (UUID): Artifact ID to retrieve
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | str
    """

    return (
        await asyncio_detailed(
            artifact_id=artifact_id,
            client=client,
            x_internal_api_key=x_internal_api_key,
        )
    ).parsed
