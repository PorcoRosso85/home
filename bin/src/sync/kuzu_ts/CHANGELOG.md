# Changelog

All notable changes to this project will be documented in this file.

## [2025-07-24]

### Changed
- TypeScriptファイル名をcamelCaseに統一
  - `websocket-server.ts` → `websocketServer.ts`
  - `websocket-client.ts` → `websocketClient.ts`
  - `tests/integration_test.ts` → `tests/websocket_sync.test.ts`

### Impact
- 関連する設定ファイルのパスを更新