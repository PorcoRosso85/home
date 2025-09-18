"""
ProjectSessionManager機能のテスト - TDD REDフェーズ
Session Architecture 2機能分離のStep 2: プロジェクト分離Session

機能2: プロジェクト実行Session（Designer ↔ Developer通信）
- プロジェクト別独立session環境
- クロスsession通信によるタスク分離
- スケーラブルな並列プロジェクト実行
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, call
import subprocess
from typing import Dict, Any

from application import (
    generate_project_session_name,
    ensure_project_session, 
    send_to_developer_session,
    get_project_session_status
)


class TestProjectSessionManager:
    """プロジェクト専用session管理のテスト群"""

    def test_generate_project_session_name(self):
        """プロジェクトsession名生成のテスト"""
        # REQUIREMENTS.md Line 32: プロジェクト専用session生成: `dev-project-{name}`
        # REQUIREMENTS.md Line 64: return f"dev-project-{Path(project_path).name}"
        
        # テスト1: 基本的なプロジェクトパス
        project_path = "/home/nixos/bin/src/poc/email"
        expected = "dev-project-email"
        result = generate_project_session_name(project_path)
        assert result == expected, f"Expected {expected}, got {result}"
        
        # テスト2: 深いパス構造
        project_path = "/home/nixos/bin/src/develop/org/subproject"
        expected = "dev-project-subproject"  
        result = generate_project_session_name(project_path)
        assert result == expected, f"Expected {expected}, got {result}"
        
        # テスト3: ルートディレクトリ
        project_path = "/project"
        expected = "dev-project-project"
        result = generate_project_session_name(project_path)
        assert result == expected, f"Expected {expected}, got {result}"

    @patch('subprocess.run')
    def test_ensure_project_session_new_session(self, mock_run):
        """新規プロジェクトsession作成のテスト"""
        # REQUIREMENTS.md Line 34: session lifecycle管理（作成・接続・廃棄）
        # REQUIREMENTS.md Line 72-74: Session lifecycle - 存在確認・作成
        
        project_path = "/home/nixos/bin/src/poc/email"
        expected_session = "dev-project-email"
        
        # session存在確認が失敗（session未存在）
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, 'tmux has-session'),  # session not found
            Mock(returncode=0)  # new-session success
        ]
        
        result = ensure_project_session(project_path)
        
        # session名を返す
        assert result == expected_session
        
        # tmux has-sessionで存在確認
        mock_run.assert_any_call(
            ['tmux', 'has-session', '-t', expected_session],
            capture_output=True,
            text=True
        )
        
        # tmux new-sessionで作成
        mock_run.assert_any_call(
            ['tmux', 'new-session', '-d', '-s', expected_session, '-c', project_path],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_ensure_project_session_existing_session(self, mock_run):
        """既存プロジェクトsession確保のテスト"""
        # REQUIREMENTS.md Line 72-74: 存在確認・作成
        
        project_path = "/home/nixos/bin/src/poc/email"  
        expected_session = "dev-project-email"
        
        # session存在確認が成功（session既存）
        mock_run.return_value = Mock(returncode=0)
        
        result = ensure_project_session(project_path)
        
        # session名を返す
        assert result == expected_session
        
        # tmux has-sessionのみ実行（new-sessionは実行されない）
        mock_run.assert_called_once_with(
            ['tmux', 'has-session', '-t', expected_session],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_send_to_developer_session(self, mock_run):
        """Cross-session通信のテスト"""
        # REQUIREMENTS.md Line 33: Cross-session通信による完全分離
        # REQUIREMENTS.md Line 67-68: tmux send-keys -t session:window
        
        project_path = "/home/nixos/bin/src/poc/email"
        message = "echo 'Testing cross-session communication'"
        expected_session = "dev-project-email"
        
        # session存在確認成功
        mock_run.side_effect = [
            Mock(returncode=0),  # has-session success
            Mock(returncode=0)   # send-keys success
        ]
        
        result = send_to_developer_session(project_path, message)
        
        # 成功を示すbool値を返す
        assert result is True
        
        # session存在確認
        mock_run.assert_any_call(
            ['tmux', 'has-session', '-t', expected_session],
            capture_output=True,
            text=True
        )
        
        # Cross-session通信（tmux send-keys）
        mock_run.assert_any_call(
            ['tmux', 'send-keys', '-t', f"{expected_session}:0", message, 'Enter'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_send_to_developer_session_no_session(self, mock_run):
        """存在しないsessionへの通信エラーテスト"""
        # REQUIREMENTS.md Line 93: Cross-session通信の遅延・信頼性問題
        
        project_path = "/home/nixos/bin/src/poc/nonexistent"
        message = "echo 'This should fail'"
        
        # session存在確認失敗
        mock_run.side_effect = subprocess.CalledProcessError(1, 'tmux has-session')
        
        result = send_to_developer_session(project_path, message)
        
        # 失敗を示すbool値を返す
        assert result is False
        
        # send-keysは実行されない（has-sessionでエラー）
        assert len(mock_run.call_args_list) == 1

    @patch('subprocess.run')
    def test_get_project_session_status(self, mock_run):
        """プロジェクトsession状態取得のテスト"""
        # REQUIREMENTS.md Line 40: `get_all_*_status` 統合状態管理継続
        
        project_path = "/home/nixos/bin/src/poc/email"
        expected_session = "dev-project-email"
        
        # tmux list-sessionsの出力をモック
        mock_output = f"{expected_session}: 1 windows (created Sat Sep  6 16:00:00 2025)\n"
        mock_run.return_value = Mock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )
        
        result = get_project_session_status(project_path)
        
        # session情報を含む辞書を返す
        expected_result = {
            'session_name': expected_session,
            'exists': True,
            'windows': 1,
            'created': 'Sat Sep  6 16:00:00 2025'
        }
        assert result == expected_result
        
        # tmux list-sessions実行確認
        mock_run.assert_called_once_with(
            ['tmux', 'list-sessions'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_get_project_session_status_not_found(self, mock_run):
        """存在しないプロジェクトsession状態取得のテスト"""
        project_path = "/home/nixos/bin/src/poc/nonexistent"
        expected_session = "dev-project-nonexistent"
        
        # tmux list-sessionsで他のsessionのみ出力
        mock_output = "other-session: 1 windows (created Sat Sep  6 16:00:00 2025)\n"
        mock_run.return_value = Mock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )
        
        result = get_project_session_status(project_path)
        
        # session不存在を示す辞書を返す
        expected_result = {
            'session_name': expected_session,
            'exists': False,
            'windows': 0,
            'created': None
        }
        assert result == expected_result

    def test_parallel_project_sessions_scalability(self):
        """並列プロジェクト実行のスケーラビリティテスト"""
        # REQUIREMENTS.md Line 35: 並列プロジェクト実行のスケーラビリティ
        
        # 複数プロジェクトの並列session名生成
        projects = [
            "/home/nixos/bin/src/poc/email",
            "/home/nixos/bin/src/poc/graph", 
            "/home/nixos/bin/src/develop/terminal",
            "/home/nixos/bin/src/search/vss-kuzu"
        ]
        
        expected_sessions = [
            "dev-project-email",
            "dev-project-graph",
            "dev-project-terminal", 
            "dev-project-vss-kuzu"
        ]
        
        # 各プロジェクトが独立したsession名を持つ
        for project, expected in zip(projects, expected_sessions):
            result = generate_project_session_name(project)
            assert result == expected, f"Project {project} expected {expected}, got {result}"
        
        # session名の重複がないことを確認
        results = [generate_project_session_name(p) for p in projects]
        assert len(results) == len(set(results)), "Session names must be unique for parallel execution"

    @patch('subprocess.run')
    def test_project_session_lifecycle_complete(self, mock_run):
        """完全なSession lifecycle管理のテスト"""
        # REQUIREMENTS.md Line 34: session lifecycle管理（作成・接続・廃棄）
        
        project_path = "/home/nixos/bin/src/poc/email"
        expected_session = "dev-project-email"
        message = "echo 'Lifecycle test'"
        
        # シーケンス: ensure(create) -> send -> status -> terminate
        mock_run.side_effect = [
            # ensure_project_session (session not exists -> create)
            subprocess.CalledProcessError(1, 'tmux has-session'),  # not exists
            Mock(returncode=0),  # new-session success
            
            # send_to_developer_session  
            Mock(returncode=0),  # has-session success
            Mock(returncode=0),  # send-keys success
            
            # get_project_session_status
            Mock(returncode=0, stdout=f"{expected_session}: 1 windows\n", stderr=""),
            
            # terminate session
            Mock(returncode=0)   # kill-session success
        ]
        
        # 1. Session確保（作成）
        session_name = ensure_project_session(project_path)
        assert session_name == expected_session
        
        # 2. 通信実行
        send_result = send_to_developer_session(project_path, message)
        assert send_result is True
        
        # 3. 状態確認
        status = get_project_session_status(project_path)
        assert status['exists'] is True
        assert status['session_name'] == expected_session
        
        # 4. Session廃棄（テスト用の関数、実装時に追加予定）
        from application import terminate_project_session
        terminate_result = terminate_project_session(project_path)
        assert terminate_result is True
        
        # 全てのtmux操作が正しい順序で実行されることを確認
        assert len(mock_run.call_args_list) == 6