# SF6 Combo Lab - 実装提案書

## プロジェクト概要
- **名称**: SF6 Combo Lab
- **ディレクトリ**: `publish/sf6-combo-lab`
- **目的**: ストリートファイター6のコンボ情報を構造化し、実用性を証明できるプラットフォーム

## MVP段階的実装

### Phase 1: 基盤構築（1-2日）
```bash
# waku-initベースで初期化
cp -r waku-init sf6-combo-lab
cd sf6-combo-lab

# 不要なコンポーネント削除
rm -rf src/components/counter
rm -rf src/components/test-connection

# package.json更新
# name: "sf6-combo-lab"
```

### Phase 2: 認証機能（1日）
- Google OAuth実装
- X (Twitter) OAuth実装
- Cloudflare KVでユーザー情報管理

### Phase 3: コア機能実装（2-3日）

#### 投稿フォーム（構造化必須）
```typescript
interface ComboData {
  character: string;       // キャラクター
  startMove: string;      // 始動技
  recipe: string;         // コンボレシピ（テンキー表記）
  damage: number;         // ダメージ
  driveGauge: number;     // 使用ゲージ本数
  situation: string[];    // タグ: ["画面中央", "画面端"]
  version: string;        // ゲームバージョン
}
```

#### データベース設計（Cloudflare D1）
```sql
CREATE TABLE combos (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  character TEXT NOT NULL,
  start_move TEXT NOT NULL,
  recipe TEXT NOT NULL,
  damage INTEGER NOT NULL,
  drive_gauge INTEGER NOT NULL,
  situation TEXT, -- JSON array
  version TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reproductions (
  combo_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  success_type TEXT, -- "training" or "ranked"
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (combo_id) REFERENCES combos(id)
);
```

### Phase 4: 差別化機能（2日）

#### 再現報告システム
- 「トレモで成功」ボタン
- 「ランクマで決まった」ボタン
- 再現数の可視化

#### 自動算出指標
```typescript
// ゲージ効率計算
const efficiency = damage / (driveGauge || 0.5);

// 実用性スコア
const practicalScore = reproductionCount * 0.7 + uniqueUserCount * 0.3;
```

#### 称号システム
- 「最高効率コンボ開発者」
- 「〇〇キャラマスター」
- バッジ表示機能

### Phase 5: Turborepo統合 & デプロイ（1日）
```bash
# Turborepo統合
# publish/turbo.json に追加
# publish/package.json のworkspacesに追加

# ビルド
turbo build --filter=sf6-combo-lab

# Siliplaneデプロイ
npm run deploy
```

## 技術スタック
- **Frontend**: Waku + React
- **認証**: OAuth (Google/X) + Cloudflare Workers
- **Database**: Cloudflare D1
- **Cache**: Cloudflare KV
- **Hosting**: Cloudflare Pages

## 独自の価値提供

### 1. 構造化データの強制
- フリーテキスト禁止
- テンキー表記統一
- バージョン管理

### 2. 実用性の可視化
- 再現報告数
- ゲージ効率の自動計算
- 状況別フィルタリング

### 3. コミュニティドリブン
- 投稿者への称号付与
- 実績システム
- トッププレイヤーの巻き込み

## 収益化戦略（将来）

### フリーミアムモデル
- **無料**: 基本的な検索・閲覧
- **有料**: 
  - 高度なフィルタリング
  - API アクセス
  - 広告非表示

### コーチングマッチング
- 上級者と初心者のマッチング
- 手数料モデル

## 開発優先順位

1. **Week 1**: MVP完成（ログイン + 投稿 + 一覧）
2. **Week 2**: 再現報告 + 効率計算
3. **Week 3**: 称号システム + UI改善
4. **Week 4**: パフォーマンス最適化 + デプロイ

## KPI設定
- 初月: 100人のアクティブユーザー
- 3ヶ月: 1000件のコンボ登録
- 6ヶ月: 5000件の再現報告

## リスクと対策
- **リスク**: 既存サービスとの競合
- **対策**: 「再現報告」という独自機能で差別化

## 次のアクション
```bash
# プロジェクト開始コマンド
/phase "publish/sf6-combo-labを作成
1. waku-initをコピーしてsf6-combo-labとして初期化
2. OAuth認証実装（Google/X）
3. 構造化投稿フォーム実装
4. Cloudflare D1でデータベース構築
5. 再現報告システム実装
6. Turborepo統合とSiliplaneデプロイ"
```