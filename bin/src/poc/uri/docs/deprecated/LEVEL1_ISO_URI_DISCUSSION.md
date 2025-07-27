# Level 1: 各ISOから標準的なURIが取得できるかの議論

## 結論：技術的には可能、設計上の選択が重要

### 1. ISO規格のURI変換可能性

各ISO規格は**構造化された識別子体系**を持っているため、LocationURI形式への変換は技術的に可能です。

#### 変換の具体例

**ISO 20022（金融）**:
- ISO識別子: `pacs.008.001.08`
- ビジネス名: FIToFICustomerCreditTransfer
- URI候補:
  - ドメイン指向: `req://finance/features/payment-initiation`
  - ISO直接参照: `req://iso/20022/pacs/008`
  - ハイブリッド: `req://finance/iso20022/payment-initiation`

**ISO 13606（医療）**:
- ISO構造: `EHR_EXTRACT > FOLDER > COMPOSITION`
- URI候補:
  - `req://healthcare/features/ehr-extract`
  - `req://iso/13606/ehr-extract/folder/composition`

### 2. URI設計の3つのアプローチ

#### アプローチ1: ビジネスドメイン中心（推奨）
```
req://[domain]/features/[business-function]
例: req://finance/features/payment-initiation
```

**利点**:
- ビジネス観点で直感的
- ISO規格が変わっても安定
- 複数のISO規格を統合可能

**欠点**:
- ISO規格へのトレーサビリティが間接的
- マッピングテーブルが必要

#### アプローチ2: ISO規格直接参照
```
req://iso/[standard-number]/[identifier]
例: req://iso/20022/pacs/008
```

**利点**:
- ISO規格への完全なトレーサビリティ
- 自動生成が容易
- 標準準拠が明確

**欠点**:
- ビジネス的に理解しづらい
- ISO規格のバージョン管理が複雑

#### アプローチ3: ハイブリッド型
```
req://[domain]/iso[standard]/[function]
例: req://finance/iso20022/payment-initiation
```

**利点**:
- ビジネス理解とトレーサビリティの両立
- 段階的な移行が可能

**欠点**:
- URI構造が複雑化
- 命名規則の一貫性維持が困難

### 3. 実装上の考慮事項

#### a) ISO規格の階層性の活用

```python
# ISO 20022の4階層構造をURIに反映
"req://finance"                                    # Business Area
"req://finance/payments"                           # Message Functionality
"req://finance/payments/credit-transfer"           # Message Type
"req://finance/payments/credit-transfer/domestic"  # Variant
```

#### b) バージョン管理

```python
# バージョンを含む場合
"req://finance/features/payment-initiation@iso20022-2019"
"req://finance/features/payment-initiation/v2"

# バージョンを別属性で管理
{
    "uri": "req://finance/features/payment-initiation",
    "iso_source": "20022:pacs.008.001.08",
    "version": "2019"
}
```

#### c) 複数ISO規格の統合

同じ機能が複数のISO規格で定義される場合：

```python
# 統合URI
"req://finance/features/payment-authentication"

# マッピング
mappings = {
    "req://finance/features/payment-authentication": [
        "ISO 20022: pacs.008 authentication block",
        "ISO 27001: A.14.1.3 Authenticating payment instructions",
        "ISO 12812: Mobile payment security"
    ]
}
```

### 4. 自動化の可能性

#### ISO規格からのURI自動生成

```python
def generate_uri_from_iso(standard: str, identifier: str) -> str:
    """ISO識別子から自動的にURIを生成"""
    
    # ISO 20022の場合
    if standard == "20022":
        # pacs.008 -> payment-initiation
        message_type_mapping = {
            "pacs.008": "payment-initiation",
            "camt.053": "account-statement",
            # ...
        }
        
        if identifier.startswith("pacs"):
            return f"req://finance/features/{message_type_mapping.get(identifier, identifier)}"
    
    # デフォルト
    return f"req://iso/{standard}/{identifier.replace('.', '/')}"
```

### 5. 推奨事項

1. **ビジネスドメイン中心のURI設計を採用**
   - 利用者の理解しやすさを優先
   - ISO規格はメタデータとして保持

2. **マッピングテーブルの維持**
   - URI ↔ ISO識別子の双方向マッピング
   - バージョン管理を含む

3. **段階的な拡張**
   - 最初は主要な機能のみURI化
   - 需要に応じて詳細化

4. **ドメインエキスパートとの協働**
   - ISO規格の解釈には専門知識が必要
   - ビジネス用語への適切な変換

### 6. 課題と制限

1. **ISO規格の複雑性**
   - 一つのISO規格が数百のメッセージタイプを含む
   - すべてをURI化するのは現実的でない

2. **ドメイン横断の標準化**
   - 異なるドメインで同じ概念が異なる名前
   - 統一的な命名規則の確立が困難

3. **メンテナンスコスト**
   - ISO規格の更新への追従
   - マッピングの保守

## 結論

ISO規格からLevel 1の標準的なURIを取得することは**技術的に可能**です。ただし、以下の点が成功の鍵となります：

1. **明確なURI設計方針**の確立（ビジネス中心 vs ISO直接参照）
2. **自動化ツール**の開発（ISO解析→URI生成）
3. **ガバナンス体制**の構築（命名規則、更新プロセス）
4. **段階的アプローチ**（コアな機能から開始）

最も実用的なアプローチは、ビジネスドメイン中心のURI設計を採用し、ISO規格への参照はメタデータとして管理することです。これにより、利用者にとって理解しやすく、かつ標準への準拠も担保できるシステムが実現できます。