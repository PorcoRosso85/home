import { DuckDBCell } from "../../components/DuckDBCell";

export function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Minimal Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-6 py-3">
          <h1 className="text-2xl font-bold text-gray-900">DuckDB WASM POC</h1>
          <p className="text-sm text-gray-600">Local asset loading demonstration</p>
        </div>
      </div>

      {/* Main Content - DuckDB Interface */}
      <div className="py-4">
        <DuckDBCell />
      </div>
    </div>
  );
}
