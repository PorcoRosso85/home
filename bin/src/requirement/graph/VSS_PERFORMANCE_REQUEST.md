# VSS-Kuzu パフォーマンス改善依頼書

## 概要

requirement/graphプロジェクトにおいて、VSS（Vector Similarity Search）の初期化に11.3秒かかっており、ユーザー体験を著しく損なっています。CLIツールとして実用的な応答時間（3秒以内）を実現するため、vss-kuzuモジュールのパフォーマンス改善をお願いします。

## 現状の問題

### パフォーマンス測定結果
```
VSS初期化: 11.328秒
├─ モデルロード: 推定 8-9秒
├─ embedding生成: 推定 2-3秒
└─ インデックス構築: 推定 0.5秒

FTS初期化: 0.979秒
全体実行時間: 約30秒（Nix含む）
```

### 利用状況
- **呼び出し頻度**: 毎回のCLIコマンド実行時（1日数十回）
- **利用パターン**: 短いセッションで繰り返し実行
- **現在のモデル**: cl-nagoya/ruri-v3-30m（30Mパラメータ）

## 改善要望

### 1. 初期化オプションの追加

```python
# 現在の呼び出し
vss_service = create_vss(
    db_path=db_path,
    existing_connection=connection
)

# 要望: オプショナルパラメータの追加
vss_service = create_vss(
    db_path=db_path,
    existing_connection=connection,
    # 以下の高速化オプションをサポートしてほしい
    lazy_init=True,              # 遅延初期化モード
    cache_dir="./vss_cache",     # embeddings/モデルキャッシュ
    model_name="all-MiniLM-L6-v2",  # 軽量モデル指定
    skip_index_rebuild=True,     # 既存インデックスの再利用
    precomputed_embeddings=path  # 事前計算済みembeddings
)
```

### 2. キャッシュ機能

#### Embeddingsキャッシュ
```python
# ディスクベースのembeddingsキャッシュ
class EmbeddingsCache:
    def get_or_compute(self, text: str) -> np.ndarray:
        cache_key = hashlib.md5(text.encode()).hexdigest()
        cache_path = f"{self.cache_dir}/{cache_key}.npy"
        
        if os.path.exists(cache_path):
            return np.load(cache_path)  # 0.01秒
        
        embedding = self.model.encode(text)  # 0.5秒（初回のみ）
        np.save(cache_path, embedding)
        return embedding
```

#### モデルキャッシュ
```python
# モデルの永続化
model_cache_path = f"{cache_dir}/model.pkl"
if os.path.exists(model_cache_path):
    model = pickle.load(open(model_cache_path, 'rb'))  # 1-2秒
else:
    model = load_model(model_name)  # 8-9秒
    pickle.dump(model, open(model_cache_path, 'wb'))
```

### 3. 軽量モデルのサポート

| モデル | パラメータ数 | 精度 | ロード時間 |
|--------|-------------|------|-----------|
| cl-nagoya/ruri-v3-30m（現在） | 30M | 高 | 8-9秒 |
| all-MiniLM-L6-v2（提案） | 22M | 中 | 2-3秒 |
| all-MiniLM-L12-v2（提案） | 33M | 中高 | 3-4秒 |

### 4. 遅延初期化モード

```python
class LazyVSS:
    def __init__(self, config):
        self.config = config
        self._model = None  # 初期化しない
        self._index = None  # 初期化しない
    
    def search(self, query: str):
        # 検索時に初めて必要な部分だけ初期化
        if not self._model:
            self._model = self._load_lightweight_model()  # 2-3秒
        
        # キャッシュから既存embeddingsを読み込み
        embeddings = self._load_cached_embeddings()  # 0.1秒
        
        # 新規分のみ計算
        new_embeddings = self._compute_new_only(query)
        
        return self._search_with_cache(query, embeddings)
```

### 5. バッチ処理の最適化

```python
# 現在: 個別処理
for text in texts:
    embedding = model.encode(text)  # N × 0.5秒

# 改善案: バッチ処理
embeddings = model.encode(texts, batch_size=32)  # 一括で高速化
```

## 期待される効果

| 改善項目 | 現在 | 改善後 | 削減時間 |
|---------|------|--------|---------|
| モデルロード | 8-9秒 | 2-3秒（軽量版） | 6秒 |
| Embeddingsキャッシュ | なし | 0.01秒（2回目以降） | 2-3秒 |
| 遅延初期化 | 全て事前 | 必要時のみ | 3-4秒 |
| **合計** | **11.3秒** | **2-3秒** | **8-9秒削減** |

## 実装優先順位

1. **P0（必須）**: Embeddingsキャッシュ機能
   - 最も効果が高く、実装も比較的簡単
   - 2回目以降の実行が劇的に高速化

2. **P1（推奨）**: 軽量モデルオプション
   - モデル切り替えだけで大幅改善
   - 用途に応じた精度とパフォーマンスのトレードオフ

3. **P2（可能なら）**: 遅延初期化
   - アーキテクチャ変更が必要だが効果大

## テスト方法

```bash
# パフォーマンステスト
time python -c "
from vss_kuzu import create_vss
import time
start = time.time()
vss = create_vss(db_path='test.db', lazy_init=True, model_name='all-MiniLM-L6-v2')
print(f'初期化時間: {time.time() - start:.2f}秒')
"

# 期待値: 3秒以内
```

## 互換性維持

既存のAPIは維持し、オプショナルパラメータとして追加することで、後方互換性を保証してください：

```python
def create_vss(
    db_path: str,
    existing_connection=None,
    # 以下、新規オプション（デフォルトは現在の動作）
    lazy_init: bool = False,
    cache_dir: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs
):
    if model_name is None:
        model_name = "cl-nagoya/ruri-v3-30m"  # 現在のデフォルト
    ...
```

## まとめ

CLIツールとしての実用性を確保するため、VSS初期化時間を**11.3秒から3秒以内**に短縮することが必要です。特にEmbeddingsキャッシュと軽量モデルサポートは、比較的実装が簡単で効果も大きいため、優先的な対応をお願いします。

ご質問や技術的な相談があれば、お気軽にお問い合わせください。

---
作成日: 2025-01-10
作成者: requirement/graphチーム