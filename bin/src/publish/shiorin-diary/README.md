shiorin-diary (staging)

Minimal Cloudflare Worker using KV and R2. Deployed to `*.workers.dev` with `-stg` postfix.

Setup
- Create KV namespace and R2 bucket (staging):
  - KV: `wrangler kv namespace create shiorin-diary-stg-cache` → put the returned `id` into `wrangler.toml` under `env.staging.kv_namespaces[0].id`.
  - R2: Create `stg-shiorin-diary-files` from dashboard or CLI, or adjust the bucket name in `wrangler.toml`.

Run
- Dev: `npm run dev` (binds staging env)
- Deploy (staging): `npm run deploy:staging`

Endpoints
- `GET /` → health/info JSON
- KV:
  - `PUT /kv/<key>` with raw text body → store
  - `GET /kv/<key>` → fetch
  - `DELETE /kv/<key>` → delete
- R2:
  - `PUT /r2/<key>` with body → upload (content-type honored)
  - `GET /r2/<key>` → download
  - `DELETE /r2/<key>` → delete

Notes
- This project is intentionally lightweight: no devcontainer, tests, DB, or Redwood extras.

