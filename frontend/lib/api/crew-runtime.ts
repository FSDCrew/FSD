import type { CreateClientConfig } from './crew/client.gen';

export const createClientConfig: CreateClientConfig = (config = {}) => {
    // const token =
    //     typeof window !== 'undefined'
    //         ? localStorage.getItem('access_token')
    //         : undefined;

    return {
        ...config,
        baseUrl:
            process.env.NEXT_PUBLIC_CREW_API_BASE_URL ??
            'http://localhost:8001',

        // Ensures cookies (like Cognito session cookies) are sent cross-origin
        credentials: 'include',

        // Attach headers for token-based auth
        headers: {
            ...config.headers,
            // ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
    };
};

