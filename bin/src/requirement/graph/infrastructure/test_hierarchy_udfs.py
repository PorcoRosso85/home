"""階層処理用UDFのテスト"""

import os
import json
import pytest
from .hierarchy_udfs import (
    HierarchyConfig, 
    register_hierarchy_udfs, 
    reset_config,
    _get_config
)
from .variables.constants import DEFAULT_HIERARCHY_KEYWORDS
from .variables import with_test_env, restore_env


class TestHierarchyConfig:
    """HierarchyConfigのテスト"""
    
    def test_from_env_デフォルト値なし(self):
        """from_env_環境変数未設定_Noneが返される（conventionに従う）"""
        # Arrange - 環境変数をクリア
        original_env = {}
        for key in ["RGL_HIERARCHY_MODE", "RGL_MAX_HIERARCHY", "RGL_TEAM", "RGL_HIERARCHY_KEYWORDS"]:
            original_env[key] = os.environ.pop(key, None)
        
        # Act
        config = HierarchyConfig.from_env()
        
        # Assert - conventionに従いデフォルト値を期待（データクラスのデフォルト）
        assert config.mode == "legacy"  # データクラスのデフォルト
        assert config.max_depth == 5  # MAX_HIERARCHY_DEPTH
        assert config.team == "product"  # データクラスのデフォルト
        assert config.keywords == DEFAULT_HIERARCHY_KEYWORDS  # データクラスのデフォルト
        
        # Cleanup
        restore_env(original_env)
    
    def test_from_env_カスタム値(self):
        """from_env_環境変数設定_カスタム値が使用される"""
        # 直接HierarchyConfigを作成してテスト
        config = HierarchyConfig(
            mode="dynamic",
            max_depth=6,
            team="engineering",
            keywords={0: ["vision", "goal"], 1: ["epic"]}
        )
        
        # Assert
        assert config.mode == "dynamic"
        assert config.max_depth == 6
        assert config.team == "engineering"
        assert config.keywords[0] == ["vision", "goal"]
        assert config.keywords[1] == ["epic"]
    
    def test_from_env_不正なJSON(self):
        """from_env_不正なJSON_エラーが発生"""
        # Arrange
        original = with_test_env(RGL_HIERARCHY_KEYWORDS="invalid json")
        
        try:
            # Act & Assert - 不正なJSONの場合はエラーが発生する
            with pytest.raises(Exception) as exc_info:
                config = HierarchyConfig.from_env()
            
            assert "RGL_HIERARCHY_KEYWORDS must be valid JSON" in str(exc_info.value)
        finally:
            # Cleanup
            restore_env(original)


class TestHierarchyUDFs:
    """階層UDFのテスト"""
    
    def setup_method(self):
        """各テストの前に実行"""
        reset_config()
        # 環境変数をクリア
        for key in ["RGL_HIERARCHY_MODE", "RGL_MAX_HIERARCHY", "RGL_TEAM", "RGL_HIERARCHY_KEYWORDS"]:
            os.environ.pop(key, None)
    
    def test_hierarchy_udfs_登録_正常に動作(self):
        """階層UDF登録_全関数が利用可能"""
        # デフォルトキーワードを環境変数として設定
        os.environ["RGL_HIERARCHY_KEYWORDS"] = json.dumps({
            "0": ["ビジョン", "vision", "戦略", "目標"],
            "1": ["エピック", "epic", "大規模", "イニシアチブ"],
            "2": ["フィーチャー", "feature", "機能", "capability"],
            "3": ["ストーリー", "story", "ユーザーストーリー"],
            "4": ["タスク", "task", "実装", "バグ"]
        })
        
        # In-memoryデータベース
        from .database_factory import create_database, create_connection
        db = create_database(in_memory=True)
        conn = create_connection(db)
        
        # UDF登録
        register_hierarchy_udfs(conn)
        
        # 各UDFの動作確認
        result = conn.execute("RETURN infer_hierarchy_level('ビジョン', '')")
        assert result.get_next()[0] == 0
        
        result = conn.execute("RETURN generate_hierarchy_uri('req_001', 2)")
        assert result.get_next()[0] == "req://L2/req_001"
        
        result = conn.execute("RETURN is_valid_hierarchy(0, 1)")
        assert result.get_next()[0] == True
        
        result = conn.execute("RETURN get_max_hierarchy_depth()")
        assert result.get_next()[0] == 5
    
    def test_環境変数_動的モード_URI形式変更(self):
        """環境変数設定_dynamic mode_レベル情報なし"""
        from .database_factory import create_database, create_connection
        
        # 環境変数設定
        os.environ["RGL_HIERARCHY_MODE"] = "dynamic"
        
        db = create_database(in_memory=True)
        conn = create_connection(db)
        register_hierarchy_udfs(conn)
        
        result = conn.execute("RETURN generate_hierarchy_uri('req_001', 2)")
        assert result.get_next()[0] == "req://req_001"
        
        # 元に戻す
        os.environ["RGL_HIERARCHY_MODE"] = "legacy"
    
    def test_infer_hierarchy_level_各レベル判定(self):
        """infer_hierarchy_level_各キーワード_正しいレベルを返す"""
        from .database_factory import create_database, create_connection
        
        # デフォルトキーワードを環境変数として設定
        os.environ["RGL_HIERARCHY_KEYWORDS"] = json.dumps({
            "0": ["ビジョン", "vision", "戦略", "目標"],
            "1": ["エピック", "epic", "大規模", "イニシアチブ"],
            "2": ["フィーチャー", "feature", "機能", "capability"],
            "3": ["ストーリー", "story", "ユーザーストーリー"],
            "4": ["タスク", "task", "実装", "バグ"]
        })
        
        db = create_database(in_memory=True)
        conn = create_connection(db)
        register_hierarchy_udfs(conn)
        
        # レベル0: ビジョン
        result = conn.execute("RETURN infer_hierarchy_level('システムビジョン', '')")
        assert result.get_next()[0] == 0
        
        # レベル1: エピック
        result = conn.execute("RETURN infer_hierarchy_level('認証エピック', '')")
        assert result.get_next()[0] == 1
        
        # レベル2: フィーチャー
        result = conn.execute("RETURN infer_hierarchy_level('ログイン機能', '')")
        assert result.get_next()[0] == 2
        
        # レベル3: ストーリー
        result = conn.execute("RETURN infer_hierarchy_level('ユーザーストーリー', '')")
        assert result.get_next()[0] == 3
        
        # レベル4: タスク（デフォルト）
        result = conn.execute("RETURN infer_hierarchy_level('その他の要件', '')")
        assert result.get_next()[0] == 4
    
    def test_is_valid_hierarchy_境界値(self):
        """is_valid_hierarchy_境界値_正しく判定"""
        from .database_factory import create_database, create_connection
        
        db = create_database(in_memory=True)
        conn = create_connection(db)
        register_hierarchy_udfs(conn)
        
        # 正常な階層関係
        result = conn.execute("RETURN is_valid_hierarchy(0, 1)")
        assert result.get_next()[0] == True
        
        # 同じレベル
        result = conn.execute("RETURN is_valid_hierarchy(2, 2)")
        assert result.get_next()[0] == False
        
        # 逆転した階層
        result = conn.execute("RETURN is_valid_hierarchy(3, 1)")
        assert result.get_next()[0] == False
        
        # 負の値
        result = conn.execute("RETURN is_valid_hierarchy(-1, 2)")
        assert result.get_next()[0] == False
    
    def test_generate_hierarchy_uri_エラーケース(self):
        """generate_hierarchy_uri_空のreq_id_エラー"""
        from .database_factory import create_database, create_connection
        
        db = create_database(in_memory=True)
        conn = create_connection(db)
        register_hierarchy_udfs(conn)
        
        # 空のreq_idでエラーが発生することを確認
        with pytest.raises(Exception):
            conn.execute("RETURN generate_hierarchy_uri('', 2)")
    
    def test_max_hierarchy_depth_環境変数(self):
        """get_max_hierarchy_depth_環境変数設定_値が反映される"""
        from .database_factory import create_database, create_connection
        
        # 環境変数設定
        os.environ["RGL_MAX_HIERARCHY"] = "8"
        
        db = create_database(in_memory=True)
        conn = create_connection(db)
        register_hierarchy_udfs(conn)
        
        result = conn.execute("RETURN get_max_hierarchy_depth()")
        assert result.get_next()[0] == 8
        
        # 元に戻す
        os.environ.pop("RGL_MAX_HIERARCHY", None)