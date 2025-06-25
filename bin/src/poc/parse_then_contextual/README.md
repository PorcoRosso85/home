# Parse Then Contextual - 段階的要件処理POC

低コストから高コストへ段階的にエスカレーションする要件処理システムのPOC。

## 概要

新しい要件を処理する際、以下の順序でチェックを実行：

1. **ルールベース**（コスト: ほぼ0）
2. **軽量埋め込み**（コスト: 低）
3. **CCG検索のみ**（コスト: 中）
4. **小規模LLM判定**（コスト: 高）
5. **大規模LLM分析**（コスト: 最高）

## アーキテクチャ

```
新要件
  ↓
[Stage1: RuleChecker] → 即座に却下可能な違反を検出
  ↓
[Stage2: EmbeddingChecker] → 軽量埋め込みで重複検出
  ↓
[Stage3: SemanticChecker] → CCGで意味的類似を検索
  ↓
[Stage4: LLMChecker] → 必要時のみLLMで判定
  ↓
承認/却下
```

## 使用方法

```bash
# インストール
cd /home/nixos/bin/src/poc/parse_then_contextual
pip install -r requirements.txt

# 実行
python demo.py "新しい認証機能を追加する"
```

## コスト記録

各処理でかかったコストを記録し、最適化の効果を測定できます。

```
Stage 1: 0.000円 (ルールチェック)
Stage 2: 0.001円 (埋め込み)
Stage 3: 0.005円 (CCG検索)
合計: 0.006円
```