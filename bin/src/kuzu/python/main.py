#!/usr/bin/env python3
import argparse
import os
import sys
import json
import kuzu
import rdflib
import pyshacl
from pathlib import Path

# データベースとSHACL関連のパス設定
DB_PATH = "db"
DB_NAME = "ShapedKG" 
SHAPES_PATH = "shapes.ttl"  # SHACL制約ファイル

def init_database():
    """データベースの初期化"""
    db = kuzu.Database(DB_PATH)
    conn = kuzu.Connection(db)
    try:
        conn.execute(f"CREATE GRAPH {DB_NAME}")
        print(f"グラフ {DB_NAME} を作成しました")
    except Exception as e:
        if "already exists" in str(e):
            print(f"グラフ {DB_NAME} は既に存在します")
        else:
            print(f"グラフ作成エラー: {str(e)}")
            # エラーを出力して続行
    return conn

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

def execute_cypher(conn, query):
    """Cypherクエリの実行"""
    try:
        result = conn.execute(query)
        return True, result
    except Exception as e:
        return False, str(e)

def extract_rdf_from_cypher(query):
    """Cypherクエリから追加されるRDFデータの抽出"""
    # このシンプル実装では、CREATE文からTripleを推測
    # 実際のアプリでは、より堅牢なパーサーが必要
    if "CREATE" not in query.upper():
        return None
    
    # 簡易パース - 実際のアプリではもっと堅牢に
    turtle_data = ""
    
    # ノード作成の処理
    if "CREATE" in query.upper() and ":" in query:
        try:
            # ラベルの抽出
            label_start = query.find(":")
            if label_start > 0:
                label_end = query.find(" ", label_start)
                if label_end == -1:
                    label_end = query.find("}", label_start)
                if label_end == -1:
                    label_end = len(query)
                
                label = query[label_start+1:label_end].strip()
                
                # 簡易的なTurtle形式データの生成
                turtle_data = "@prefix ex: <http://example.org/> .\n"
                turtle_data += "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
                turtle_data += f"ex:resource a ex:{label} .\n"
                
                # プロパティの抽出（超簡易版）
                if "{" in query and "}" in query:
                    props_start = query.find("{")
                    props_end = query.find("}")
                    props_str = query[props_start+1:props_end].strip()
                    
                    # name: 'value' の形式を解析
                    props = props_str.split(",")
                    for prop in props:
                        if ":" in prop:
                            key, value = prop.split(":", 1)
                            key = key.strip()
                            value = value.strip().strip("'\"")
                            
                            # 数値かどうかを判定して適切な型を設定
                            try:
                                # 整数の場合
                                if value.isdigit():
                                    turtle_data += f"ex:resource ex:{key} \"{value}\"^^xsd:integer .\n"
                                # 浮動小数点の場合
                                elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                                    turtle_data += f"ex:resource ex:{key} \"{value}\"^^xsd:decimal .\n"
                                # それ以外は文字列として処理
                                else:
                                    turtle_data += f"ex:resource ex:{key} \"{value}\" .\n"
                            except:
                                # 変換に失敗した場合は文字列として扱う
                                turtle_data += f"ex:resource ex:{key} \"{value}\" .\n"
        except Exception as e:
            print(f"クエリ解析エラー: {str(e)}")
            print(f"生成されたTurtle: {turtle_data}")
    
    # デバッグ用にTurtleデータを表示
    print(f"生成されたTurtle:\n{turtle_data}")
    
    return turtle_data

def main():
    parser = argparse.ArgumentParser(description='TTL制約下でのKuzuアプリ')
    parser.add_argument('query', nargs='?', help='実行するCypherクエリ')
    parser.add_argument('--init', action='store_true', help='データベース初期化')
    parser.add_argument('--shapes', help='SHACL制約ファイルのパス', default=SHAPES_PATH)
    parser.add_argument('--test', action='store_true', help='テストを実行')
    
    args = parser.parse_args()
    
    # テスト実行
    if args.test:
        run_tests()
        return
    
    if not args.query:
        parser.print_help()
        return
    
    # データベース接続
    if args.init or not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH, exist_ok=True)
    
    conn = init_database()
    
    # Cypherクエリの場合
    if "CREATE" in args.query.upper():
        # 追加するRDFデータを抽出
        rdf_data = extract_rdf_from_cypher(args.query)
        if rdf_data:
            # SHACL検証
            conforms, report = validate_against_shacl(rdf_data, args.shapes)
            if conforms:
                print("SHACL制約検証に合格しました。クエリを実行します。")
                success, result = execute_cypher(conn, args.query)
                if success:
                    print("クエリ実行成功")
                    print(result)
                else:
                    print(f"クエリ実行エラー: {result}")
            else:
                print("SHACL制約違反があります:")
                print(report)
        else:
            print("RDFデータの抽出に失敗しました。クエリの形式を確認してください。")
    else:
        # 通常のクエリ(SELECT等)はそのまま実行
        success, result = execute_cypher(conn, args.query)
        if success:
            print("クエリ実行成功")
            print(result)
        else:
            print(f"クエリ実行エラー: {result}")

def run_single_test(test_name, query, expected_valid):
    """単一のテストを実行"""
    print(f"\n実行中: {test_name}")
    
    # クエリからRDFデータを抽出
    rdf_data = extract_rdf_from_cypher(query)
    
    if rdf_data is None:
        print("エラー: RDFデータの抽出に失敗しました")
        return False
    
    # SHACL検証を実行
    is_valid, report = validate_against_shacl(rdf_data)
    
    # 検証結果を表示
    print(f"生成されたRDF:\n{rdf_data}")
    print(f"検証結果: {is_valid}")
    if not is_valid:
        print(f"検証レポート:\n{report}")
    
    # 期待される結果と一致するか検証
    result = is_valid == expected_valid
    if result:
        print(f"テスト成功: 期待通りの結果 ({expected_valid})")
    else:
        print(f"テスト失敗: 期待された検証結果は {expected_valid} でしたが、実際は {is_valid} でした")
    
    return result

# テストケースの定義 (テスト名, クエリ, 期待される検証結果)
TEST_CASES = [
    ("有効なPersonの作成", "CREATE (p:Person {name: 'Alice', age: 30})", True),
    ("無効なPersonの作成（年齢が負数）", "CREATE (p:Person {name: 'Bob', age: -5})", False),
    ("無効なPersonの作成（名前なし）", "CREATE (p:Person {age: 25})", False),
    ("有効なCityの作成", "CREATE (c:City {name: 'Tokyo', population: 14000000})", True),
    ("無効なCityの作成（人口が負数）", "CREATE (c:City {name: 'Nagoya', population: -100})", False),
]

# pytestで検出されるテスト関数
def test_person_valid():
    """有効なPersonの作成テスト"""
    query = "CREATE (p:Person {name: 'Alice', age: 30})"
    rdf_data = extract_rdf_from_cypher(query)
    assert rdf_data is not None, "RDFデータの抽出に失敗"
    is_valid, _ = validate_against_shacl(rdf_data)
    assert is_valid is True, "有効なPersonデータが制約検証に失敗"

def test_person_invalid_age():
    """無効なPerson（年齢が負数）のテスト"""
    query = "CREATE (p:Person {name: 'Bob', age: -5})"
    rdf_data = extract_rdf_from_cypher(query)
    assert rdf_data is not None, "RDFデータの抽出に失敗"
    is_valid, _ = validate_against_shacl(rdf_data)
    assert is_valid is False, "無効なPersonデータ（年齢が負数）が制約検証を通過"

def test_person_missing_name():
    """無効なPerson（名前なし）のテスト"""
    query = "CREATE (p:Person {age: 25})"
    rdf_data = extract_rdf_from_cypher(query)
    assert rdf_data is not None, "RDFデータの抽出に失敗"
    is_valid, _ = validate_against_shacl(rdf_data)
    assert is_valid is False, "無効なPersonデータ（名前なし）が制約検証を通過"

def test_city_valid():
    """有効なCityの作成テスト"""
    query = "CREATE (c:City {name: 'Tokyo', population: 14000000})"
    rdf_data = extract_rdf_from_cypher(query)
    assert rdf_data is not None, "RDFデータの抽出に失敗"
    is_valid, _ = validate_against_shacl(rdf_data)
    assert is_valid is True, "有効なCityデータが制約検証に失敗"

def test_city_invalid_population():
    """無効なCity（人口が負数）のテスト"""
    query = "CREATE (c:City {name: 'Nagoya', population: -100})"
    rdf_data = extract_rdf_from_cypher(query)
    assert rdf_data is not None, "RDFデータの抽出に失敗"
    is_valid, _ = validate_against_shacl(rdf_data)
    assert is_valid is False, "無効なCityデータ（人口が負数）が制約検証を通過"

def run_tests():
    """テストケースを実行する関数"""
    # 独自のテスト実行ロジック（コマンドライン引数での--testオプション用）
    print("=" * 50)
    print("SHACL制約テストの実行")
    print("=" * 50)
    
    # テスト結果の集計
    total_tests = len(TEST_CASES)
    passed_tests = 0
    
    # すべてのテストケースを実行
    for test_name, query, expected_valid in TEST_CASES:
        result = run_single_test(test_name, query, expected_valid)
        if result:
            passed_tests += 1
    
    # 結果のサマリーを表示
    print("\n" + "=" * 50)
    print(f"テスト結果: {passed_tests}/{total_tests} 成功")
    print("=" * 50)

if __name__ == "__main__":
    main()
