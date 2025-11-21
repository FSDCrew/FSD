from http import HTTPStatus
from typing import Any, cast
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.claim_job_response import ClaimJobResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.update_status_request import UpdateStatusRequest
from ...types import Response


def _get_kwargs(
    queue_id: UUID,
    *,
    body: UpdateStatusRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/queue/{queue_id}/status".format(
            queue_id=queue_id,
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ClaimJobResponse | None | HTTPValidationError | None:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> ClaimJobResponse | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = ClaimJobResponse.from_dict(data)

                return response_200_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ClaimJobResponse | None, data)

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
) -> Response[ClaimJobResponse | None | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    queue_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateStatusRequest,
) -> Response[ClaimJobResponse | None | HTTPValidationError]:
    """Update Queue Status

     Update the status of a queue entry.
    Requires valid lease_token so that only the worker that claimed the job can update the status.
    This prevents zombie workers from updating the status after they've lost the lease.

    Args:
        queue_id (UUID):
        body (UpdateStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClaimJobResponse | None | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    queue_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateStatusRequest,
) -> ClaimJobResponse | None | HTTPValidationError | None:
    """Update Queue Status

     Update the status of a queue entry.
    Requires valid lease_token so that only the worker that claimed the job can update the status.
    This prevents zombie workers from updating the status after they've lost the lease.

    Args:
        queue_id (UUID):
        body (UpdateStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClaimJobResponse | None | HTTPValidationError
    """

    return sync_detailed(
        queue_id=queue_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    queue_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateStatusRequest,
) -> Response[ClaimJobResponse | None | HTTPValidationError]:
    """Update Queue Status

     Update the status of a queue entry.
    Requires valid lease_token so that only the worker that claimed the job can update the status.
    This prevents zombie workers from updating the status after they've lost the lease.

    Args:
        queue_id (UUID):
        body (UpdateStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClaimJobResponse | None | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    queue_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateStatusRequest,
) -> ClaimJobResponse | None | HTTPValidationError | None:
    """Update Queue Status

     Update the status of a queue entry.
    Requires valid lease_token so that only the worker that claimed the job can update the status.
    This prevents zombie workers from updating the status after they've lost the lease.

    Args:
        queue_id (UUID):
        body (UpdateStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClaimJobResponse | None | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            client=client,
            body=body,
        )
    ).parsed
