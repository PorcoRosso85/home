protobufメッセージの大部分を表現できる設計になっています。

 1 message スキーマ:
    • message_id で一意性を確保し、full_name で完全修飾名を格納可能。
    • parent_id でネストされたメッセージ構造(親子関係)を表現可能。
    • is_enum フラグで列挙型(enum)の扱いを区別。
 2 field スキーマ:
    • message_id で所属するメッセージを特定。
    • field_type, type_name でフィールドの型情報を格納可能。
    • is_repeated, is_optional, is_map で protobuf の繰り返し、オプション、マップ型をサポート。
    • map_info, default_value で複雑な型やデフォルト値の情報を保持。

 1 現状のスキーマで表現可能な主な要素：
    • ネスト構造（parent_idによる親子関係）
    • 基本データ型（field_typeによる指定）
    • ユーザ定義型（type_nameによる参照）
    • 繰り返し（is_repeated）
    • オプショナル（is_optional）
    • マップ型（is_map + map_info）
    • デフォルト値（default_value）
    • 列挙型（is_enumフラグ）
 2 表現できない/未実装の主な要素： • oneof構造：

   
TODO
 1 参照整合性制約:
    • field スキーマの type_name が他の message または enum を参照する場合、その存在確認が未実装。
    • コメントにある「!(field_type = 'message' and !exists(*message{message_id:
      target_id}))」の制約が実装されていない。
 2 oneof フィールド:
    • protobuf の oneof 構造を直接表現する列や制約が不足。
 3 map 型の詳細:
    • map_info が Json 型で格納されているが、具体的な検証ロジックが未実装。
 4 enum のバージョン管理:
    • enum スキーマで version のユニーク制約が未実装。

# 不足している要素例
    oneof_group: String?  # oneofグループ名を保持する列が必要

   • 完全な参照整合性：

    # fieldスキーマのTODOコメントにある
    # 「!(field_type = 'message' and !exists(*message{message_id: target_id}))」
    # の制約が未実装（外部キー制約不足）

   • Map型の厳密な検証：

    # map_info: Json に格納されるが、key/valueの型情報を
    # 構造化して保持する仕組みが不足

   • パッケージスコープ：

    # messageスキーマにpackage情報がないため
    # 同名メッセージのパッケージ違いを区別できない

 3 改善が必要な設計ポイント：

    # messageスキーマに追加が必要な要素例
    package: String?  # パッケージ名
    syntax: String    # proto2/proto3
    is_extend: Bool   # 拡張メッセージかどうか

    # fieldスキーマに追加が必要な要素例
    json_name: String?  # JSONマッピング用
    options: Json       # フィールドオプション

 4 テスト観点での課題：

    # 現在のテストケース（test_ddl）はスキーマ作成のみを検証
    # 実際のProtobuf構造を投入した際の整合性チェックテストが不足


結論：
基本的なメッセージ構造の表現は可能ですが、Protobufのより高度な機能（oneof、オプション、パッケージス
コープなど）を完全にサポートするには追加実装が必要です。特に参照整合性と型システムの厳密な検証が今
後の課題と言えます。
""
# Message スキーマ TODO

1. 拡張要素
   - package: String?  # パッケージ名
   - syntax: String    # proto2/proto3
   - is_extend: Bool   # 拡張メッセージかどうか

2. ネスト構造
   - 深いネスト構造のパフォーマンス改善
   - 循環依存の検出メカニズム

3. バージョン管理
   - 異なるバージョンのメッセージ定義が並存した場合の一意性保証
   - バージョン間の互換性管理

4. 拡張機能
   - oneof 構造のサポート
   - 拡張フィールドの管理
