from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.artifact_read import ArtifactRead
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    original_crew_run_id: UUID,
    new_crew_run_id: UUID,
    *,
    x_internal_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_internal_api_key, Unset):
        headers["X-Internal-Api-Key"] = x_internal_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/internal/crew-run/{original_crew_run_id}/copy-artifacts/{new_crew_run_id}".format(
            original_crew_run_id=original_crew_run_id,
            new_crew_run_id=new_crew_run_id,
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[ArtifactRead] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ArtifactRead.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[ArtifactRead]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    original_crew_run_id: UUID,
    new_crew_run_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | list[ArtifactRead]]:
    """Copy Artifacts Internal

     Copy all artifacts from the original crew run to the new crew run (internal use only).

    Args:
        original_crew_run_id (UUID): Original Crew Run ID to copy artifacts from
        new_crew_run_id (UUID): New Crew Run ID to copy artifacts to
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[ArtifactRead]]
    """

    kwargs = _get_kwargs(
        original_crew_run_id=original_crew_run_id,
        new_crew_run_id=new_crew_run_id,
        x_internal_api_key=x_internal_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    original_crew_run_id: UUID,
    new_crew_run_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | list[ArtifactRead] | None:
    """Copy Artifacts Internal

     Copy all artifacts from the original crew run to the new crew run (internal use only).

    Args:
        original_crew_run_id (UUID): Original Crew Run ID to copy artifacts from
        new_crew_run_id (UUID): New Crew Run ID to copy artifacts to
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[ArtifactRead]
    """

    return sync_detailed(
        original_crew_run_id=original_crew_run_id,
        new_crew_run_id=new_crew_run_id,
        client=client,
        x_internal_api_key=x_internal_api_key,
    ).parsed


async def asyncio_detailed(
    original_crew_run_id: UUID,
    new_crew_run_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | list[ArtifactRead]]:
    """Copy Artifacts Internal

     Copy all artifacts from the original crew run to the new crew run (internal use only).

    Args:
        original_crew_run_id (UUID): Original Crew Run ID to copy artifacts from
        new_crew_run_id (UUID): New Crew Run ID to copy artifacts to
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[ArtifactRead]]
    """

    kwargs = _get_kwargs(
        original_crew_run_id=original_crew_run_id,
        new_crew_run_id=new_crew_run_id,
        x_internal_api_key=x_internal_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    original_crew_run_id: UUID,
    new_crew_run_id: UUID,
    *,
    client: AuthenticatedClient,
    x_internal_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | list[ArtifactRead] | None:
    """Copy Artifacts Internal

     Copy all artifacts from the original crew run to the new crew run (internal use only).

    Args:
        original_crew_run_id (UUID): Original Crew Run ID to copy artifacts from
        new_crew_run_id (UUID): New Crew Run ID to copy artifacts to
        x_internal_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[ArtifactRead]
    """

    return (
        await asyncio_detailed(
            original_crew_run_id=original_crew_run_id,
            new_crew_run_id=new_crew_run_id,
            client=client,
            x_internal_api_key=x_internal_api_key,
        )
    ).parsed
