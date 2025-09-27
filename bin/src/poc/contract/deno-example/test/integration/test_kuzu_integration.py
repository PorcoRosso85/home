import pytest
from persistence.kuzu_py.core.database import create_database


def test_can_create_contract_tables():
    """契約テーブルが作成できることを確認"""
    # Arrange
    db = create_database(in_memory=True, use_cache=False)
    
    # Act - この時点では実装がないため失敗する
    with pytest.raises(Exception):
        # DDLを適用する処理（未実装）
        apply_ddl(db, "ddl/contract_schema.cypher")
    
    # Assert - テーブルの存在確認
    tables = db.execute("CALL table_info() RETURN *").get_as_df()
    assert "LocationURI" in tables["name"].values