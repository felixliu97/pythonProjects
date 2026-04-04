import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: 'http://localhost:8000/openapi.json',
  output: './src/api-client',
  plugins: [
    {
      name: '@hey-api/client-fetch',
    },
    '@hey-api/typescript',
    '@hey-api/sdk',
  ],
});
