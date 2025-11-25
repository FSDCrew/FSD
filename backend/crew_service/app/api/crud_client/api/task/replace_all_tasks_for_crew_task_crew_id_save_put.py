from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.task_create import TaskCreate
from ...models.task_read import TaskRead
from ...types import Response


def _get_kwargs(
    crew_id: UUID,
    *,
    body: list[TaskCreate],
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/task/{crew_id}/save".format(
            crew_id=crew_id,
        ),
    }

    _kwargs["json"] = []
    for body_item_data in body:
        body_item = body_item_data.to_dict()
        _kwargs["json"].append(body_item)

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[TaskRead] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = TaskRead.from_dict(response_200_item_data)

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
) -> Response[HTTPValidationError | list[TaskRead]]:
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
    body: list[TaskCreate],
) -> Response[HTTPValidationError | list[TaskRead]]:
    """Replace All Tasks For Crew

     Replace all tasks for a crew.

    Args:
        crew_id (UUID): Crew ID to associate the task with
        body (list[TaskCreate]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[TaskRead]]
    """

    kwargs = _get_kwargs(
        crew_id=crew_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    crew_id: UUID,
    *,
    client: AuthenticatedClient,
    body: list[TaskCreate],
) -> HTTPValidationError | list[TaskRead] | None:
    """Replace All Tasks For Crew

     Replace all tasks for a crew.

    Args:
        crew_id (UUID): Crew ID to associate the task with
        body (list[TaskCreate]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[TaskRead]
    """

    return sync_detailed(
        crew_id=crew_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    crew_id: UUID,
    *,
    client: AuthenticatedClient,
    body: list[TaskCreate],
) -> Response[HTTPValidationError | list[TaskRead]]:
    """Replace All Tasks For Crew

     Replace all tasks for a crew.

    Args:
        crew_id (UUID): Crew ID to associate the task with
        body (list[TaskCreate]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[TaskRead]]
    """

    kwargs = _get_kwargs(
        crew_id=crew_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    crew_id: UUID,
    *,
    client: AuthenticatedClient,
    body: list[TaskCreate],
) -> HTTPValidationError | list[TaskRead] | None:
    """Replace All Tasks For Crew

     Replace all tasks for a crew.

    Args:
        crew_id (UUID): Crew ID to associate the task with
        body (list[TaskCreate]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[TaskRead]
    """

    return (
        await asyncio_detailed(
            crew_id=crew_id,
            client=client,
            body=body,
        )
    ).parsed
