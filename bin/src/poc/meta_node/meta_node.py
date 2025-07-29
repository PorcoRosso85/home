"""
Meta Node POC - Cypherクエリをノードに格納して動的実行する仕組み

このモジュールは、グラフノード自体にクエリロジックを持たせ、
メタプログラミング的なアプローチでグラフ操作を実現します。
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import kuzu


class QueryNotFoundError(Exception):
    """クエリノードが見つからない場合の例外"""
    pass


class CypherSyntaxError(Exception):
    """Cypherクエリの構文エラー"""
    pass


@dataclass
class QueryNode:
    """Cypherクエリを格納するノードのデータ構造"""
    name: str
    description: str
    cypher_query: str


@dataclass
class GuardrailRule(QueryNode):
    """ガードレールルールを表すデータ構造（QueryNodeを拡張）"""
    rule_type: str  # "validation", "transformation", etc.
    condition: str  # 実行条件（Python式）
    action: str     # 実行アクション（Python式）
    priority: int   # 実行優先度（小さいほど高優先度）
    active: bool    # アクティブフラグ


class MetaNode:
    """メタノードシステムのメインクラス"""
    
    def __init__(self, db: kuzu.Database):
        """
        メタノードシステムを初期化
        
        Args:
            db: KuzuDatabase インスタンス
        """
        self.db = db
        self._initialize_schema()
    
    def _initialize_schema(self):
        """QueryNodeテーブルのスキーマを初期化"""
        conn = kuzu.Connection(self.db)
        # QueryNodeテーブルが存在しない場合は作成
        try:
            conn.execute("""
                CREATE NODE TABLE QueryNode(
                    name STRING,
                    description STRING,
                    cypher_query STRING,
                    PRIMARY KEY(name)
                )
            """)
        except:
            # テーブルが既に存在する場合は無視
            pass
        
        # GuardrailRuleテーブルが存在しない場合は作成
        try:
            conn.execute("""
                CREATE NODE TABLE GuardrailRule(
                    name STRING,
                    description STRING,
                    cypher_query STRING,
                    rule_type STRING,
                    condition STRING,
                    action STRING,
                    priority INT64,
                    active BOOLEAN,
                    PRIMARY KEY(name)
                )
            """)
        except:
            # テーブルが既に存在する場合は無視
            pass
    
    def create_query_node(self, query_node: QueryNode) -> str:
        """
        クエリノードを作成して保存
        
        Args:
            query_node: 保存するQueryNodeインスタンス
            
        Returns:
            作成されたノードのname（ID）
        """
        conn = kuzu.Connection(self.db)
        conn.execute(
            """
            CREATE (:QueryNode {
                name: $name,
                description: $description,
                cypher_query: $cypher_query
            })
            """,
            {
                "name": query_node.name,
                "description": query_node.description,
                "cypher_query": query_node.cypher_query
            }
        )
        return query_node.name
    
    def get_query_node(self, name: str) -> QueryNode:
        """
        名前でクエリノードを取得
        
        Args:
            name: 取得するクエリノードの名前
            
        Returns:
            QueryNodeインスタンス
            
        Raises:
            ValueError: クエリノードが存在しない場合
        """
        conn = kuzu.Connection(self.db)
        result = conn.execute(
            "MATCH (q:QueryNode {name: $name}) RETURN q",
            {"name": name}
        )
        
        if result.has_next():
            row = result.get_next()
            node_data = row[0]
            return QueryNode(
                name=node_data["name"],
                description=node_data["description"],
                cypher_query=node_data["cypher_query"]
            )
        raise ValueError(f"Query node '{name}' not found")
    
    def create_guardrail_rule(
        self,
        rule_type: str,
        name: str,
        description: str,
        priority: int,
        active: bool,
        cypher_query: Optional[str] = None,
        condition: Optional[str] = None,
        action: Optional[str] = None
    ) -> str:
        """
        ガードレールルールを作成して保存
        
        Args:
            rule_type: ルールのタイプ（例: "validation", "transformation"）
            name: ルールの名前（一意）
            description: ルールの説明
            priority: 実行優先度（小さいほど高優先度）
            active: アクティブフラグ
            cypher_query: 実行するCypherクエリ（新形式・オプション）
            condition: 実行条件（Python式・旧形式・オプション）
            action: 実行アクション（Python式・旧形式・オプション）
            
        Returns:
            作成されたルールのname（ID）
        """
        conn = kuzu.Connection(self.db)
        conn.execute(
            """
            CREATE (:GuardrailRule {
                name: $name,
                description: $description,
                cypher_query: $cypher_query,
                rule_type: $rule_type,
                condition: $condition,
                action: $action,
                priority: $priority,
                active: $active
            })
            """,
            {
                "name": name,
                "description": description,
                "cypher_query": cypher_query or "",
                "rule_type": rule_type,
                "condition": condition or "",
                "action": action or "",
                "priority": priority,
                "active": active
            }
        )
        return name
    
    def get_guardrail_rules(self, active_only: bool = True) -> List[GuardrailRule]:
        """
        ガードレールルールを取得（優先度順）
        
        Args:
            active_only: Trueの場合、アクティブなルールのみ取得
            
        Returns:
            GuardrailRuleのリスト（優先度順）
        """
        conn = kuzu.Connection(self.db)
        
        if active_only:
            query = """
                MATCH (r:GuardrailRule)
                WHERE r.active = true
                RETURN r
                ORDER BY r.priority ASC
            """
        else:
            query = """
                MATCH (r:GuardrailRule)
                RETURN r
                ORDER BY r.priority ASC
            """
        
        result = conn.execute(query)
        
        rules = []
        while result.has_next():
            row = result.get_next()
            rule_data = row[0]
            rules.append(GuardrailRule(
                name=rule_data["name"],
                description=rule_data["description"],
                cypher_query=rule_data["cypher_query"],
                rule_type=rule_data["rule_type"],
                condition=rule_data["condition"],
                action=rule_data["action"],
                priority=rule_data["priority"],
                active=rule_data["active"]
            ))
        
        return rules
    
    def update_guardrail_rule(self, name: str, **kwargs) -> None:
        """
        ガードレールルールを更新
        
        Args:
            name: 更新するルールの名前
            **kwargs: 更新するフィールドと値
        """
        conn = kuzu.Connection(self.db)
        
        # 更新可能なフィールドのみフィルタリング
        valid_fields = {"description", "rule_type", "condition", "action", "priority", "active"}
        update_fields = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not update_fields:
            return
        
        # SET句を動的に構築
        set_clauses = [f"r.{field} = ${field}" for field in update_fields]
        set_clause = ", ".join(set_clauses)
        
        query = f"""
            MATCH (r:GuardrailRule {{name: $name}})
            SET {set_clause}
        """
        
        # パラメータを準備
        params = {"name": name}
        params.update(update_fields)
        
        conn.execute(query, params)
    
    def execute_guardrail_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ガードレールルールを実行
        
        Args:
            data: ルール実行時に渡すデータ
            
        Returns:
            実行結果を含む辞書
        """
        # RuleExecutorインスタンスを作成して実行
        executor = RuleExecutor(self)
        return executor.execute_rules(data)


class QueryExecutor:
    """動的クエリ実行エンジン"""
    
    def __init__(self, meta_node: MetaNode):
        """
        QueryExecutorを初期化
        
        Args:
            meta_node: MetaNodeインスタンス
        """
        self.meta_node = meta_node
    
    def execute_query(self, query_name: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        保存されたクエリを名前で実行
        
        Args:
            query_name: 実行するクエリの名前
            parameters: クエリパラメータ（オプション）
            
        Returns:
            クエリ結果のリスト
            
        Raises:
            QueryNotFoundError: クエリノードが存在しない場合
            CypherSyntaxError: Cypherクエリの構文エラーが発生した場合
        """
        # クエリノードを取得
        try:
            query_node = self.meta_node.get_query_node(query_name)
        except ValueError:
            raise QueryNotFoundError(f"Query node '{query_name}' not found in database")
        
        # クエリを実行
        try:
            conn = kuzu.Connection(self.meta_node.db)
            result = conn.execute(query_node.cypher_query, parameters or {})
        except Exception as e:
            # Cypherクエリの構文エラーの場合
            error_msg = str(e)
            if any(keyword in error_msg.lower() for keyword in ['syntax', 'parse', 'invalid']):
                raise CypherSyntaxError(f"Syntax error in Cypher query '{query_name}': {error_msg}")
            else:
                # その他のエラーはそのまま再発生
                raise
        
        # 結果を辞書のリストに変換
        results = []
        while result.has_next():
            row = result.get_next()
            # 各行を辞書に変換
            row_dict = {}
            for i, col_name in enumerate(result.get_column_names()):
                row_dict[col_name] = row[i]
            results.append(row_dict)
        
        return results


class RuleExecutor:
    """ガードレールルール実行エンジン（Cypherクエリベース）"""
    
    def __init__(self, meta_node: MetaNode):
        """
        RuleExecutorを初期化
        
        Args:
            meta_node: MetaNodeインスタンス
        """
        self.meta_node = meta_node
    
    def execute_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        アクティブなガードレールルールを優先度順に実行
        
        Args:
            data: ルール実行時に渡すデータ
            
        Returns:
            実行結果を含む辞書
                - passed: すべてのルールが成功したかどうか
                - executed_rules: 実行されたルールのリスト
                - logs: 実行中に記録されたログ
                - failed_rules: 失敗したルールのリスト
        """
        # アクティブなルールを優先度順に取得
        rules = self.meta_node.get_guardrail_rules(active_only=True)
        
        result = {
            "passed": True,
            "executed_rules": [],
            "failed_rules": [],
            "logs": []
        }
        
        # ログ記録用の関数（旧形式の互換性のため）
        def log(message: str):
            result["logs"].append(message)
        
        # 各ルールを実行
        for rule in rules:
            try:
                # cypher_queryが指定されている場合は新形式で実行
                if rule.cypher_query and rule.cypher_query.strip():
                    # Cypherクエリを実行してpass/fail判定
                    rule_passed = self._execute_cypher_rule(rule, data, result)
                    
                    if rule_passed:
                        # 実行されたルールを記録
                        result["executed_rules"].append({
                            "name": rule.name,
                            "description": rule.description,
                            "priority": rule.priority,
                            "rule_type": rule.rule_type
                        })
                    else:
                        # 失敗したルールを記録
                        result["failed_rules"].append({
                            "name": rule.name,
                            "description": rule.description,
                            "priority": rule.priority,
                            "rule_type": rule.rule_type
                        })
                        result["passed"] = False
                        
                        # validation タイプのルールが失敗した場合は処理を中断
                        if rule.rule_type == "validation":
                            result["logs"].append(f"Validation rule '{rule.name}' failed. Stopping execution.")
                            break
                # conditionとactionが指定されている場合は旧形式で実行
                elif rule.condition and rule.action:
                    # 実行コンテキストを準備
                    context = {
                        "data": data,
                        "log": log,
                        "pass": True,
                        "ValueError": ValueError,
                        "raise_error": self._raise_exception
                    }
                    
                    # 条件を評価
                    condition_result = eval(rule.condition, {"__builtins__": {}}, context)
                    
                    if condition_result:
                        # アクションを実行
                        eval(rule.action, {"__builtins__": {}}, context)
                        
                        # 実行されたルールを記録
                        result["executed_rules"].append({
                            "name": rule.name,
                            "description": rule.description,
                            "priority": rule.priority
                        })
                else:
                    # どちらも指定されていない場合はスキップ
                    result["logs"].append(f"Rule '{rule.name}' has no cypher_query or condition/action. Skipping.")
                    
            except Exception as e:
                result["passed"] = False
                result["logs"].append(f"Error executing rule '{rule.name}': {str(e)}")
                
                # 失敗したルールを記録
                result["failed_rules"].append({
                    "name": rule.name,
                    "description": rule.description,
                    "priority": rule.priority,
                    "rule_type": rule.rule_type,
                    "error": str(e)
                })
                
                # validation タイプのルールでエラーが発生した場合は処理を中断
                if rule.rule_type == "validation":
                    result["logs"].append(f"Validation rule '{rule.name}' failed with error. Stopping execution.")
                    break
        
        return result
    
    def _execute_cypher_rule(self, rule: GuardrailRule, data: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """
        Cypherクエリベースのルールを実行
        
        Args:
            rule: 実行するルール
            data: ルール実行時のデータ
            result: 実行結果を格納する辞書
            
        Returns:
            ルールが成功した場合True、失敗した場合False
        """
        conn = kuzu.Connection(self.meta_node.db)
        
        try:
            # Cypherクエリを実行
            # まずパラメータ付きで試行し、パラメータが見つからない場合はパラメータなしで再試行
            try:
                query_result = conn.execute(rule.cypher_query, data if data else {})
            except RuntimeError as e:
                if "Parameter" in str(e) and "not found" in str(e):
                    # パラメータが見つからない場合は、パラメータなしで再試行
                    query_result = conn.execute(rule.cypher_query)
                else:
                    raise
            
            # クエリ結果からpass/failを判定
            if query_result.has_next():
                row = query_result.get_next()
                
                # 結果の最初のカラムをブール値として評価
                if len(row) > 0:
                    # 最初のカラムの値を取得
                    first_value = row[0]
                    
                    # 結果がブール値の場合はそのまま使用
                    if isinstance(first_value, bool):
                        rule_passed = first_value
                    # 結果が数値の場合は0以外をTrueとする
                    elif isinstance(first_value, (int, float)):
                        rule_passed = first_value != 0
                    # 結果が文字列の場合
                    elif isinstance(first_value, str):
                        rule_passed = first_value.lower() in ['true', 'pass', 'ok', 'yes', '1']
                    # その他の場合はTrueとする（結果が存在する）
                    else:
                        rule_passed = True
                        
                    # ログメッセージがある場合は記録（2番目のカラム）
                    if len(row) > 1 and row[1] is not None:
                        result["logs"].append(f"[{rule.name}] {row[1]}")
                        
                    return rule_passed
                else:
                    # 結果が空の場合は失敗とする
                    return False
            else:
                # 結果が返されない場合は失敗とする
                return False
                
        except Exception as e:
            # クエリ実行エラー
            result["logs"].append(f"Error executing Cypher query for rule '{rule.name}': {str(e)}")
            # エラーを再raiseして呼び出し元でキャッチさせる
            raise
    
    def _raise_exception(self, exception):
        """例外を発生させるヘルパー関数（旧形式の互換性のため）"""
        raise exception