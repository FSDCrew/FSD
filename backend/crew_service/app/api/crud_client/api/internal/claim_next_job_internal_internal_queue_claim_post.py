from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.claim_job_response import ClaimJobResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
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
        "url": "/internal/queue/claim",
        "params": params,
    }

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
    *,
    client: AuthenticatedClient,
    visibility_timeout_seconds: int | Unset = 300,
    x_internal_api_key: None | str | Unset = UNSET,
) -> Response[ClaimJobResponse | None | HTTPValidationError]:
    """Claim Next Job Internal

     Claim the next available job from the queue (internal use only).

    Args:
        visibility_timeout_seconds (int | Unset):  Default: 300.
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClaimJobResponse | None | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        visibility_timeout_seconds=visibility_timeout_seconds,
        x_internal_api_key=x_internal_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    visibility_timeout_seconds: int | Unset = 300,
    x_internal_api_key: None | str | Unset = UNSET,
) -> ClaimJobResponse | None | HTTPValidationError | None:
    """Claim Next Job Internal

     Claim the next available job from the queue (internal use only).

    Args:
        visibility_timeout_seconds (int | Unset):  Default: 300.
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClaimJobResponse | None | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        visibility_timeout_seconds=visibility_timeout_seconds,
        x_internal_api_key=x_internal_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    visibility_timeout_seconds: int | Unset = 300,
    x_internal_api_key: None | str | Unset = UNSET,
) -> Response[ClaimJobResponse | None | HTTPValidationError]:
    """Claim Next Job Internal

     Claim the next available job from the queue (internal use only).

    Args:
        visibility_timeout_seconds (int | Unset):  Default: 300.
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClaimJobResponse | None | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        visibility_timeout_seconds=visibility_timeout_seconds,
        x_internal_api_key=x_internal_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    visibility_timeout_seconds: int | Unset = 300,
    x_internal_api_key: None | str | Unset = UNSET,
) -> ClaimJobResponse | None | HTTPValidationError | None:
    """Claim Next Job Internal

     Claim the next available job from the queue (internal use only).

    Args:
        visibility_timeout_seconds (int | Unset):  Default: 300.
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClaimJobResponse | None | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            visibility_timeout_seconds=visibility_timeout_seconds,
            x_internal_api_key=x_internal_api_key,
        )
    ).parsed
