/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { User } from '../models/User';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class UserService {
    /**
     * Sync User
     * Sync/create user in database from JWT token.
     * @returns User Successful Response
     * @throws ApiError
     */
    public static syncUserUserSyncPost(): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/user/sync',
        });
    }
    /**
     * Get User By Id
     * Get user by ID. Users can only access their own profile.
     * @returns User Successful Response
     * @throws ApiError
     */
    public static getUserByIdUserGet(): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/user/',
        });
    }
}
