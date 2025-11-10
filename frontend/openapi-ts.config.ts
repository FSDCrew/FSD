import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
    input: 'http://localhost:8000/openapi.json',
    output: './lib/api/crud',
    plugins: [
        {
            name: '@hey-api/client-fetch',
            runtimeConfigPath: '../crud-runtime',
        },
    ],
});