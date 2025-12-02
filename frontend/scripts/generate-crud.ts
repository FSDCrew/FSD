import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const result = spawnSync(
  'npx',
  ['openapi-ts', '-f', resolve(__dirname, '../config/openapi-ts.config.crud.ts')],
  { stdio: 'inherit', cwd: resolve(__dirname, '..') }
);

process.exit(result.status ?? 0);

