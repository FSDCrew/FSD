/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TaskCreate } from '../models/TaskCreate';
import type { TaskRead } from '../models/TaskRead';
import type { TaskUpdate } from '../models/TaskUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TaskService {
    /**
     * Create Task
     * Create a new task.
     * @param crewId Crew ID to associate the task with
     * @param requestBody
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static createTaskTaskCrewIdPost(
        crewId: string,
        requestBody: TaskCreate,
    ): CancelablePromise<TaskRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/task/{crew_id}',
            path: {
                'crew_id': crewId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update One Task
     * Update one task.
     * @param crewId Crew ID to associate the task with
     * @param requestBody
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static updateOneTaskTaskCrewIdPatch(
        crewId: string,
        requestBody: TaskUpdate,
    ): CancelablePromise<Array<TaskRead>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/task/{crew_id}',
            path: {
                'crew_id': crewId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Replace All Tasks For Crew
     * Replace all tasks for a crew.
     * @param crewId Crew ID to associate the task with
     * @param requestBody
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static replaceAllTasksForCrewTaskCrewIdSavePut(
        crewId: string,
        requestBody: Array<TaskCreate>,
    ): CancelablePromise<Array<TaskRead>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/task/{crew_id}/save',
            path: {
                'crew_id': crewId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
