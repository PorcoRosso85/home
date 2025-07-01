"""
階層処理用UDF - KuzuDBでの階層自動処理
依存: なし
外部依存: kuzu
"""
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from .variables.constants import DEFAULT_HIERARCHY_KEYWORDS, MAX_HIERARCHY_DEPTH
from .variables import get_hierarchy_mode, get_max_hierarchy, get_team, get_hierarchy_keywords


@dataclass(frozen=True)
class HierarchyConfig:
    """階層設定を管理するデータクラス"""
    mode: str = "legacy"
    max_depth: int = MAX_HIERARCHY_DEPTH
    team: str = "product"
    keywords: Dict[int, list[str]] = field(default_factory=lambda: DEFAULT_HIERARCHY_KEYWORDS)
    
    @classmethod
    def from_env(cls) -> "HierarchyConfig":
        """環境変数から設定を読み込む
        
        Returns:
            HierarchyConfig: 環境変数から生成した設定
            
        Raises:
            ValueError: 環境変数の値が不正な場合
        """
        try:
            # 階層キーワード定義
            keywords = get_hierarchy_keywords()
            if keywords is None:
                keywords = DEFAULT_HIERARCHY_KEYWORDS
            
            return cls(
                mode=get_hierarchy_mode(),
                max_depth=get_max_hierarchy(),
                team=get_team(),
                keywords=keywords
            )
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"環境変数の解析エラー: {e}")


# グローバル設定インスタンス（関数内で参照）
_config: Optional[HierarchyConfig] = None


def _get_config() -> HierarchyConfig:
    """設定を取得（遅延初期化）"""
    global _config
    if _config is None:
        _config = HierarchyConfig.from_env()
    return _config


def reset_config() -> None:
    """設定をリセット（テスト用）"""
    global _config
    _config = None


def register_hierarchy_udfs(connection: Any) -> None:
    """階層処理用のUDFを登録
    
    Args:
        connection: KuzuDB接続オブジェクト
        
    使用例:
        >>> conn = kuzu.Connection(db)
        >>> register_hierarchy_udfs(conn)
        >>> result = conn.execute("RETURN infer_hierarchy_level('システムビジョン', '')")
        >>> assert result.get_next()[0] == 0  # ビジョンレベル
    """
    
    # 設定をリセット（環境変数が変更された場合に備えて）
    reset_config()
    
    # 1. 階層レベル推論
    def infer_hierarchy_level(title: str, description: str = "") -> int:
        """タイトルから階層レベルを推論
        
        Args:
            title: 要件タイトル
            description: 要件説明（オプション）
            
        Returns:
            階層レベル（0-4）
            
        Example:
            >>> infer_hierarchy_level("システムビジョン")
            0
            >>> infer_hierarchy_level("認証機能")
            2
        """
        if not title:
            return 4  # デフォルト: タスク
            
        text = f"{title} {description}".lower()
        config = _get_config()
        
        # キーワードマッチング
        for level, keywords in config.keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return level
        
        return 4  # デフォルト: タスク
    
    # 2. 動的URI生成
    def generate_hierarchy_uri(req_id: str, level: int) -> str:
        """階層を考慮したURI生成
        
        Args:
            req_id: 要件ID
            level: 階層レベル（0-4）
            
        Returns:
            階層URI（例: "req://L1/req_001" または "req://req_001"）
            
        Raises:
            ValueError: req_idが空の場合
            
        Example:
            >>> generate_hierarchy_uri("req_001", 2)
            'req://L2/req_001'  # legacy mode
        """
        if not req_id:
            raise ValueError("要件IDは必須です")
            
        config = _get_config()
        
        if config.mode == "dynamic":
            # 新形式：レベル情報なし
            return f"req://{req_id}"
        else:
            # 従来形式：L0/L1形式
            if level < 0 or level >= config.max_depth:
                level = min(max(level, 0), config.max_depth - 1)
            return f"req://L{level}/{req_id}"
    
    # 3. 階層検証
    def is_valid_hierarchy(parent_level: int, child_level: int) -> bool:
        """階層関係の妥当性を検証
        
        Args:
            parent_level: 親の階層レベル（0以上）
            child_level: 子の階層レベル（0以上）
            
        Returns:
            子が親より下位の階層の場合True
            
        Example:
            >>> is_valid_hierarchy(0, 1)  # ビジョン -> エピック
            True
            >>> is_valid_hierarchy(3, 1)  # ストーリー -> エピック
            False
        """
        # 負の値は不正
        if parent_level < 0 or child_level < 0:
            return False
            
        # 子は親より下位（大きい値）である必要がある
        return child_level > parent_level
    
    # 4. 最大階層深度
    def get_max_hierarchy_depth() -> int:
        """環境変数から最大階層深度を取得
        
        Returns:
            最大階層深度（デフォルト: 5）
            
        Example:
            >>> os.environ["RGL_MAX_HIERARCHY"] = "6"
            >>> get_max_hierarchy_depth()
            6
        """
        config = _get_config()
        return config.max_depth
    
    # UDFを登録（既に存在する場合はスキップ）
    functions_to_register = [
        ("infer_hierarchy_level", infer_hierarchy_level),
        ("generate_hierarchy_uri", generate_hierarchy_uri),
        ("is_valid_hierarchy", is_valid_hierarchy),
        ("get_max_hierarchy_depth", get_max_hierarchy_depth)
    ]
    
    for func_name, func in functions_to_register:
        try:
            connection.create_function(func_name, func)
        except RuntimeError as e:
            if "already exists" in str(e):
                # 既に存在する場合はスキップ（テスト環境での再登録時）
                pass
            else:
                raise
