import { Link } from 'waku';
import { Suspense } from 'react';
import { Counter } from '../components/counter';
import { SimpleForm } from '../components/simple-form';
import { DonutChart } from '../components/donut-chart';
import { DuckDBLoader } from '../components/duckdb-loader';
import { SQLiteLoader } from '../components/sqlite-loader';
import { getHonoContext } from '../../waku.hono-enhancer';
import { isBuild } from '../lib/waku';
import { variables } from '../lib/variables';

export default async function HomePage() {
  const data = await getData();

  // Example: getting the Hono context object and invoking
  // waitUntil() on the Cloudflare executionCtx.
  // https://hono.dev/docs/api/context#executionctx
  const c = getHonoContext();
  c?.executionCtx?.waitUntil(
    new Promise<void>((resolve) => {
      setTimeout(() => {
        console.log(
          'Cloudflare waitUntil() promise resolved. The server response does not wait for this.',
        );
        resolve();
      }, 1000);
    }),
  );

  const maxItems = variables.maxItems();
  const enableWasmFromR2 = variables.enableWasmFromR2();
  const r2PublicUrl = variables.r2PublicUrl();
  const r2WasmUrl = variables.r2WasmUrl();

  return (
    <div style={{
      fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    }}>
      <title>{data.title}</title>
      <h1 style={{
        fontSize: '2.25rem',
        fontWeight: 'bold',
        letterSpacing: '-0.025em',
        fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
      }}>{data.headline}</h1>
      <p>{data.body}</p>
      <p>MAX_ITEMS = {maxItems}.</p>
      <Suspense fallback="Pending...">
        <ServerMessage />
      </Suspense>
      <Counter max={maxItems} />
      <SimpleForm />
      <DonutChart />
      <DuckDBLoader enableR2={enableWasmFromR2} r2Url={r2PublicUrl} />
      <SQLiteLoader wasmUrl="/wasm/sqlite3.wasm" />
      {/* R2 URL (CORS設定後に使用): {r2WasmUrl}/sqlite/sqlite3.wasm */}
      <Link to="/about" style={{
        marginTop: '16px',
        display: 'inline-block',
        textDecoration: 'underline'
      }}>
        About page
      </Link>
    </div>
  );
}

// Example async server component
const ServerMessage = async () => {
  if (isBuild()) {
    console.warn('Note: server components are awaited during build.');
    return null;
  }
  await new Promise((resolve) => setTimeout(resolve, 2000));
  return <p>Hello from server!</p>;
};

// Example async data fetching
const getData = async () => {
  const data = {
    title: 'Waku',
    headline: 'Waku',
    body: 'Hello world!',
  };

  return data;
};

// Enable dynamic server rendering.
// Static rendering is possible if you want to render at build time.
// The Hono context will not be available.
export const getConfig = async () => {
  return {
    render: 'dynamic',
  } as const;
};
