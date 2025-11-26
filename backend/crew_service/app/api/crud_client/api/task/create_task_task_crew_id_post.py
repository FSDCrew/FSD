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
    body: TaskCreate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/task/{crew_id}".format(
            crew_id=crew_id,
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TaskRead | None:
    if response.status_code == 201:
        response_201 = TaskRead.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | TaskRead]:
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
    body: TaskCreate,
) -> Response[HTTPValidationError | TaskRead]:
    """Create Task

     Create a new task.

    Args:
        crew_id (UUID): Crew ID to associate the task with
        body (TaskCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TaskRead]
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
    body: TaskCreate,
) -> HTTPValidationError | TaskRead | None:
    """Create Task

     Create a new task.

    Args:
        crew_id (UUID): Crew ID to associate the task with
        body (TaskCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TaskRead
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
    body: TaskCreate,
) -> Response[HTTPValidationError | TaskRead]:
    """Create Task

     Create a new task.

    Args:
        crew_id (UUID): Crew ID to associate the task with
        body (TaskCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TaskRead]
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
    body: TaskCreate,
) -> HTTPValidationError | TaskRead | None:
    """Create Task

     Create a new task.

    Args:
        crew_id (UUID): Crew ID to associate the task with
        body (TaskCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TaskRead
    """

    return (
        await asyncio_detailed(
            crew_id=crew_id,
            client=client,
            body=body,
        )
    ).parsed
