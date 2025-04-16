# Field スキーマ TODO

1. 参照整合性制約
   - type_name が他の message/enum を参照する場合の存在確認
   - 「!(field_type = 'message' and !exists(*message{message_id: target_id}))」制約の実装

2. Map型の詳細
   - map_info の検証ロジック実装
   - key/valueの型情報を構造化して保持する仕組み

3. 型システム拡張
   - oneof 構造のサポート
   - ジェネリクス表現の可能性検討
   - ユニオン型のサポート検討
