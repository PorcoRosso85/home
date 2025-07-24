# 認証と権限の分離に関する議論

## 現状分析

### 既存実装の確認
- **WorkflowPermissionSystem**: 組織管理、承認ワークフロー、権限管理が混在（認証機能なし）
- **SimpleAuthSystem**: 認証（ユーザー作成、パスワード認証、セッション管理）と権限（ロール割り当て、権限チェック）が一つのクラスに混在

## 責務の整理

### 認証 (Authentication)
- ユーザーの身元確認
- パスワード管理
- セッション/トークン管理
- ログイン/ログアウト

### 権限 (Authorization)
- ロール管理
- 権限チェック
- リソースアクセス制御
- 権限の委譲

## 分離アプローチの検討

### 理想的な完全分離
```
src/poc/
├── authentication/     # 認証パッケージ
├── authorization/      # 権限パッケージ
└── auth_integration/   # 統合層
```

**メリット**: 単一責任原則、独立した進化、再利用性、テスタビリティ

### 現実的な課題
- 同じユーザー情報を参照
- 同じデータベースを使用
- 過度な分離は複雑性を増す

## 推奨アプローチ

**内部で責務を分離しつつ、同じパッケージ内に配置**

```
auth/
├── models.py           # 共通モデル
├── repository.py       # DB アクセス
├── authentication/     # 認証の責務
│   ├── password.py
│   └── session.py
├── authorization/      # 権限の責務
│   ├── rbac.py
│   └── permissions.py
└── tests/
```

### 利点
1. 共通のデータベース・モデルを効率的に利用
2. 責務は明確に分離
3. 必要に応じて独立したパッケージに分割可能
4. 実装の複雑性を抑制

### 実装例
```python
# 共通リポジトリを使用
class UserRepository:
    def get_user(self, user_id) -> User
    def get_user_with_roles(self, user_id) -> UserWithRoles

# 各サービスは責務に集中
class AuthenticationService:
    def __init__(self, user_repo: UserRepository)
    
class AuthorizationService:
    def __init__(self, user_repo: UserRepository)
```

## 結論
完全なパッケージ分離よりも、**単一パッケージ内での責務分離**が実用的。共通リソースを効率的に活用しつつ、各コンポーネントの責務を明確に保つことで、保守性と拡張性を確保する。