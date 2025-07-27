#!/usr/bin/env python3
"""
Runner script for the enforced guardrails demo
Handles proper database initialization with DDL
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'persistence', 'kuzu_py'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'requirement', 'graph'))

import tempfile
from pathlib import Path
import kuzu

from reference_repository import create_reference_repository
from asvs_loader import ASVSLoader
from enforced_workflow import EnforcedRequirementWorkflow
from test_completeness_report import TestCompletenessAnalyzer
from demo_enforced_guardrails import GuardrailsDemo


def initialize_database(db_path):
    """Initialize database with proper DDL"""
    # Create connection
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # Apply base DDL for reference entities
    ddl_path = Path(__file__).parent / "ddl" / "v3.5.0_reference_entity.cypher"
    if ddl_path.exists():
        with open(ddl_path, 'r') as f:
            ddl_content = f.read()
        
        # Execute DDL statements
        for statement in ddl_content.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    conn.execute(statement)
                except Exception as e:
                    # Ignore if already exists
                    if "already exists" not in str(e):
                        print(f"Warning: {e}")
    
    # Also create RequirementEntity if not exists
    try:
        conn.execute("""
        CREATE NODE TABLE IF NOT EXISTS RequirementEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING,
            entity_type STRING,
            metadata STRING
        )
        """)
    except:
        pass
    
    conn.close()
    return db_path


class InitializedGuardrailsDemo(GuardrailsDemo):
    """Demo with proper database initialization"""
    
    def __init__(self):
        """Initialize demo with temporary database"""
        # Create temp file for database
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_file.name
        self.temp_file.close()
        
        # Initialize database with DDL
        initialize_database(self.db_path)
        
        # Now setup the system
        self._setup_system()
    
    def __del__(self):
        """Clean up temp file"""
        if hasattr(self, 'temp_file'):
            try:
                Path(self.db_path).unlink(missing_ok=True)
            except:
                pass


def main():
    """Run the demo with proper initialization"""
    print("🚀 Running Enforced Reference Guardrails Demo")
    print("=" * 60)
    
    try:
        demo = InitializedGuardrailsDemo()
        demo.run_all_demos()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()