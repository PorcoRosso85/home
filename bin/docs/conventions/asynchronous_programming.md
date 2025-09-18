# 非同期処理

## 基本方針

非同期処理は、アプリケーションの応答性を保つために不可欠ですが、複雑さの源泉でもあります。
`async/await` 構文を基本とし、コールバック地獄や `Promise` の直接操作を避けることで、同期的で読みやすいコードスタイルを維持します。

## ガイドライン

- **`async/await` を徹底する**: 非同期関数は必ず `async` で定義し、呼び出し側は `await` で結果を待ち受けます。`.then()` や `.catch()` のチェーンは原則として使用しません。

- **エラーハンドリング**: 非同期処理のエラーハンドリングも、[エラー処理の規約](./error_handling.md)に従います。`try/catch` ブロックを使って `await` した処理のエラーを捕捉し、値として返します。
  ```typescript
  async function fetchData(url: string): Promise<Result<Data, Error>> {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        return { ok: false, error: new Error(`HTTP error! status: ${response.status}`) };
      }
      const data = await response.json();
      return { ok: true, value: data };
    } catch (error) { // ネットワークエラーなど
      return { ok: false, error: error as Error };
    }
  }
  ```

- **並行処理**: 複数の非同期処理を並行して実行する場合は、`Promise.all()` (または各言語の同等機能) を使用して、すべての処理が完了するのを待ちます。ただし、1つの処理の失敗が全体に影響を与える点に注意してください。

- **トップレベル`await`**: スクリプトの初期化など、限定的な場面でのみ使用を許可します。基本的には `async` 関数内で `await` を使用してください。
