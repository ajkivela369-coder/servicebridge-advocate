import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const target = process.argv[2];
if (!target) {
  throw new Error('Usage: node scripts/create_appdeploy_client_stub.mjs <project-directory>');
}

const dir = resolve(target, 'node_modules', '@appdeploy', 'client');
mkdirSync(dir, { recursive: true });
writeFileSync(
  resolve(dir, 'package.json'),
  JSON.stringify({ name: '@appdeploy/client', version: '0.0.0-ci-stub', type: 'module', exports: './index.js' }, null, 2),
);
writeFileSync(
  resolve(dir, 'index.js'),
  [
    'const noop = async () => ({});',
    'const chain = new Proxy(noop, { get: () => chain, apply: () => Promise.resolve({}) });',
    'export const api = chain;',
    'export const auth = chain;',
    'export const image = chain;',
  ].join('\n') + '\n',
);
console.log('Installed CI-only @appdeploy/client resolution stub in', dir);
