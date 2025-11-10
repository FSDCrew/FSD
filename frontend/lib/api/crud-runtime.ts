import type { CreateClientConfig } from './crud/client.gen';

export const createClientConfig: CreateClientConfig = (config = {}) => {
    // const token =
    //     typeof window !== 'undefined'
    //         ? localStorage.getItem('access_token')
    //         : undefined;

    return {
        ...config,
        baseUrl:
            process.env.NEXT_PUBLIC_CRUD_API_BASE_URL ??
            'http://localhost:8000',

        // Ensures cookies (like Cognito session cookies) are sent cross-origin
        credentials: 'include',

        // Attach headers for token-based auth
        headers: {
            ...config.headers,
            // ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
    };
};
