import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
    input: 'http://localhost:8001/openapi.json',
    output: './lib/api/crew',
    plugins: [
        {
            name: '@hey-api/client-fetch',
            runtimeConfigPath: '../crew-runtime',
        },
    ],
});

