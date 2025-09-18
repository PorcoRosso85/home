# 層構造（Layered Architecture）

クリーンアーキテクチャやオニオンアーキテクチャに触発された、以下の3層構造を基本とします。

## レイヤー

1.  **Domain（ドメイン層）**: アプリケーションの核となるビジネスルールとデータ構造を定義します。この層は、他のどの層にも依存しません。
2.  **Application（アプリケーション層）**: ユースケースを実装します。ドメイン層のオブジェクトや関数を組み合わせて、具体的なアプリケーションの機能を実現します。インフラストラクチャ層に定義されたインターフェースに依存します。
3.  **Infrastructure（インフラストラクチャ層）**: データベース、外部API、UIフレームワークなど、技術的な詳細を実装します。アプリケーション層のインターフェースを実装（実装）し、副作用をこの層に閉じ込めます。

この3層に加え、プロジェクトに応じて**Presentation（プレゼンテーション層）**の追加も議論されうる。

## 依存関係のルール

依存の方向は、必ず **Infrastructure → Application → Domain** の一方向でなければなりません。
Presentation層を追加する場合は、**Presentation → Application → Domain** となります。

- Domainは何も知らない。
- ApplicationはDomainを知っている。
- InfrastructureはApplicationとDomainを知っている。
- Presentation（存在する場合）はApplicationとDomainを知っている。

このルール（The Dependency Rule）により、ビジネスロジックを技術的詳細から完全に分離し、テスト容易性と保守性を高めます。
