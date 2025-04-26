#!/usr/bin/env python3
import argparse
import json
import os
import sys
import kuzu
import rdflib
import pyshacl
from pathlib import Path

# パッケージのルートディレクトリを取得
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# データベースとSHACL関連のパス設定
DB_PATH = os.path.join(ROOT_DIR, "db")
DB_NAME = "DesignKG" 
SHAPES_PATH = os.path.join(ROOT_DIR, "design_shapes.ttl")  # SHACL制約ファイル

def init_database():
    """データベースの初期化"""
    db = kuzu.Database(DB_PATH)
    conn = kuzu.Connection(db)
    # Kuzuはグラフを自動的に作成するので明示的に作成する必要はない
    print(f"グラフ {DB_NAME} を使用します")
    
    # Function型のノードを表すラベルとそのプロパティを定義
    try:
        conn.execute(f"""
        CREATE NODE TABLE Function (
            title STRING,
            description STRING,
            type STRING,
            pure BOOLEAN,
            async BOOLEAN,
            PRIMARY KEY (title)
        )
        """)
        print("Function テーブルを作成しました")
    except Exception as e:
        if "already exists" in str(e):
            print("Function テーブルは既に存在します")
        else:
            print(f"テーブル作成エラー: {str(e)}")
    
    # パラメータを表すノードテーブルを作成
    try:
        conn.execute(f"""
        CREATE NODE TABLE Parameter (
            name STRING,
            type STRING,
            description STRING,
            required BOOLEAN,
            PRIMARY KEY (name)
        )
        """)
        print("Parameter テーブルを作成しました")
    except Exception as e:
        if "already exists" in str(e):
            print("Parameter テーブルは既に存在します")
        else:
            print(f"テーブル作成エラー: {str(e)}")
    
    # 関数とパラメータを関連付けるエッジテーブルを作成
    try:
        conn.execute(f"""
        CREATE REL TABLE HasParameter (
            FROM Function TO Parameter,
            order_index INT
        )
        """)
        print("HasParameter エッジテーブルを作成しました")
    except Exception as e:
        if "already exists" in str(e):
            print("HasParameter エッジテーブルは既に存在します")
        else:
            print(f"エッジテーブル作成エラー: {str(e)}")
    
    # 戻り値の型を表すノードテーブルを作成
    try:
        conn.execute(f"""
        CREATE NODE TABLE ReturnType (
            type STRING,
            description STRING,
            PRIMARY KEY (type)
        )
        """)
        print("ReturnType テーブルを作成しました")
    except Exception as e:
        if "already exists" in str(e):
            print("ReturnType テーブルは既に存在します")
        else:
            print(f"テーブル作成エラー: {str(e)}")
    
    # 関数と戻り値の型を関連付けるエッジテーブルを作成
    try:
        conn.execute(f"""
        CREATE REL TABLE HasReturnType (
            FROM Function TO ReturnType
        )
        """)
        print("HasReturnType エッジテーブルを作成しました")
    except Exception as e:
        if "already exists" in str(e):
            print("HasReturnType エッジテーブルは既に存在します")
        else:
            print(f"エッジテーブル作成エラー: {str(e)}")
    
    return conn

def create_design_shapes():
    """設計用のSHACL制約ファイルを作成"""
    if os.path.exists(SHAPES_PATH):
        print(f"{SHAPES_PATH} は既に存在します")
        return
    
    shapes_content = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

# Function型の制約
ex:FunctionShape
    a sh:NodeShape ;
    sh:targetClass ex:Function ;
    sh:property [
        sh:path ex:title ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path ex:type ;
        sh:datatype xsd:string ;
        sh:hasValue "function" ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path ex:description ;
        sh:datatype xsd:string ;
    ] ;
    sh:property [
        sh:path ex:pure ;
        sh:datatype xsd:boolean ;
    ] ;
    sh:property [
        sh:path ex:async ;
        sh:datatype xsd:boolean ;
    ] .

# Parameter型の制約
ex:ParameterShape
    a sh:NodeShape ;
    sh:targetClass ex:Parameter ;
    sh:property [
        sh:path ex:name ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path ex:type ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path ex:required ;
        sh:datatype xsd:boolean ;
    ] .

# ReturnType型の制約
ex:ReturnTypeShape
    a sh:NodeShape ;
    sh:targetClass ex:ReturnType ;
    sh:property [
        sh:path ex:type ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
    ] .
"""
    
    with open(SHAPES_PATH, "w") as f:
        f.write(shapes_content)
    print(f"{SHAPES_PATH} を作成しました")

def validate_against_shacl(rdf_data, shapes_file=SHAPES_PATH):
    """RDFデータをSHACL制約に対して検証"""
    # RDFデータをグラフに変換
    data_graph = rdflib.Graph()
    data_graph.parse(data=rdf_data, format="turtle")
    
    # SHACL制約を読み込む
    shapes_graph = rdflib.Graph()
    shapes_graph.parse(shapes_file, format="turtle")
    
    # 検証実行
    try:
        results = pyshacl.validate(
            data_graph,
            shacl_graph=shapes_graph,
            inference='rdfs',
            debug=False
        )
        conforms, _, report_text = results
        return conforms, report_text
    except Exception as e:
        return False, f"検証エラー: {str(e)}"

def add_function_node(conn, function_data):
    """Function型のノードを追加する"""
    # 基本的な必須フィールドをチェック
    required_fields = ["title", "type", "parameters", "returnType"]
    for field in required_fields:
        if field not in function_data:
            return False, f"必須フィールドがありません: {field}"
    
    # タイトルと説明を取得
    title = function_data["title"]
    description = function_data.get("description", "")
    type_value = function_data["type"]  # "function"であるはず
    pure = function_data.get("pure", True)
    async_value = function_data.get("async", False)
    
    try:
        # 関数ノードを作成
        query = f"""
        CREATE (f:Function {{
            title: '{title}',
            description: '{description}',
            type: '{type_value}',
            pure: {str(pure).lower()},
            async: {str(async_value).lower()}
        }})
        """
        conn.execute(query)
        print(f"関数ノード '{title}' を作成しました")
        
        # パラメータの処理
        params = function_data["parameters"]
        if "properties" in params:
            param_props = params["properties"]
            required_params = params.get("required", [])
            
            for idx, (param_name, param_info) in enumerate(param_props.items()):
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                is_required = param_name in required_params
                
                # パラメータノードを作成
                param_query = f"""
                CREATE (p:Parameter {{
                    name: '{param_name}',
                    type: '{param_type}',
                    description: '{param_desc}',
                    required: {str(is_required).lower()}
                }})
                """
                conn.execute(param_query)
                
                # 関数とパラメータを関連付けるエッジを作成
                edge_query = f"""
                MATCH (f:Function), (p:Parameter)
                WHERE f.title = '{title}' AND p.name = '{param_name}'
                CREATE (f)-[:HasParameter {{ order_index: {idx} }}]->(p)
                """
                conn.execute(edge_query)
                
                print(f"パラメータ '{param_name}' を関数 '{title}' に追加しました")
        
        # 戻り値の型を処理
        return_type = function_data["returnType"]
        return_type_value = return_type.get("type", "any")
        return_desc = return_type.get("description", "")
        
        # 戻り値ノードを作成
        return_query = f"""
        CREATE (r:ReturnType {{
            type: '{return_type_value}',
            description: '{return_desc}'
        }})
        """
        conn.execute(return_query)
        
        # 関数と戻り値を関連付けるエッジを作成
        return_edge_query = f"""
        MATCH (f:Function), (r:ReturnType)
        WHERE f.title = '{title}' AND r.type = '{return_type_value}'
        CREATE (f)-[:HasReturnType]->(r)
        """
        conn.execute(return_edge_query)
        
        print(f"戻り値の型 '{return_type_value}' を関数 '{title}' に追加しました")
        
        return True, f"関数 '{title}' の追加が完了しました"
    
    except Exception as e:
        return False, f"関数ノード追加エラー: {str(e)}"

def extract_rdf_from_function_data(function_data):
    """関数データからRDFデータを抽出する"""
    # タートルフォーマットでRDFデータを生成
    turtle_data = "@prefix ex: <http://example.org/> .\n"
    turtle_data += "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
    
    # 関数ノードを生成
    title = function_data["title"]
    turtle_data += f"ex:{title} a ex:Function .\n"
    
    # titleプロパティを明示的に追加（SHACL制約でminCount=1が要求されているため）
    turtle_data += f'ex:{title} ex:title "{title}" .\n'
    
    # 関数の基本プロパティを追加
    description = function_data.get("description", "")
    if description:
        turtle_data += f'ex:{title} ex:description "{description}" .\n'
    
    type_value = function_data["type"]
    turtle_data += f'ex:{title} ex:type "{type_value}" .\n'
    
    pure = function_data.get("pure", True)
    turtle_data += f'ex:{title} ex:pure "{str(pure).lower()}"^^xsd:boolean .\n'
    
    async_value = function_data.get("async", False)
    turtle_data += f'ex:{title} ex:async "{str(async_value).lower()}"^^xsd:boolean .\n'
    
    # パラメータの処理
    params = function_data["parameters"]
    if "properties" in params:
        param_props = params["properties"]
        required_params = params.get("required", [])
        
        for param_name, param_info in param_props.items():
            param_id = f"{param_name}Param"  # 一意のIDを作成
            # パラメータノードを生成
            turtle_data += f"ex:{param_id} a ex:Parameter .\n"
            turtle_data += f'ex:{param_id} ex:name "{param_name}" .\n'
            
            param_type = param_info.get("type", "any")
            turtle_data += f'ex:{param_id} ex:type "{param_type}" .\n'
            
            param_desc = param_info.get("description", "")
            if param_desc:
                turtle_data += f'ex:{param_id} ex:description "{param_desc}" .\n'
            
            is_required = param_name in required_params
            turtle_data += f'ex:{param_id} ex:required "{str(is_required).lower()}"^^xsd:boolean .\n'
            
            # 関数とパラメータの関連付け
            turtle_data += f"ex:{title} ex:hasParameter ex:{param_id} .\n"
    
    # 戻り値の型を処理
    return_type = function_data["returnType"]
    return_type_value = return_type.get("type", "any")
    return_type_node = f"{title}ReturnType"  # 関数名に基づいた一意のID
    
    turtle_data += f"ex:{return_type_node} a ex:ReturnType .\n"
    turtle_data += f'ex:{return_type_node} ex:type "{return_type_value}" .\n'
    
    return_desc = return_type.get("description", "")
    if return_desc:
        turtle_data += f'ex:{return_type_node} ex:description "{return_desc}" .\n'
    
    # 関数と戻り値の型の関連付け
    turtle_data += f"ex:{title} ex:hasReturnType ex:{return_type_node} .\n"
    
    return turtle_data

def add_function_from_json(conn, json_file):
    """JSONファイルから関数ノードを追加する"""
    try:
        # JSONファイルのパスを絶対パスに変換（相対パスが指定された場合）
        if not os.path.isabs(json_file):
            json_file = os.path.join(ROOT_DIR, json_file)
            
        with open(json_file, 'r') as f:
            function_data = json.load(f)
        
        # RDFデータを抽出
        rdf_data = extract_rdf_from_function_data(function_data)
        
        # SHACL検証
        if os.path.exists(SHAPES_PATH):
            conforms, report = validate_against_shacl(rdf_data)
            if not conforms:
                print("SHACL制約違反があります:")
                print(report)
                return False, report
        
        # 検証に合格したら関数ノードを追加
        success, message = add_function_node(conn, function_data)
        return success, message
    
    except Exception as e:
        return False, f"JSONファイル処理エラー: {str(e)}"

def get_all_functions(conn):
    """すべての関数ノードを取得する"""
    try:
        query_result = conn.execute(f"""
        MATCH (f:Function)
        RETURN f.title, f.description, f.type, f.pure, f.async
        """)
        # QueryResultオブジェクトをリストに変換
        result = []
        while query_result.has_next():
            result.append(query_result.get_next())
        return True, result
    except Exception as e:
        return False, f"クエリ実行エラー: {str(e)}"

def get_function_details(conn, function_title):
    """指定した関数の詳細情報を取得する"""
    try:
        # 関数の基本情報を取得
        function_query = conn.execute(f"""
        MATCH (f:Function)
        WHERE f.title = '{function_title}'
        RETURN f.title, f.description, f.type, f.pure, f.async
        """)
        
        # QueryResultをリストに変換
        function_result = []
        while function_query.has_next():
            function_result.append(function_query.get_next())
        
        if not function_result:
            return False, f"関数 '{function_title}' が見つかりません"
        
        # パラメータ情報を取得
        params_query = conn.execute(f"""
        MATCH (f:Function)-[r:HasParameter]->(p:Parameter)
        WHERE f.title = '{function_title}'
        RETURN p.name, p.type, p.description, p.required, r.order_index
        ORDER BY r.order_index
        """)
        
        # QueryResultをリストに変換
        params_result = []
        while params_query.has_next():
            params_result.append(params_query.get_next())
        
        # 戻り値の型を取得
        return_type_query = conn.execute(f"""
        MATCH (f:Function)-[:HasReturnType]->(r:ReturnType)
        WHERE f.title = '{function_title}'
        RETURN r.type, r.description
        """)
        
        # QueryResultをリストに変換
        return_type_result = []
        while return_type_query.has_next():
            return_type_result.append(return_type_query.get_next())
        
        # 結果を整形して返す
        function_data = {
            "title": function_result[0][0],
            "description": function_result[0][1],
            "type": function_result[0][2],
            "pure": function_result[0][3],
            "async": function_result[0][4],
            "parameters": {
                "properties": {},
                "required": []
            },
            "returnType": {}
        }
        
        # パラメータ情報を追加
        for param in params_result:
            name, type_value, desc, required, _ = param
            function_data["parameters"]["properties"][name] = {
                "type": type_value,
                "description": desc
            }
            if required:
                function_data["parameters"]["required"].append(name)
        
        # 戻り値の型を追加
        if return_type_result and len(return_type_result) > 0:
            function_data["returnType"] = {
                "type": return_type_result[0][0],
                "description": return_type_result[0][1]
            }
        
        return True, function_data
    
    except Exception as e:
        return False, f"クエリ実行エラー: {str(e)}"

def run_tests():
    """テストケースを実行する関数"""
    # テスト実行部分は省略（実装の参照は元ファイルを参照）
    print("テスト実行は未実装です。design.pyを参照してください。")
    return False

def main():
    parser = argparse.ArgumentParser(description='関数型設計のためのKuzuアプリ - Function.Meta.jsonからノード追加機能')
    parser.add_argument('--init', action='store_true', help='データベース初期化（最初に実行してください）')
    parser.add_argument('--add', help='追加するFunction.Meta.jsonファイルのパス（例: example_function.json）')
    parser.add_argument('--list', action='store_true', help='すべての登録済み関数を一覧表示')
    parser.add_argument('--get', help='詳細を取得する関数のタイトル（例: MapFunction）')
    parser.add_argument('--create-shapes', action='store_true', help='SHACL制約ファイルを作成（通常は--initで自動作成）')
    parser.add_argument('--test', action='store_true', help='単体テスト実行（pytest実行には "uv run pytest design.py" を使用）')
    
    # 使用例を表示
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n使用例:")
        print("  # 環境変数の設定とKuzu用ライブラリパスの追加")
        print("  LD_PATH=\"/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib\"")
        print("  # データベース初期化")
        print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --init")
        print("  # サンプル関数を追加")
        print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --add example_function.json")
        print("  # 登録された関数の一覧表示")
        print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --list")
        print("  # MapFunction関数の詳細表示")
        print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --get MapFunction")
        print("  # 単体テスト実行（内部テスト）")
        print("  LD_LIBRARY_PATH=\"$LD_PATH\":$LD_LIBRARY_PATH python -m upsert --test")
        return
    
    args = parser.parse_args()
    
    # テスト実行
    if args.test:
        run_tests()
        return
    
    # SHACL制約ファイルの作成
    if args.create_shapes:
        create_design_shapes()
        return
    
    # データベース初期化
    if args.init or not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH, exist_ok=True)
        create_design_shapes()
    
    conn = init_database()
    
    # 関数の追加
    if args.add:
        success, message = add_function_from_json(conn, args.add)
        if success:
            print(f"関数を追加しました: {message}")
        else:
            print(f"関数の追加に失敗しました: {message}")
    
    # 関数一覧の表示
    if args.list:
        success, result = get_all_functions(conn)
        if success:
            print("登録されている関数:")
            for func in result:
                print(f"- {func[0]}: {func[1]}")
        else:
            print(f"関数一覧の取得に失敗しました: {result}")
    
    # 関数詳細の表示
    if args.get:
        success, result = get_function_details(conn, args.get)
        if success:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"関数詳細の取得に失敗しました: {result}")

if __name__ == "__main__":
    main()
