# コード規約

このドキュメントはプロジェクト全体で守るべきコード規約を定義しています。

## ロギングシステムの設計規約

### 型定義と型安全性

1. **インターフェース禁止、type のみを使用**
   - TypeScriptの `interface` キーワードは使用せず、`type` のみを使用する
   - 型の合成や拡張は、型の交差 (`&`) や合併 (`|`) で行う

2. **ハードコード値の禁止**
   - 文字列リテラルや数値などの直接指定は避け、型やconstによる定義を行う
   - 例: `format: 'json'` ではなく `format: ConsoleFormat` を使用
   ```typescript
   // 良い例
   type ConsoleFormat = 'simple' | 'json' | 'detailed';
   const logger = createLogger([consolePlugin({ format: 'json' })]);
   
   // 悪い例
   const logger = createLogger([consolePlugin({ format: 'custom-format' })]);
   ```

3. **enumも許容**
   - 列挙型として明確に定義される値は `enum` も使用可能
   - 例: `LogLevel.DEBUG` のように使用

### アーキテクチャと設計パターン

1. **プラグインベースの設計**
   - 機能は独立したプラグインとして実装
   - 拡張性を考慮し、カスタムプラグインの追加が容易な設計にする
   ```typescript
   // プラグイン型定義
   type LoggerPlugin = {
     name: string;
     process: (level: LogLevel, message: string, data?: any) => void;
   };
   
   // 複数のプラグインを組み合わせる
   const logger = createLogger([
     consolePlugin({ format: 'json' }),
     duckdbPlugin({ table: 'app_logs' })
   ]);
   ```

2. **拡張可能なオプション**
   - 柔軟な設定を可能にするオプションオブジェクトの設計
   - デフォルト値は明示的に定義し、Partial型で上書き可能にする
   ```typescript
   type LoggerOptions = {
     level: LogLevel;
     format: string;
     // その他のオプション
   };
   
   const DEFAULT_OPTIONS: LoggerOptions = {
     level: LogLevel.ERROR,
     format: 'simple'
   };
   
   function createLogger(options?: Partial<LoggerOptions>) {
     const opts = { ...DEFAULT_OPTIONS, ...options };
     // 以下、optsを使用
   }
   ```

3. **クラス禁止**
   - クラスベースのオブジェクト指向プログラミングは使用しない
   - 代わりに関数型プログラミングと型定義を重視する
   - ファクトリ関数やプレーンなオブジェクトを使用

4. **モック・フォールバック禁止**
   - テスト用のモッキングコードは本番コードに含めない
   - 機能が使用できない場合のフォールバック実装を含めない
   - 明示的なエラーハンドリングを行う

5. **try/catch 禁止**
   - 例外処理には try/catch を使用しない
   - エラーは型定義に基づいた返り値として扱う
   ```typescript
   // 良い例
   type Result<T> = 
     | { ok: true; value: T }
     | { ok: false; error: SqlError };
     
   function executeQuery(): Result<Row[]> {
     // 処理
     if (errorCondition) {
       return { ok: false, error: { code: 'ERROR_CODE', message: 'エラーメッセージ' } };
     }
     return { ok: true, value: rows };
   }
   
   // 使用側
   const result = executeQuery();
   if (result.ok) {
     // 成功時の処理
     const rows = result.value;
   } else {
     // エラー時の処理
     const error = result.error;
   }
   ```

### ファイル構造とモジュール設計

1. **明確なディレクトリ構造**
   - `/domain` - ドメインモデルと型定義
   - `/infrastructure` - 技術的実装
   - `/plugins` - プラグイン実装
   
2. **一貫した命名規則**
   - キャメルケース（camelCase）を使用
   - 型名にはパスカルケース（PascalCase）を使用
   - ファイル名はキャメルケース

3. **使用されていないファイル/ディレクトリの削除**
   - 未使用のコードは削除
   - 空のディレクトリも削除

4. **モジュールエクスポートの統一**
   - mod.ts からの一元的なエクスポート
   - 使用者が簡単に利用できるように直接関数もエクスポート
   ```typescript
   // mod.ts
   export { createLogger, consolePlugin, duckdbPlugin };
   export type { Logger, LoggerOptions, LoggerPlugin };
   ```

### コメントとドキュメント

1. **コードコメントの活用**
   - mod.ts に使用例を記載
   - README不要で、コード自体がドキュメントの役割を果たす
   ```typescript
   /**
    * 使用例:
    * ```typescript
    * import { debug, info } from "./log/mod.ts";
    * debug("デバッグメッセージ");
    * ```
    */
   ```

2. **型定義の明確化**
   - 型定義にはコメントを付けて目的を説明
   - オプションの意味を明確に記述
