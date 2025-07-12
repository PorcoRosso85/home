# MinIO Identity and Access Management Reference

## 概要
MinIOのIAMドキュメントから、S3互換クライアントの認証方法について重要な情報を抽出。

## 認証方法

### AWS Signature Version 4 Protocol
- S3/MinIO管理APIへのアクセスには有効なアクセスキーとシークレットキーが必要
- 非推奨のSignature Version 2 Protocolもサポート

### アイデンティティプロバイダー (IDP)
1. **内部MinIO IDP**
2. **OpenID Connect (OIDC)**
3. **Active Directory/LDAP**
4. **外部認証プラグイン**

## アクセス制御の原則

### ポリシーベースアクセス制御 (PBAC)
- ポリシーは特定のアクションと条件を定義
- デフォルトでは「明示的に参照されていないアクションやリソースへのアクセスを拒否」

### 主要な認証特性
- 認証（本人確認）と認可（権限検証）の両方が必要
- AWS IAMポリシー構文と互換性あり
- ポリシーによる細かいアクセス制御をサポート
- 「Deny」ルールは「Allow」ルールを上書き

## Cloudflare R2 CLIへの応用

このドキュメントは、S3 API互換性と柔軟なアイデンティティ管理戦略を強調しており、
R2 CLI認証設計の参考になる。

### 参考URL
- https://min.io/docs/minio/linux/administration/identity-access-management.html