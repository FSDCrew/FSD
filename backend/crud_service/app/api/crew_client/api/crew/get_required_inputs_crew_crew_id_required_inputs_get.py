from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.required_inputs_response import RequiredInputsResponse
from ...types import Response


def _get_kwargs(
    crew_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/crew/{crew_id}/required-inputs".format(
            crew_id=crew_id,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RequiredInputsResponse | None:
    if response.status_code == 200:
        response_200 = RequiredInputsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | RequiredInputsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    crew_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | RequiredInputsResponse]:
    """Get Required Inputs

     Get required inputs for a crew based on its tasks and flow dependencies.

    Args:
        crew_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RequiredInputsResponse]
    """

    kwargs = _get_kwargs(
        crew_id=crew_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    crew_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | RequiredInputsResponse | None:
    """Get Required Inputs

     Get required inputs for a crew based on its tasks and flow dependencies.

    Args:
        crew_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RequiredInputsResponse
    """

    return sync_detailed(
        crew_id=crew_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    crew_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | RequiredInputsResponse]:
    """Get Required Inputs

     Get required inputs for a crew based on its tasks and flow dependencies.

    Args:
        crew_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RequiredInputsResponse]
    """

    kwargs = _get_kwargs(
        crew_id=crew_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    crew_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | RequiredInputsResponse | None:
    """Get Required Inputs

     Get required inputs for a crew based on its tasks and flow dependencies.

    Args:
        crew_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RequiredInputsResponse
    """

    return (
        await asyncio_detailed(
            crew_id=crew_id,
            client=client,
        )
    ).parsed
