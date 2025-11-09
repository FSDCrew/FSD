/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CrewCreate } from '../models/CrewCreate';
import type { CrewRead } from '../models/CrewRead';
import type { CrewUpdate } from '../models/CrewUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CrewService {
    /**
     * Get Crews
     * Get crews, optionally filtered by crew_id.
     * @param crewId Optional Crew ID to filter
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCrewsCrewGet(
        crewId?: (string | null),
    ): CancelablePromise<(CrewRead | Array<CrewRead>)> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/crew/',
            query: {
                'crew_id': crewId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Crew
     * Create a new crew.
     * @param requestBody
     * @returns CrewRead Successful Response
     * @throws ApiError
     */
    public static createCrewCrewPost(
        requestBody: CrewCreate,
    ): CancelablePromise<CrewRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/crew/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Crew
     * Update an existing crew.
     * @param requestBody
     * @returns CrewRead Successful Response
     * @throws ApiError
     */
    public static updateCrewCrewPut(
        requestBody: CrewUpdate,
    ): CancelablePromise<CrewRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/crew/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
