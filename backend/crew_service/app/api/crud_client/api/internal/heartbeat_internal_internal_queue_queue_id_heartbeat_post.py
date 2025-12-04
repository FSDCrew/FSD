from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.heartbeat_request import HeartbeatRequest
from ...models.heartbeat_response import HeartbeatResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    queue_id: UUID,
    *,
    body: HeartbeatRequest,
    visibility_timeout_seconds: int | Unset = 300,
    x_internal_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_internal_api_key, Unset):
        headers["X-Internal-Api-Key"] = x_internal_api_key

    params: dict[str, Any] = {}

    params["visibility_timeout_seconds"] = visibility_timeout_seconds

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/internal/queue/{queue_id}/heartbeat".format(
            queue_id=queue_id,
        ),
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | HeartbeatResponse | None:
    if response.status_code == 200:
        response_200 = HeartbeatResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | HeartbeatResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    queue_id: UUID,
    *,
    client: AuthenticatedClient,
    body: HeartbeatRequest,
    visibility_timeout_seconds: int | Unset = 300,
    x_internal_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | HeartbeatResponse]:
    """Heartbeat Internal

     Extend the visibility timeout (lease renewal) for a claimed job.

    Args:
        queue_id (UUID):
        visibility_timeout_seconds (int | Unset):  Default: 300.
        x_internal_api_key (None | str | Unset):
        body (HeartbeatRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | HeartbeatResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        body=body,
        visibility_timeout_seconds=visibility_timeout_seconds,
        x_internal_api_key=x_internal_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    queue_id: UUID,
    *,
    client: AuthenticatedClient,
    body: HeartbeatRequest,
    visibility_timeout_seconds: int | Unset = 300,
    x_internal_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | HeartbeatResponse | None:
    """Heartbeat Internal

     Extend the visibility timeout (lease renewal) for a claimed job.

    Args:
        queue_id (UUID):
        visibility_timeout_seconds (int | Unset):  Default: 300.
        x_internal_api_key (None | str | Unset):
        body (HeartbeatRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | HeartbeatResponse
    """

    return sync_detailed(
        queue_id=queue_id,
        client=client,
        body=body,
        visibility_timeout_seconds=visibility_timeout_seconds,
        x_internal_api_key=x_internal_api_key,
    ).parsed


async def asyncio_detailed(
    queue_id: UUID,
    *,
    client: AuthenticatedClient,
    body: HeartbeatRequest,
    visibility_timeout_seconds: int | Unset = 300,
    x_internal_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | HeartbeatResponse]:
    """Heartbeat Internal

     Extend the visibility timeout (lease renewal) for a claimed job.

    Args:
        queue_id (UUID):
        visibility_timeout_seconds (int | Unset):  Default: 300.
        x_internal_api_key (None | str | Unset):
        body (HeartbeatRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | HeartbeatResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        body=body,
        visibility_timeout_seconds=visibility_timeout_seconds,
        x_internal_api_key=x_internal_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    queue_id: UUID,
    *,
    client: AuthenticatedClient,
    body: HeartbeatRequest,
    visibility_timeout_seconds: int | Unset = 300,
    x_internal_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | HeartbeatResponse | None:
    """Heartbeat Internal

     Extend the visibility timeout (lease renewal) for a claimed job.

    Args:
        queue_id (UUID):
        visibility_timeout_seconds (int | Unset):  Default: 300.
        x_internal_api_key (None | str | Unset):
        body (HeartbeatRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | HeartbeatResponse
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            client=client,
            body=body,
            visibility_timeout_seconds=visibility_timeout_seconds,
            x_internal_api_key=x_internal_api_key,
        )
    ).parsed
