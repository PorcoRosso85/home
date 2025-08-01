#!/usr/bin/env python3
"""
Vessel用の簡易構造化ログシステム
規約準拠のため、print()を使わずにJSON形式でログ出力
"""
import json
import sys
import os
from datetime import datetime
from typing import Any, Dict, Optional

class VesselLogger:
    """Vessel用の構造化ログ出力"""
    
    def __init__(self, vessel_type: str = "vessel"):
        self.vessel_type = vessel_type
        self.debug_mode = os.environ.get('VESSEL_DEBUG', '').lower() in ('1', 'true', 'yes')
    
    def _format_log(self, level: str, message: str, **kwargs) -> str:
        """ログエントリをJSON形式でフォーマット"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "vessel_type": self.vessel_type,
            "message": message,
            **kwargs
        }
        return json.dumps(log_entry, ensure_ascii=False)
    
    def debug(self, message: str, **kwargs):
        """デバッグログ（VESSEL_DEBUG環境変数が設定されている場合のみ）"""
        if self.debug_mode:
            sys.stderr.write(self._format_log("debug", message, **kwargs) + "\n")
            sys.stderr.flush()
    
    def info(self, message: str, **kwargs):
        """情報ログ"""
        sys.stderr.write(self._format_log("info", message, **kwargs) + "\n")
        sys.stderr.flush()
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """エラーログ"""
        if error:
            kwargs['error'] = str(error)
            kwargs['error_type'] = type(error).__name__
        
        sys.stderr.write(self._format_log("error", message, **kwargs) + "\n")
        sys.stderr.flush()
    
    def output(self, data: Any):
        """標準出力への出力（これはログではない）"""
        # 通常の出力はそのまま標準出力へ
        if isinstance(data, str):
            sys.stdout.write(data)
            if not data.endswith('\n'):
                sys.stdout.write('\n')
        else:
            sys.stdout.write(str(data) + '\n')
        sys.stdout.flush()

# グローバルインスタンス
logger = VesselLogger()