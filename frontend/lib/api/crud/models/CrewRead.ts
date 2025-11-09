/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Agent } from './Agent';
import type { TaskRead } from './TaskRead';
export type CrewRead = {
    name: string;
    id: string;
    tasks: Array<TaskRead>;
    agents: Array<Agent>;
};

