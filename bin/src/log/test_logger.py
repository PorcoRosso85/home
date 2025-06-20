#!/usr/bin/env python3
# Python版ロガーのテストと使用例
# CONVENTION.yaml準拠：最小構成

import os
import sys

# パスを追加（テスト実行用）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ロガーインポート
from log import (
    # メイン関数
    log, parse, format, validate, create,
    # レイヤー別ログ
    presentation_log, application_log, domain_log, infrastructure_log
)

def test_basic_logging():
    """基本的なログ出力テスト"""
    print("=== 基本ログ出力テスト ===")
    
    # 環境変数設定
    os.environ['LOG_CONFIG'] = '*:INFO'
    
    # 各レベルでログ出力
    log('TRACE', 'test', "このメッセージは表示されません（TRACE < INFO）")
    log('DEBUG', 'test', "このメッセージも表示されません（DEBUG < INFO）")
    log('INFO', 'test', "情報メッセージ")
    log('WARN', 'test', "警告メッセージ")
    log('ERROR', 'test', "エラーメッセージ")
    log('FATAL', 'test', "致命的エラーメッセージ")
    
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
    
    log('INFO', 'test', "JSON形式のログ", user_id=123, action='login')
    log('ERROR', 'test', "エラー情報", error_code='DB_CONNECTION_FAILED', retry_count=3)
    
    # フォーマットを戻す
    os.environ['LOG_FORMAT'] = 'console'
    print()

def test_hierarchical_config():
    """階層的設定テスト"""
    print("=== 階層的設定テスト ===")
    
    # app.* はDEBUG、app.service.* はTRACE
    os.environ['LOG_CONFIG'] = '*:WARN,app:DEBUG,app.service:TRACE'
    
    # カスタムロガー作成
    app_log = create('app')
    app_controller_log = create('app.controller')
    app_service_log = create('app.service')
    app_service_user_log = create('app.service.user')
    
    # ログ出力
    app_log['debug']("アプリケーションデバッグ")  # 表示される
    app_controller_log['debug']("コントローラーデバッグ")  # 表示される（親のapp:DEBUGを継承）
    app_service_log['trace']("サービストレース")  # 表示される
    app_service_user_log['trace']("ユーザーサービストレース")  # 表示される（親を継承）
    
    print()

def test_config_validation():
    """設定検証テスト"""
    print("=== 設定検証テスト ===")
    
    # 正しい設定
    is_valid, errors = validate("*:INFO,domain:DEBUG")
    print(f"正しい設定: {is_valid}, エラー: {errors}")
    
    # 不正な設定
    is_valid, errors = validate("app:INVALID")
    print(f"不正な設定: {is_valid}, エラー: {errors}")
    
    print()

def main():
    """メインテスト実行"""
    print("Python版ロガーテスト開始\n")
    
    # 各種テスト実行
    test_basic_logging()
    test_layer_logging()
    test_json_format()
    test_hierarchical_config()
    test_config_validation()
    
    print("テスト完了")

if __name__ == '__main__':
    main()