# % プロセス詳細化クエリ
# % このクエリは、既存のプロセスをより詳細なプロセスに置き換えるために使用されます。
# % TODO transaction
# % パラメータ形式: [元プロセスsource, 元プロセスtarget, 置換用メッセージIDリスト]
# % TODO :parameter?
# % :parameter original_source Uuid
# % :parameter original_target Uuid
# % :parameter new_steps [Uuid]

# % 0. transaction開始
# % 1. 元の実行フロー削除
# :remove execution {
#     source: $original_source,
#     target: $original_target,
#     flow_type: "execution_flow"
# }

# % 2. 新しい実行チェーン構築
# :put execution { source: s, target: t, flow_type: "execution_flow" } :<-
# ?[s, t] := 
#     // チェーン構築 [source, ...new_steps, target]
#     full_chain = concat([$original_source], $new_steps, [$original_target]),
#     // 隣接ノードペア生成
#     pairs = windows(full_chain, 2),
#     [s, t] in pairs

# % 3. 構造的依存関係自動検出（既存ルール再利用）
# ?[s, t] := 
#     *field{message_id: s, field_type: "message", type_name: t_name},
#     *message{full_name: t_name, message_id: t}

# % 4. 循環参照検証（既存ルール拡張）
# ?[
#     path,
#     is_cyclic
# ] := *execution{flow_type: "execution_flow", source: s, target: t},
# *message{message_id: s, full_name: s_name},
# *message{message_id: t, full_name: t_name},
# path = [s_name, t_name],
# is_cyclic = false
# :recursive [
#   ?[
#       path + [new_t_name],
#       is_cyclic or (s_name == new_t_name)
#   ] := *execution{flow_type: "execution_flow", source: t, target: new_t},
#   *message{message_id: new_t, full_name: new_t_name},
#   path = prev_path,
#   prev_path[-1] == t_name,
#   length(prev_path) < 10
# ]
# % 0. transaction終了
