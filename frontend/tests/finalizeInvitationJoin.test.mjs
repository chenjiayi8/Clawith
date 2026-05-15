import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { build } from 'esbuild';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const outdir = path.resolve(__dirname, '../.tmp-tests');
const outfile = path.join(outdir, 'finalizeInvitationJoin.mjs');

await mkdir(outdir, { recursive: true });
await build({
  entryPoints: [path.resolve(__dirname, '../src/utils/invitationJoinAuth.ts')],
  bundle: true,
  platform: 'node',
  format: 'esm',
  outfile,
  logLevel: 'silent',
});

const { syncAuthAfterInvitationJoin } = await import(pathToFileURL(outfile).href);

test('refreshes auth with the existing token when joining an invited company returns no new access token', async () => {
  const calls = [];
  const expectedUser = { id: 'user-1', tenant_id: 'tenant-1' };

  const joined = await syncAuthAfterInvitationJoin({
    invitationCode: 'INVITE123',
    currentToken: 'existing-token',
    joinCompany: async (code) => {
      calls.push(['join', code]);
      return { role: 'member', tenant: { id: 'tenant-1' } };
    },
    loadCurrentUser: async () => {
      calls.push(['me']);
      return expectedUser;
    },
    persistToken: (token) => {
      calls.push(['persist', token]);
    },
    applyAuth: (user, token) => {
      calls.push(['setAuth', user, token]);
    },
  });

  assert.equal(joined, true);
  assert.deepEqual(calls, [
    ['join', 'INVITE123'],
    ['me'],
    ['setAuth', expectedUser, 'existing-token'],
  ]);
});

test('persists and uses the tenant-scoped token when join returns a new access token', async () => {
  const calls = [];
  const expectedUser = { id: 'user-1', tenant_id: 'tenant-2' };

  const joined = await syncAuthAfterInvitationJoin({
    invitationCode: 'INVITE456',
    currentToken: 'old-token',
    joinCompany: async () => {
      calls.push(['join']);
      return { access_token: 'new-token', role: 'member', tenant: { id: 'tenant-2' } };
    },
    loadCurrentUser: async () => {
      calls.push(['me']);
      return expectedUser;
    },
    persistToken: (token) => {
      calls.push(['persist', token]);
    },
    applyAuth: (user, token) => {
      calls.push(['setAuth', user, token]);
    },
  });

  assert.equal(joined, true);
  assert.deepEqual(calls, [
    ['join'],
    ['persist', 'new-token'],
    ['me'],
    ['setAuth', expectedUser, 'new-token'],
  ]);
});
