import type { CreateClientConfig } from './crud/client.gen';

export const createClientConfig: CreateClientConfig = (config = {}) => {
    const token = typeof window !== 'undefined' 
        ? getCognitoIdToken() 
        : undefined;

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
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
    };
};

function getCognitoIdToken(): string | null {
    const cookies = document.cookie.split('; ');
    for (const cookie of cookies) {
        const [name, value] = cookie.split('=');
        if (name.includes('CognitoIdentityServiceProvider') && name.endsWith('.idToken')) {
            return value;
        }
    }
    return null;
}
