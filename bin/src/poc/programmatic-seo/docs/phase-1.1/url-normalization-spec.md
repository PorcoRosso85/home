# URL正規化仕様書 - Phase 1.1

## 概要

Phase 1.1では、国際化対応のプログラマティックSEOシステムにおけるURL正規化の標準的な実装方法を定義します。この仕様は、sitemap.xmlとhreflang alternatesの両方での一貫したURL管理を保証します。

## 正規化ルール

### 1. URL形式の制約

#### 1.1 絶対URL限定
- **必須**: すべてのURLは絶対URL形式である必要があります
- **禁止**: 相対URLは一切受け付けません
- **例**:
  - ✅ `https://example.com/page`
  - ❌ `/page` (相対URL)
  - ❌ `page.html` (相対URL)

#### 1.2 プロトコル制限
- **推奨**: HTTPSプロトコルの使用
- **許可**: HTTPプロトコル（開発環境等）
- **禁止**: その他のプロトコル（ftp, file等）

```typescript
// デフォルト設定
allowedProtocols: ['https', 'http']

// 厳密設定（本番環境推奨）
allowedProtocols: ['https']
```

### 2. 末尾スラッシュの統一

#### 2.1 統一ルール
- **デフォルト**: `never` - 末尾スラッシュを除去
- **オプション**: `always` - 末尾スラッシュを追加
- **オプション**: `preserve` - 元の形式を保持

#### 2.2 適用例

```typescript
// never (デフォルト)
'https://example.com/page/' → 'https://example.com/page'
'https://example.com/' → 'https://example.com/' (ルートは除外)

// always
'https://example.com/page' → 'https://example.com/page/'
'https://example.com/' → 'https://example.com/' (変更なし)

// preserve
'https://example.com/page' → 'https://example.com/page' (変更なし)
'https://example.com/page/' → 'https://example.com/page/' (変更なし)
```

### 3. クエリパラメータとフラグメントの除去

#### 3.1 除去対象
- **クエリパラメータ**: `?key=value&foo=bar` 部分を除去
- **フラグメント**: `#section` 部分を除去
- **理由**: canonical URLの統一とSEO最適化

#### 3.2 適用例

```typescript
// 正規化前
'https://example.com/page?utm_source=google&utm_medium=cpc#section1'

// 正規化後
'https://example.com/page'
```

### 4. ポート番号の正規化

#### 4.1 標準ポートの除去
- **HTTPS**: ポート443は除去
- **HTTP**: ポート80は除去
- **カスタムポート**: 保持

#### 4.2 適用例

```typescript
// 正規化前
'https://example.com:443/page'
'http://example.com:80/page'
'https://example.com:8080/page'

// 正規化後
'https://example.com/page'
'http://example.com/page'
'https://example.com:8080/page' (カスタムポートは保持)
```

## 設定オプション

### URLNormalizationConfig

```typescript
interface URLNormalizationConfig {
  /** 末尾スラッシュの統一ルール */
  trailingSlash: 'always' | 'never' | 'preserve';

  /** クエリパラメータの除去 */
  removeQuery: boolean;

  /** フラグメントの除去 */
  removeFragment: boolean;

  /** 許可されるプロトコル */
  allowedProtocols: ('https' | 'http')[];

  /** ポート番号の正規化 */
  normalizePort: boolean;
}
```

### プリセット設定

#### デフォルト設定
```typescript
export const DEFAULT_URL_NORMALIZATION: URLNormalizationConfig = {
  trailingSlash: 'never',
  removeQuery: true,
  removeFragment: true,
  allowedProtocols: ['https', 'http'],
  normalizePort: true
};
```

#### 厳密設定（本番環境推奨）
```typescript
export const STRICT_URL_NORMALIZATION: URLNormalizationConfig = {
  trailingSlash: 'never',
  removeQuery: true,
  removeFragment: true,
  allowedProtocols: ['https'], // HTTPSのみ
  normalizePort: true
};
```

## バリデーション

### エラーコード

| コード | 説明 | 対処法 |
|--------|------|--------|
| `INVALID_URL` | URL形式が不正 | 正しいURL形式で入力 |
| `RELATIVE_URL` | 相対URLが指定された | 絶対URLに変更 |
| `UNSUPPORTED_PROTOCOL` | サポートされていないプロトコル | httpsまたはhttpを使用 |
| `INVALID_HOST` | ホスト名が不正 | 有効なドメイン名を指定 |
| `TRAILING_SLASH_VIOLATION` | 末尾スラッシュルール違反 | 設定に従って修正 |

### バリデーション関数

```typescript
import { validateURL, normalizeURL } from './packages/i18n/validation.js';

// バリデーション
const result = validateURL('https://example.com/page?param=value');
if (result.valid) {
  console.log('正規化済みURL:', result.data);
} else {
  console.error('エラー:', result.errors);
}

// 直接正規化（エラー時は例外発生）
try {
  const normalized = normalizeURL('https://example.com/page?param=value');
  console.log('正規化済み:', normalized);
} catch (error) {
  console.error('正規化エラー:', error.message);
}
```

## 実装例

### 基本的な使用方法

```typescript
import {
  normalizeURL,
  validateURL,
  DEFAULT_URL_NORMALIZATION
} from './packages/i18n/validation.js';

// 1. 単一URL正規化
const url = 'https://example.com/page/?utm_source=google#section';
const normalized = normalizeURL(url);
console.log(normalized); // 'https://example.com/page'

// 2. バリデーション付き正規化
const result = validateURL(url);
if (result.valid) {
  console.log('成功:', result.data);
} else {
  console.error('失敗:', result.errors);
}

// 3. カスタム設定での正規化
const customConfig = {
  ...DEFAULT_URL_NORMALIZATION,
  trailingSlash: 'always'
};
const customNormalized = normalizeURL(url, customConfig);
console.log(customNormalized); // 'https://example.com/page/'
```

### 一括処理

```typescript
import { validateURLSourceDatabase } from './packages/i18n/validation.js';

// URL-source.jsonのバリデーション
const urlSourceData = await fetch('./scripts/url-source.json').then(r => r.json());
const validation = validateURLSourceDatabase(urlSourceData);

if (validation.valid) {
  console.log('データベース検証成功:', validation.data);
} else {
  console.error('検証エラー:', validation.errors);
}
```

## 国際化対応

### hreflang alternates

URL正規化は各言語のURLでも一貫して適用されます：

```json
{
  "loc": "https://example.com/en/page",
  "lastmod": "2024-03-15T10:00:00.000Z",
  "lang": "en",
  "alternates": [
    {
      "lang": "ja",
      "loc": "https://example.com/ja/page"
    },
    {
      "lang": "x-default",
      "loc": "https://example.com/page"
    }
  ]
}
```

### x-default対応

- `x-default`は言語固有でないバージョンを示します
- 通常はルートパス（`/`）または言語プレフィックスなしのパスを使用
- すべてのalternatesで一貫した正規化を適用

## 注意事項

### 1. SEO観点
- 正規化により、重複コンテンツの問題を回避
- canonical URLの一貫性を保証
- sitemap.xmlでの統一性確保

### 2. 開発観点
- 型安全性により、コンパイル時にURL形式をチェック
- バリデーション関数により、実行時エラーを防止
- 設定可能な正規化ルールで柔軟性を確保

### 3. 運用観点
- ログ出力時は正規化前のURLも記録推奨
- エラー発生時の詳細情報提供
- パフォーマンス：正規化処理のキャッシュ検討

## 更新履歴

- **v1.1** (2024-03-15): 初版リリース
  - 基本的なURL正規化ルール定義
  - TypeScript型安全性対応
  - BCP47言語タグ統合
  - JSON Schema validation対応
