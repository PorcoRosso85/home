class SchemaError(Exception):
    pass


def create_message_schema(client):
    """Create message table schema with constraints.
    pk(message_id)
    unique(full_name)
    fk(parent_id) => message(message_id), trigger(on rm)で代用？

    TODO
    """
    try:
        # スキーマ定義
        result = client.run('''
            :create message {
                message_id: Uuid,
                =>
                full_name: String,
                parent_id: Uuid?,
                version: Int,
                description: String,
                is_enum: Bool,
            }
        ''')

        # full_name のユニーク制約
        client.run('''
            ::set_triggers message
            on put {
                ?[full_name] := _new[full_name]
                ?[count] := *message{full_name}, count = 1
                :assert count == 0
            }
        ''')

        # parent_id の参照整合性制約
        client.run('''
            ::set_triggers message
            on put {
                ?[parent_id] := _new[parent_id]
                ?[exists] := *message{message_id: parent_id}, exists = 1
                :assert exists == 1
            }
        ''')

        return result['status'][0]
    except Exception as e:
        return SchemaError(str(e))

def create_field_schema(client):
    """Create field table schema with constraints.

    TODO:
    - 「constraint check_ref」:
        ↳ 『(!(field_type = 'message' and ...』の判定条件が曖昧
        ↳ 方向性制約と存在性証明の組み合わせロジックを定義
    - 参照整合性制約のカマーの削除(構文エラー)
    """
    try:
        # スキーマ定義
        result = client.run('''
            :create field {
                field_id: Uuid,
                =>
                message_id: Uuid,
                field_name: String,
                field_type: String,
                type_name: String,
                tag_number: Int,
                is_repeated: Bool,
                is_optional: Bool,
                is_map: Bool,
                map_info: Json,
                default_value: String,
            }
        ''')

        # message_id の参照整合性制約
        client.run('''
            ::set_triggers field
            on put {
                ?[message_id] := _new[message_id]
                ?[exists] := *message{message_id}, exists = 1
                :assert exists == 1
            }
        ''')

        # field_type = 'message' の場合の参照整合性制約
        client.run('''
            ::set_triggers field
            on put {
                ?[field_type, type_name] := _new[field_type, type_name]
                ?[exists] := field_type == 'message' => *message{full_name: type_name}, exists = 1
                :assert exists == 1
            }
        ''')

        return result['status'][0]
    except Exception as e:
        return SchemaError(str(e))

def create_enum_schema(client):
    """Create enum table schema.

    TODO:
    - 列制約が未実装(nullable等の設定)
    - バージョン番号のユニーク制約要検討
    """
    try:
        result = client.run('''
            :create enum {
                enum_id: Uuid,
                name: String,
                package: String,
                values: Json,
                version: Int,
                # =>
                # pk(enum_id)
            }
        ''')
        return result['status'][0]
    except Exception as e:
        return SchemaError(str(e))

def create_execution_schema(client):
    """Create execution table schema with constraints.

    TODO:
    - "constraint no_self_ref":
        ↳ 'source != target' 自己参照の禁止ロジック正規化
    - "constraint valid_flow_type":
        ↳ フロータイプ指定の検証方法再考

    executionを削除するときは単体でOK, 
    """
    try:
        result = client.run('''
            :create execution {
                source: Uuid,
                target: Uuid,
                flow_type: String,
                # =>
                # constraint no_self_ref { source != target }
                # constraint valid_flow_type { flow_type == 'execution_flow' }
            }
        ''')
        return result['status'][0]
    except Exception as e:
        return SchemaError(str(e))

# def create_all_schemas(client):
#     results = {}
#     results['message'] = create_message_schema(client)
#     results['field'] = create_field_schema(client)
#     results['enum'] = create_enum_schema(client)
#     results['execution'] = create_execution_schema(client)
#     return results


from .. import dbg
if dbg.is_pytest():
    from ..infrastructure import logger
    from pycozo.client import Client
    logger.debug("hello pytest")

    client = Client()

    def test_ddl():
        assert create_message_schema(client) == 'OK'
        assert create_field_schema(client) == 'OK'
        assert create_enum_schema(client) == 'OK'
        assert create_execution_schema(client) == 'OK'
