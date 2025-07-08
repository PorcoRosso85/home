"""
Unified Query Interface - Cypherとカスタムプロシージャの統合インターフェース
依存: cypher_executor, custom_procedures, query_validator
外部依存: なし
"""
from typing import Dict, List, Any, Optional, Union, Callable
import re


class UnifiedQueryInterface:
    """
    Cypherクエリとカスタムプロシージャを統合的に扱うインターフェース
    LLMが自然にクエリを記述できるようにする
    """
    
    def __init__(self, cypher_executor, custom_procedures, query_validator):
        self.cypher = cypher_executor
        self.procedures = custom_procedures
        self.validator = query_validator
        
        # クエリタイプのパターン
        self.patterns = {
            "procedure_call": re.compile(r"CALL\s+(\w+\.\w+)\s*\((.*?)\)", re.IGNORECASE),
            "with_procedure": re.compile(r"WITH.*?CALL\s+(\w+\.\w+)", re.IGNORECASE),
            "return_procedure": re.compile(r"RETURN\s+(\w+\.\w+)\s*\(", re.IGNORECASE)
        }
    
    def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        統合クエリ実行
        
        Args:
            query: Cypherクエリ（プロシージャ呼び出しを含む可能性あり）
            parameters: クエリパラメータ
            options: 実行オプション（timeout, explain等）
            
        Returns:
            実行結果
        """
        parameters = parameters or {}
        options = options or {}
        
        # クエリタイプを判定
        query_type = self._detect_query_type(query)
        
        if query_type == "pure_cypher":
            # 純粋なCypherクエリ
            return self._execute_pure_cypher(query, parameters, options)
        elif query_type == "procedure_only":
            # プロシージャ呼び出しのみ
            return self._execute_procedure_only(query, parameters)
        else:
            # 混合クエリ（Cypher + プロシージャ）
            return self._execute_mixed_query(query, parameters, options)
    
    def _detect_query_type(self, query: str) -> str:
        """クエリタイプを検出"""
        has_call = bool(self.patterns["procedure_call"].search(query))
        has_match = "MATCH" in query.upper()
        has_create = "CREATE" in query.upper()
        
        if has_call and not (has_match or has_create):
            return "procedure_only"
        elif has_call:
            return "mixed"
        else:
            return "pure_cypher"
    
    def _execute_pure_cypher(
        self,
        query: str,
        parameters: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """純粋なCypherクエリを実行"""
        # バリデーション
        is_valid, error_msg = self.validator.validate(query)
        if not is_valid:
            return {
                "status": "error",
                "error": f"Query validation failed: {error_msg}",
                "query": query
            }
        
        # パラメータサニタイズ
        clean_params = self.validator.sanitize_parameters(parameters)
        
        # 実行
        result = self.cypher.execute(query, clean_params)
        
        if "error" in result:
            return {
                "status": "error",
                "error": result["error"]["message"],
                "error_type": result["error"]["type"],
                "query": query
            }
        
        return {
            "status": "success",
            "data": result.get("data", []),
            "metadata": {
                "row_count": result.get("row_count", 0),
                "columns": result.get("columns", []),
                "query_type": "cypher"
            }
        }
    
    def _execute_procedure_only(
        self,
        query: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """プロシージャ呼び出しのみを実行"""
        # CALL文をパース
        match = self.patterns["procedure_call"].search(query)
        if not match:
            return {
                "status": "error",
                "error": "Invalid procedure call syntax"
            }
        
        proc_name = match.group(1)
        args_str = match.group(2)
        
        # 引数をパース
        args = self._parse_procedure_args(args_str, parameters)
        
        # プロシージャを実行
        if proc_name not in self.procedures.procedures:
            return {
                "status": "error",
                "error": f"Unknown procedure: {proc_name}",
                "available_procedures": list(self.procedures.procedures.keys())
            }
        
        try:
            proc_func = self.procedures.procedures[proc_name]
            results = proc_func(*args)
            
            return {
                "status": "success",
                "data": results,
                "metadata": {
                    "procedure": proc_name,
                    "args": args,
                    "query_type": "procedure"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "procedure": proc_name
            }
    
    def _execute_mixed_query(
        self,
        query: str,
        parameters: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cypherとプロシージャの混合クエリを実行"""
        # 混合クエリを分解
        segments = self._split_mixed_query(query)
        
        results = []
        final_data = []
        
        for segment in segments:
            if segment["type"] == "cypher":
                # Cypherセグメントを実行
                result = self._execute_pure_cypher(
                    segment["query"],
                    parameters,
                    options
                )
                if result["status"] == "error":
                    return result
                
                # 結果を次のセグメントのパラメータとして使用
                if result["data"]:
                    # 最後の結果を次のパラメータに追加
                    parameters["_previous_result"] = result["data"]
                    final_data = result["data"]
                    
            elif segment["type"] == "procedure":
                # プロシージャセグメントを実行
                # 前の結果を引数として使用
                if "_previous_result" in parameters:
                    # プロシージャ引数に前の結果を組み込む
                    proc_args = self._merge_with_previous_result(
                        segment["args"],
                        parameters["_previous_result"]
                    )
                else:
                    proc_args = segment["args"]
                
                try:
                    proc_func = self.procedures.procedures[segment["name"]]
                    proc_results = proc_func(*proc_args)
                    
                    # プロシージャ結果を統合
                    if isinstance(proc_results, list):
                        final_data.extend(proc_results)
                    else:
                        final_data.append(proc_results)
                        
                except Exception as e:
                    return {
                        "status": "error",
                        "error": str(e),
                        "procedure": segment["name"]
                    }
        
        return {
            "status": "success",
            "data": final_data,
            "metadata": {
                "query_type": "mixed",
                "segments": len(segments)
            }
        }
    
    def _parse_procedure_args(
        self,
        args_str: str,
        parameters: Dict[str, Any]
    ) -> List[Any]:
        """プロシージャ引数をパース"""
        if not args_str.strip():
            return []
        
        args = []
        # 簡易パーサー（カンマ区切り）
        parts = args_str.split(",")
        
        for part in parts:
            part = part.strip()
            
            # パラメータ参照（$param）
            if part.startswith("$"):
                param_name = part[1:]
                if param_name in parameters:
                    args.append(parameters[param_name])
                else:
                    args.append(None)
            # 文字列リテラル
            elif part.startswith(("'", '"')):
                args.append(part.strip("'\""))
            # 数値
            elif part.replace(".", "").isdigit():
                if "." in part:
                    args.append(float(part))
                else:
                    args.append(int(part))
            # ブール値
            elif part.lower() in ["true", "false"]:
                args.append(part.lower() == "true")
            else:
                # その他は文字列として扱う
                args.append(part)
        
        return args
    
    def _split_mixed_query(self, query: str) -> List[Dict[str, Any]]:
        """混合クエリをセグメントに分割"""
        segments = []
        
        # 簡易的な分割（CALLの位置で分割）
        # 実際の実装では、より高度なパーサーが必要
        call_pattern = re.compile(r"(.*?)(CALL\s+\w+\.\w+\s*\([^)]*\))(.*)", re.IGNORECASE | re.DOTALL)
        
        remaining = query
        while remaining:
            match = call_pattern.match(remaining)
            if match:
                # Cypherパート
                cypher_part = match.group(1).strip()
                if cypher_part:
                    segments.append({
                        "type": "cypher",
                        "query": cypher_part
                    })
                
                # プロシージャパート
                proc_match = self.patterns["procedure_call"].search(match.group(2))
                if proc_match:
                    segments.append({
                        "type": "procedure",
                        "name": proc_match.group(1),
                        "args": self._parse_procedure_args(proc_match.group(2), {})
                    })
                
                remaining = match.group(3).strip()
            else:
                # 残りはCypherとして扱う
                if remaining.strip():
                    segments.append({
                        "type": "cypher",
                        "query": remaining
                    })
                break
        
        return segments
    
    def _merge_with_previous_result(
        self,
        args: List[Any],
        previous_result: List[Dict]
    ) -> List[Any]:
        """前の結果を引数にマージ"""
        # 簡易実装: 最初の結果のIDを最初の引数として使用
        if previous_result and isinstance(previous_result[0], dict):
            if "id" in previous_result[0]:
                if args:
                    args[0] = previous_result[0]["id"]
                else:
                    args = [previous_result[0]["id"]]
        
        return args
    
    def explain(self, query: str) -> Dict[str, Any]:
        """クエリの実行計画を説明"""
        query_type = self._detect_query_type(query)
        
        explanation = {
            "query_type": query_type,
            "steps": []
        }
        
        if query_type == "pure_cypher":
            explanation["steps"].append({
                "step": 1,
                "type": "cypher_execution",
                "description": "Execute Cypher query through graph database"
            })
        elif query_type == "procedure_only":
            match = self.patterns["procedure_call"].search(query)
            if match:
                explanation["steps"].append({
                    "step": 1,
                    "type": "procedure_call",
                    "procedure": match.group(1),
                    "description": f"Call custom procedure {match.group(1)}"
                })
        else:
            segments = self._split_mixed_query(query)
            for i, segment in enumerate(segments):
                if segment["type"] == "cypher":
                    explanation["steps"].append({
                        "step": i + 1,
                        "type": "cypher_execution",
                        "description": "Execute Cypher segment"
                    })
                else:
                    explanation["steps"].append({
                        "step": i + 1,
                        "type": "procedure_call",
                        "procedure": segment["name"],
                        "description": f"Call procedure {segment['name']}"
                    })
        
        return explanation
