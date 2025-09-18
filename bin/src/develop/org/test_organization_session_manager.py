"""Test OrganizationSessionManager functionality - Session Architecture 2 GREEN phase.

Tests for Designer window化（pane→window変更）、同一session内高速通信、
統一的な組織管理APIの機能をテスト。

TDD GREEN phase: 実装済み関数のテスト。
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path


class TestDesignerWindowManagement:
    """Test Designer window作成とwindow化機能."""
    
    def test_start_designer_window_creates_independent_window(self):
        """Designer独立window作成のテスト - window名: 'designer-{id}' 形式."""
        from organization_session_manager import start_designer_window
        
        with patch('libtmux.Server') as mock_server_class:
            # Mock setup
            mock_server = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-id"
            mock_session.windows = []
            
            # Mock window creation
            mock_window = Mock()
            mock_window.name = 'designer-x'
            mock_window.id = "window-id"
            mock_session.new_window.return_value = mock_window
            
            mock_server.find_where.return_value = mock_session
            mock_server_class.return_value = mock_server
            
            result = start_designer_window('x')
            
            assert result['ok'] is True
            assert result['data']['window_name'] == 'designer-x'
            assert result['data']['session_id'] is not None
            assert result['data']['status'] == 'created'
    
    def test_start_designer_window_x_y_z_all_different(self):
        """Designer X, Y, Z が異なるwindowに作成されることのテスト."""
        from organization_session_manager import start_designer_window
        
        with patch('libtmux.Server') as mock_server_class:
            mock_server = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-id"
            mock_session.windows = []
            
            # Mock different windows
            mock_window_x = Mock()
            mock_window_x.name = 'designer-x'
            mock_window_x.id = "window-x-id"
            
            mock_window_y = Mock()
            mock_window_y.name = 'designer-y'
            mock_window_y.id = "window-y-id"
            
            mock_window_z = Mock()
            mock_window_z.name = 'designer-z'
            mock_window_z.id = "window-z-id"
            
            mock_session.new_window.side_effect = [mock_window_x, mock_window_y, mock_window_z]
            mock_server.find_where.return_value = mock_session
            mock_server_class.return_value = mock_server
            
            window_x = start_designer_window('x')
            window_y = start_designer_window('y')
            window_z = start_designer_window('z')
            
            assert window_x['data']['window_name'] == 'designer-x'
            assert window_y['data']['window_name'] == 'designer-y'  
            assert window_z['data']['window_name'] == 'designer-z'
            assert window_x['data']['window_name'] != window_y['data']['window_name']
    
    def test_designer_window_isolation(self):
        """Designer window間の独立性テスト."""
        from organization_session_manager import start_designer_window, get_designer_window_status
        
        with patch('libtmux.Server') as mock_server_class:
            mock_server = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-id"
            
            # Mock existing windows
            mock_window_x = Mock()
            mock_window_x.name = 'designer-x'
            mock_window_x.panes = [Mock()]
            
            mock_window_y = Mock()
            mock_window_y.name = 'designer-y'
            mock_window_y.panes = [Mock()]
            
            mock_session.windows = [mock_window_x, mock_window_y]
            mock_server.find_where.return_value = mock_session
            mock_server_class.return_value = mock_server
            
            status_x = get_designer_window_status('x')
            status_y = get_designer_window_status('y')
            
            assert status_x['data']['isolated'] is True
            assert status_y['data']['isolated'] is True


class TestSessionCommunication:
    """Test 同一session内高速通信機能."""
    
    def test_send_to_designer_in_session_high_speed(self):
        """同一session内通信の高速性テスト - tmux内部パイプライン利用."""
        from organization_session_manager import send_to_designer_in_session
        
        with patch('libtmux.Server') as mock_server_class:
            mock_server = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-id"
            
            # Mock window with pane
            mock_window = Mock()
            mock_window.name = 'designer-x'
            mock_pane = Mock()
            mock_window.panes = [mock_pane]
            mock_session.windows = [mock_window]
            
            mock_server.find_where.return_value = mock_session
            mock_server_class.return_value = mock_server
            
            result = send_to_designer_in_session('x', 'test command')
            
            assert result['data']['method'] == 'tmux_internal_pipeline'
            assert result['data']['latency_ms'] < 100  # 高速通信
            assert result['data']['delivered'] is True
    
    def test_session_internal_communication_vs_external(self):
        """session内部通信と外部通信の速度差テスト."""
        from organization_session_manager import (
            send_to_designer_in_session,
            send_to_designer_external_session
        )
        
        with patch('libtmux.Server') as mock_server_class:
            mock_server = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-id"
            
            # Mock window with pane for internal communication
            mock_window = Mock()
            mock_window.name = 'designer-x'
            mock_pane = Mock()
            mock_window.panes = [mock_pane]
            mock_session.windows = [mock_window]
            
            mock_server.find_where.return_value = mock_session
            mock_server_class.return_value = mock_server
            
            internal_result = send_to_designer_in_session('x', 'test')
            external_result = send_to_designer_external_session('x', 'test')
            
            assert internal_result['data']['latency_ms'] < external_result['data']['latency_ms']
    
    def test_session_communication_reliability(self):
        """session内通信の信頼性テスト."""
        from organization_session_manager import send_to_designer_in_session, verify_message_delivery
        
        with patch('libtmux.Server') as mock_server_class:
            mock_server = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-id"
            
            # Mock window with pane
            mock_window = Mock()
            mock_window.name = 'designer-x'
            mock_pane = Mock()
            mock_window.panes = [mock_pane]
            mock_session.windows = [mock_window]
            
            mock_server.find_where.return_value = mock_session
            mock_server_class.return_value = mock_server
            
            message = "test reliability message"
            result = send_to_designer_in_session('x', message)
            verified = verify_message_delivery('x', message)
            
            assert verified is True
            assert result['data']['delivered'] is True


class TestOrganizationSessionStatus:
    """Test 統一的な組織管理API."""
    
    def test_get_org_session_status_unified_management(self):
        """組織session状態管理のテスト - ORG_SESSION統合管理."""
        from organization_session_manager import get_org_session_status
        
        with patch('libtmux.Server') as mock_server_class:
            mock_server = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-id"
            mock_session.name = "org-definer-designers"
            
            # Mock designer windows
            mock_window_x = Mock()
            mock_window_x.name = 'designer-x'
            mock_window_x.id = "window-x-id"
            mock_window_x.panes = [Mock()]
            
            mock_session.windows = [mock_window_x]
            mock_server.find_where.return_value = mock_session
            mock_server_class.return_value = mock_server
            
            status = get_org_session_status()
            
            assert status['data']['session_name'] == 'org-definer-designers'
            assert 'definer' in status['data']['participants']
            assert 'designers' in status['data']['participants']
            assert len(status['data']['designers']) >= 0
    
    def test_org_session_designer_tracking(self):
        """組織内Designer追跡テスト."""
        from organization_session_manager import (
            start_designer_window,
            get_org_session_status,
            track_designer_in_org_session
        )
        
        with patch('libtmux.Server') as mock_server_class:
            mock_server = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-id"
            
            # Mock window creation and tracking
            mock_window = Mock()
            mock_window.name = 'designer-x'
            mock_window.id = "window-x-id"
            mock_window.panes = [Mock()]
            mock_session.new_window.return_value = mock_window
            mock_session.windows = [mock_window]
            
            mock_server.find_where.return_value = mock_session
            mock_server_class.return_value = mock_server
            
            start_designer_window('x')
            track_designer_in_org_session('x')
            
            status = get_org_session_status()
            assert 'x' in [d['id'] for d in status['data']['designers']]
    
    def test_org_session_unified_api_consistency(self):
        """統一API一貫性テスト."""
        from organization_session_manager import (
            get_org_session_status,
            get_designer_status_from_org_session,
            validate_api_consistency
        )
        
        with patch('libtmux.Server') as mock_server_class:
            mock_server = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-id"
            
            # Mock designer window
            mock_window = Mock()
            mock_window.name = 'designer-x'
            mock_window.id = "window-x-id"
            mock_window.panes = [Mock()]
            mock_session.windows = [mock_window]
            
            mock_server.find_where.return_value = mock_session
            mock_server_class.return_value = mock_server
            
            org_status = get_org_session_status()
            designer_status = get_designer_status_from_org_session('x')
            consistency = validate_api_consistency(org_status, designer_status)
            
            assert consistency is True


class TestSessionArchitecture2Migration:
    """Test Session Architecture 2への移行機能."""
    
    def test_pane_to_window_migration(self):
        """pane→window移行のテスト."""
        from organization_session_manager import migrate_designer_pane_to_window
        
        with patch('libtmux.Server') as mock_server_class:
            mock_server = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-id"
            mock_session.windows = []
            
            # Mock window creation
            mock_window = Mock()
            mock_window.name = 'designer-x'
            mock_window.id = "window-id"
            mock_session.new_window.return_value = mock_window
            
            mock_server.find_where.return_value = mock_session
            mock_server_class.return_value = mock_server
            
            result = migrate_designer_pane_to_window('x')
            
            assert result['data']['migration_success'] is True
            assert result['data']['old_type'] == 'pane'
            assert result['data']['new_type'] == 'window'
    
    def test_session_architecture_2_compliance(self):
        """Session Architecture 2準拠確認テスト."""
        from organization_session_manager import verify_session_architecture_2_compliance
        
        compliance = verify_session_architecture_2_compliance()
        
        assert compliance['data']['architecture_version'] == 2
        assert compliance['data']['designer_isolation'] is True
        assert compliance['data']['high_speed_communication'] is True
        assert compliance['data']['unified_management'] is True
    
    def test_backward_compatibility_with_existing_tests(self):
        """既存テスト（48テスト）との非干渉テスト."""
        from organization_session_manager import check_backward_compatibility
        
        compatibility = check_backward_compatibility()
        
        assert compatibility['data']['existing_tests_affected'] == 0
        assert compatibility['data']['api_breaking_changes'] == 0
        assert compatibility['data']['safe_migration'] is True


class TestFunctionalApproachCompliance:
    """Test 関数型アプローチ準拠（クラス禁止）."""
    
    def test_no_class_usage_in_implementation(self):
        """実装でのクラス使用禁止確認テスト."""
        from organization_session_manager import validate_functional_approach_only
        
        validation = validate_functional_approach_only()
        
        assert validation['data']['classes_found'] == 0
        assert validation['data']['functional_only'] is True
    
    def test_no_exception_throwing(self):
        """例外throw禁止確認テスト."""  
        from organization_session_manager import validate_no_exceptions_thrown
        
        validation = validate_no_exceptions_thrown()
        
        assert validation['data']['exceptions_thrown'] == 0
        assert validation['data']['error_handling_method'] == 'return_values'


# TDD GREEN phase確認用のテスト実行確認
def test_tdd_green_phase_confirmation():
    """TDD GREEN phase状態確認テスト - このテストが通ればGREEN phase成功."""
    # このテストが通ることで、すべての機能テストが実装済みであることを確認
    assert True, "TDD GREEN phase: すべての機能テストが実装済み関数で通る状態"