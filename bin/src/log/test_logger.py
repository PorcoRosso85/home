#!/usr/bin/env python3
# Python版ロガーのテストと使用例
# CONVENTION.yaml準拠：最小構成

import os
import sys

# パスを追加（テスト実行用）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ロガーインポート
from log import (
    # グローバル関数
    trace, debug, info, warn, error, fatal,
    # レイヤー別ログ
    presentation_log, application_log, domain_log, infrastructure_log,
    # ユーティリティ
    create_logger, get_current_config
)

def test_basic_logging():
    """基本的なログ出力テスト"""
    print("=== 基本ログ出力テスト ===")
    
    # 環境変数設定
    os.environ['LOG_CONFIG'] = '*:INFO'
    
    # 各レベルでログ出力
    trace("このメッセージは表示されません（TRACE < INFO）")
    debug("このメッセージも表示されません（DEBUG < INFO）")
    info("情報メッセージ")
    warn("警告メッセージ")
    error("エラーメッセージ")
    fatal("致命的エラーメッセージ")
    
    print()

def test_layer_logging():
    """レイヤー別ログテスト"""
    print("=== レイヤー別ログテスト ===")
    
    # レイヤー別設定
    os.environ['LOG_CONFIG'] = 'presentation:DEBUG,application:TRACE,domain:INFO,-infrastructure'
    
    # 各レイヤーでログ出力
    presentation_log['debug']("画面表示処理", view='UserList')
    presentation_log['info']("リクエスト受信", method='GET', path='/users')
    
    application_log['trace']("詳細トレース情報", data={'id': 1, 'name': 'test'})
    application_log['debug']("ユースケース実行", usecase='GetUsers')
    
    domain_log['info']("ビジネスルール適用", rule='UserValidation')
    domain_log['warn']("非推奨メソッド使用", method='oldValidate')
    
    # インフラ層は除外されているので表示されない
    infrastructure_log['error']("このメッセージは表示されません（除外）")
    
    print()

def test_json_format():
    """JSON形式出力テスト"""
    print("=== JSON形式出力テスト ===")
    
    os.environ['LOG_CONFIG'] = '*:INFO'
    os.environ['LOG_FORMAT'] = 'json'
    
    info("JSON形式のログ", user_id=123, action='login')
    error("エラー情報", error_code='DB_CONNECTION_FAILED', retry_count=3)
    
    # フォーマットを戻す
    os.environ['LOG_FORMAT'] = 'console'
    print()

def test_hierarchical_config():
    """階層的設定テスト"""
    print("=== 階層的設定テスト ===")
    
    # app.* はDEBUG、app.service.* はTRACE
    os.environ['LOG_CONFIG'] = '*:WARN,app:DEBUG,app.service:TRACE'
    
    # カスタムロガー作成
    app_log = create_logger('app')
    app_controller_log = create_logger('app.controller')
    app_service_log = create_logger('app.service')
    app_service_user_log = create_logger('app.service.user')
    
    # ログ出力
    app_log['debug']("アプリケーションデバッグ")  # 表示される
    app_controller_log['debug']("コントローラーデバッグ")  # 表示される（親のapp:DEBUGを継承）
    app_service_log['trace']("サービストレース")  # 表示される
    app_service_user_log['trace']("ユーザーサービストレース")  # 表示される（親を継承）
    
    print()

def test_config_info():
    """設定情報表示"""
    print("=== 現在の設定情報 ===")
    
    config = get_current_config()
    print(f"LOG_CONFIG: {config['raw_config']}")
    print(f"LOG_FORMAT: {config['format']}")
    print(f"パース済み設定:")
    for key, value in config['parsed_config'].items():
        if value:
            print(f"  {key}: {value}")
    
    print()

def main():
    """メインテスト実行"""
    print("Python版ロガーテスト開始\n")
    
    # 各種テスト実行
    test_basic_logging()
    test_layer_logging()
    test_json_format()
    test_hierarchical_config()
    test_config_info()
    
    print("テスト完了")

if __name__ == '__main__':
    main()