"""
Test for ASVS Arrow Converter
特性テストとして現在の振る舞いを記録
"""
import pytest
import pyarrow as pa
from pathlib import Path

from asvs_arrow_converter import ASVSArrowConverter


class TestArrowConverter:
    """Arrow変換の特性テスト"""
    
    def test_converter_returns_arrow_table(self, tmp_path):
        """コンバーターがArrow Tableを返すことを確認"""
        # GIVEN: サンプルのMarkdownファイル
        sample_dir = tmp_path / "5.0"
        sample_dir.mkdir()
        
        sample_md = sample_dir / "V2.md"
        sample_md.write_text("""
# V2 Authentication

## V2.1 Password Security

| # | Description | L1 | L2 | L3 |
|---|-------------|----|----|-----|
| 2.1.1 | Verify that user set passwords are at least 12 characters in length | ✓ | ✓ | ✓ |
| 2.1.2 | Verify that passwords of at least 64 characters are permitted | ✓ | ✓ | ✓ |
""")
        
        # WHEN: Arrow変換を実行
        converter = ASVSArrowConverter(str(sample_dir))
        table = converter.get_requirements_table()
        
        # THEN: Arrow Tableが返される
        assert isinstance(table, pa.Table)
        assert table.num_rows == 2
        assert 'uri' in table.column_names
        assert 'number' in table.column_names
        assert 'description' in table.column_names
        assert 'level1' in table.column_names
        assert 'level2' in table.column_names
        assert 'level3' in table.column_names
    
    def test_metadata_extraction(self, tmp_path):
        """メタデータが正しく抽出されることを確認"""
        # GIVEN: サンプルのMarkdownファイル
        sample_dir = tmp_path / "5.0"
        sample_dir.mkdir()
        
        sample_md = sample_dir / "V2.md"
        sample_md.write_text("""
# V2 Authentication

## V2.1 Password Security

| # | Description | L1 | L2 | L3 |
|---|-------------|----|----|-----|
| 2.1.1 | Verify minimum password length | ✓ | ✓ | ✓ |
""")
        
        # WHEN: メタデータを取得
        converter = ASVSArrowConverter(str(sample_dir))
        metadata = converter.get_metadata()
        
        # THEN: 正しいメタデータが返される
        assert metadata['source'] == 'OWASP/ASVS'
        assert metadata['version'] == '5.0'
        assert metadata['total_requirements'] == 1
        assert metadata['levels'] == [1, 2, 3]
        assert metadata['schema_version'] == '1.0'
    
    def test_parquet_export(self, tmp_path):
        """Parquetエクスポートが動作することを確認"""
        # GIVEN: サンプルデータとコンバーター
        sample_dir = tmp_path / "5.0"
        sample_dir.mkdir()
        
        sample_md = sample_dir / "V2.md"
        sample_md.write_text("""
# V2 Authentication

## V2.1 Password Security

| # | Description | L1 | L2 | L3 |
|---|-------------|----|----|-----|
| 2.1.1 | Test requirement | ✓ | | |
""")
        
        converter = ASVSArrowConverter(str(sample_dir))
        
        # WHEN: Parquetファイルに保存
        output_path = tmp_path / "test.parquet"
        converter.to_parquet(str(output_path))
        
        # THEN: ファイルが作成され、読み込み可能
        assert output_path.exists()
        
        import pyarrow.parquet as pq
        loaded_table = pq.read_table(str(output_path))
        assert loaded_table.num_rows == 1
        assert loaded_table.column_names == converter.get_requirements_table().column_names