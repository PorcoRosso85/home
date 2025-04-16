# シナリオ：ユーザー登録処理
# Copy
# [UI層] UserRegistrationRequest 
#   → [アプリ層] UserCommand 
#   → [永続化層] UserRecord 
#   ← [レスポンス] UserRegistrationResponse

# 1. UIイベントメッセージの登録
/* UI入力用メッセージ */
:put message {
  message_id: Uuid("ui_req_1"),
  full_name: "UserRegistrationRequest",
  version: 1,
  description: "UIからの登録リクエスト"
}

/* フィールド定義 */
:put field { field_id: Uuid("f1"), message_id: Uuid("ui_req_1"), field_name: "username", field_type: "string", tag_number: 1, is_optional: false, is_map: false, map_info: {}, default_value: "" }
:put field { field_id: Uuid("f2"), message_id: Uuid("ui_req_1"), field_name: "email", field_type: "string", tag_number: 2, is_optional: false, is_map: false, map_info: {}, default_value: "" }
:put field { field_id: Uuid("f3"), message_id: Uuid("ui_req_1"), field_name: "password", field_type: "string", tag_number: 3, is_optional: false, is_map: false, map_info: {}, default_value: "" }

/* コマンドオブジェクト */
:put message {
  message_id: Uuid("cmd_1"),
  full_name: "UserCommand",
  version: 1,
  description: "ドメイン層へのコマンド"
}

:put field { field_id: Uuid("f4"), message_id: Uuid("cmd_1"), field_name: "hashed_password", field_type: "bytes", tag_number: 1, is_optional: false, is_map: false, map_info: {}, default_value: "" }

/* 実行フローの定義 */
:put execution {
  source: Uuid("cmd_1"),  // UserCommand
  target: Uuid("ui_req_1"), // UserRegistrationRequest
  flow_type: "execution_flow"
}

/* データベースモデル */
:put message {
  message_id: Uuid("db_1"),
  full_name: "UserRecord",
  version: 1,
  description: "DB保存用スキーマ"
}

:put field { field_id: Uuid("f5"), message_id: Uuid("db_1"), field_name: "user_id", field_type: "int64", tag_number: 1, is_optional: false, is_map: false, map_info: {}, default_value: "" }
:put field { field_id: Uuid("f6"), message_id: Uuid("db_1"), field_name: "created_at", field_type: "int64", tag_number: 2, is_optional: false, is_map: false, map_info: {}, default_value: "" }

/* 実行フローの定義 */
:put execution {
  source: Uuid("db_1"),  // UserRecord
  target: Uuid("cmd_1"), // UserCommand
  flow_type: "execution_flow"
}

/* APIレスポンス */
:put message {
  message_id: Uuid("res_1"),
  full_name: "UserRegistrationResponse",
  version: 1,
  description: "クライアントへの返却データ"
}

:put field { field_id: Uuid("f7"), message_id: Uuid("res_1"), field_name: "user_id", field_type: "int64", tag_number: 1, is_optional: false, is_map: false, map_info: {}, default_value: "" }
:put field { field_id: Uuid("f8"), message_id: Uuid("res_1"), field_name: "status", field_type: "enum", type_name: "RegistrationStatus", tag_number: 2, is_optional: false, is_map: false, map_info: {}, default_value: "" }

/* DBモデルへの依存 */
:put dependency {
  source: Uuid("res_1"),
  target: Uuid("enum_1"),
  dep_type: "structural"
}

/* Enum定義 */
:put message {
  message_id: Uuid("enum_1"),
  full_name: "RegistrationStatus",
  version: 1,
  is_enum: true
}

:put field { field_id: Uuid("f9"), message_id: Uuid("enum_1"), field_name: "SUCCESS", field_type: "enum_value", type_name: "RegistrationStatus", tag_number: 0, is_optional: false, is_map: false, map_info: {}, default_value: "" }
:put field { field_id: Uuid("f10"), message_id: Uuid("enum_1"), field_name: "INVALID_EMAIL", field_type: "enum_value", type_name: "RegistrationStatus", tag_number: 1, is_optional: false, is_map: false, map_info: {}, default_value: "" }

/* レスポンスからEnumへの依存 */
:put execution {
  source: Uuid("res_1"),
  target: Uuid("enum_1"),
  flow_type: "structural"
}
// 構造的依存はfieldとparent_idから自動導出
// 構造的依存の命名パターン監視 full_name like "%.%" (ドットを含むネスト名)
?[s, t] := 
  *field{message_id: s, field_type: "message"},
  *message{full_name: type_name, message_id: t}

// ネスト構造の依存関係
?[parent, child] := 
  *message{message_id: child, parent_id: parent}

// 実行フローに特化した循環検出
?[
    path,
    is_cyclic
] := *execution{flow_type: "execution_flow", source: s, target: t},
*message{message_id: s, full_name: s_name},
*message{message_id: t, full_name: t_name},
path = [s_name, t_name],
is_cyclic = false
:recursive [
  ?[
      path + [new_t_name],
      is_cyclic or (s_name == new_t_name)
  ] := *execution{flow_type: "execution_flow", source: t, target: new_t},
  *message{message_id: new_t, full_name: new_t_name},
  path = prev_path,
  prev_path[-1] == t_name,
  length(prev_path) < 10
]
