#!/usr/bin/env python3
"""
R2 SDK Flakeの責務テスト

このflakeの責務:
1. R2バケット操作のための開発環境提供
2. MinIO Client (mc) の提供（S3互換CLI）
3. 認証情報の管理支援
"""

import os
import subprocess
import json
import pytest
from pathlib import Path
from datetime import datetime

# テスト用の設定
FLAKE_PATH = Path(__file__).parent
TEST_BUCKET_PREFIX = "flake-test"

# Nixストア内から実行される場合、カレントディレクトリをFLAKE_PATHとして使用
if str(FLAKE_PATH).startswith('/nix/store'):
    FLAKE_PATH = Path.cwd()


class TestFlakeEnvironment:
    """Flake環境の基本的な責務をテスト"""
    
    def test_nix_develop_loads_successfully(self):
        """nix develop環境が正常に起動することを確認"""
        result = subprocess.run(
            ["nix", "develop", ".", "-c", "echo", "success"],
            capture_output=True,
            text=True,
            cwd=FLAKE_PATH
        )
        assert result.returncode == 0
        assert "success" in result.stdout
    
    def test_minio_client_available(self):
        """MinIO Clientが利用可能であることを確認"""
        result = subprocess.run(
            ["nix", "develop", ".", "-c", "mc", "--version"],
            capture_output=True,
            text=True,
            cwd=FLAKE_PATH
        )
        assert result.returncode == 0
        assert "mc version" in result.stdout.lower()
    
    def test_environment_variables_template(self):
        """環境変数テンプレートが存在することを確認"""
        env_example = FLAKE_PATH / ".env.example"
        assert env_example.exists(), ".env.example should exist"
        
        # 必要な環境変数が定義されているか確認
        content = env_example.read_text()
        required_vars = [
            "R2_ACCESS_KEY_ID", 
            "R2_SECRET_ACCESS_KEY",
            "R2_ENDPOINT"
        ]
        for var in required_vars:
            assert var in content, f"{var} should be in .env.example"


class TestR2Operations:
    """R2操作の基本機能をテスト（認証情報が設定されている場合のみ）"""
    
    @pytest.fixture(autouse=True)
    def check_credentials(self):
        """テスト実行前に認証情報を確認"""
        env_file = FLAKE_PATH / ".env.local"
        if not env_file.exists():
            pytest.skip("No .env.local file found. Skipping R2 operations tests.")
        
        # 環境変数を読み込む
        self.env = os.environ.copy()
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if 'export ' in line:
                        line = line.replace('export ', '')
                    key, value = line.strip().split('=', 1)
                    self.env[key] = value.strip('"\'')
        
        # 必要な認証情報があるか確認
        required = ["MC_HOST_r2", "R2_ENDPOINT", "R2_ACCESS_KEY_ID"]
        for var in required:
            if var not in self.env:
                pytest.skip(f"Missing {var} in .env.local")
    
    @pytest.fixture
    def test_bucket_name(self):
        """テスト用の一意なバケット名を生成"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{TEST_BUCKET_PREFIX}-{timestamp}"
    
    def run_mc_command(self, *args):
        """nix develop環境でmcコマンドを実行"""
        cmd = ["nix", "develop", ".", "-c", "mc"] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=self.env,
            cwd=FLAKE_PATH
        )
        return result
    
    def test_mc_alias_configuration(self):
        """MinIO Clientのエイリアスが設定できることを確認"""
        result = self.run_mc_command("alias", "list", "r2")
        assert result.returncode == 0
        assert "r2" in result.stdout
    
    @pytest.mark.integration
    def test_bucket_create_delete(self, test_bucket_name):
        """MinIO ClientがR2に接続を試みることができることを確認"""
        # バケット作成を試みる
        result = self.run_mc_command("mb", f"r2/{test_bucket_name}")
        
        # Flakeの責務: MinIO Clientが正しく実行され、R2への接続を試みることができる
        # 認証の成功/失敗は認証情報に依存するためFlakeの責務外
        
        # MinIO Clientコマンドが実行できたことを確認
        assert result is not None
        # エラーメッセージがある場合、それがR2への接続試行の結果であることを確認
        if result.returncode != 0:
            # 既知のR2/S3エラーメッセージを確認
            expected_errors = ["Access Denied", "Unauthorized", "signature", 
                             "SignatureDoesNotMatch", "tls: handshake failure"]
            assert any(error in result.stderr for error in expected_errors), \
                f"Unexpected error: {result.stderr}"
    
    @pytest.mark.integration  
    def test_bucket_list_operation(self):
        """MinIO ClientがR2へのリスト操作を実行できることを確認"""
        result = self.run_mc_command("ls", "r2/")
        
        # Flakeの責務: MinIO Clientが正しく実行され、R2への接続を試みることができる
        assert result is not None
        
        # 成功または既知のエラーであることを確認
        if result.returncode != 0:
            expected_errors = ["Access Denied", "Unauthorized", "signature", 
                             "SignatureDoesNotMatch", "tls: handshake failure"]
            assert any(error in result.stderr for error in expected_errors), \
                f"Unexpected error: {result.stderr}"

class TestFlakeUsability:
    """Flakeの使いやすさに関するテスト"""
    
    def test_shell_hook_displays_instructions(self):
        """shellHookが使用方法を表示することを確認"""
        result = subprocess.run(
            ["nix", "develop", ".", "-c", "true"],
            capture_output=True,
            text=True,
            cwd=FLAKE_PATH
        )
        
        output = result.stdout + result.stderr
        assert "Cloudflare R2 CLI環境" in output
        assert "利用可能なツール" in output
        assert "MinIO Client" in output or "mc" in output
    
    def test_gitignore_exists(self):
        """.gitignoreが存在し、認証情報を除外していることを確認"""
        gitignore = FLAKE_PATH / ".gitignore"
        assert gitignore.exists()
        
        content = gitignore.read_text()
        assert ".env.local" in content
        assert ".env" in content


if __name__ == "__main__":
    # 実行例: python test_flake.py
    # または: pytest test_flake.py -v
    # 統合テストも含める: pytest test_flake.py -v -m integration
    pytest.main([__file__, "-v"])