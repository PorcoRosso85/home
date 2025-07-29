#!/usr/bin/env python3
"""
ASVS Import with Embeddings Script

This script imports ASVS requirements from the asvs_reference POC,
generates embeddings using the embed POC, and stores them in KuzuDB
as ReferenceEntity nodes.

Usage:
    python scripts/import_asvs_with_embeddings.py \
        --asvs-path /path/to/asvs/markdown \
        --db-path ./reference_guardrail.db \
        --model-name sentence-transformers/all-MiniLM-L6-v2
"""
import argparse
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

# Import from asvs_reference POC
sys.path.append(str(Path(__file__).parent.parent.parent / "asvs_reference"))
from asvs_arrow_converter import ASVSArrowConverter
from asvs_arrow_types import ASVSRequirementRow

# Import from embed POC
sys.path.append(str(Path(__file__).parent.parent.parent / "embed"))
from embed_pkg import create_embedder, create_embedding_repository
from embed_pkg.types import ReferenceDict, SaveResult

# Import from kuzu_py
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "persistence/kuzu_py"))
from kuzu_py import create_database, create_connection
import kuzu

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ASVSImporter:
    """Imports ASVS requirements with embeddings into KuzuDB"""
    
    def __init__(self, db_path: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the importer
        
        Args:
            db_path: Path to the KuzuDB database
            model_name: Name of the sentence transformer model to use
        """
        self.db_path = Path(db_path)
        self.model_name = model_name
        self._db = None
        self._conn = None
        self._embedder = None
        self._embedding_repo = None
        
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        
    def connect(self):
        """Connect to the database and initialize components"""
        try:
            # Create database and connection
            db_result = create_database(str(self.db_path))
            
            # Check if result is a kuzu.Database instance
            if isinstance(db_result, kuzu.Database):
                self._db = db_result
            else:
                # It's an error type (FileOperationError or ValidationError)
                raise RuntimeError(f"Failed to create database: {db_result.message}")
            
            conn_result = create_connection(self._db)
            
            # Check if result is a kuzu.Connection instance
            if isinstance(conn_result, kuzu.Connection):
                self._conn = conn_result
            else:
                # It's an error type
                raise RuntimeError(f"Failed to create connection: {conn_result.message}")
            
            # Initialize embedder and repository
            embedder_result = create_embedder(self.model_name)
            
            # Check if embedder creation succeeded
            if callable(embedder_result):
                self._embedder = embedder_result
            else:
                # It's an error dictionary
                raise RuntimeError(f"Failed to create embedder: {embedder_result.get('message', embedder_result.get('error', 'Unknown error'))}")
            
            self._embedding_repo = create_embedding_repository(
                database_path=str(self.db_path),
                embedder=self._embedder
            )
            
            logger.info(f"Connected to database at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
            
    def close(self):
        """Close database connections"""
        if self._conn:
            self._conn = None
        if self._db:
            self._db = None
        logger.info("Database connections closed")
        
    def ensure_schema(self):
        """Ensure the ReferenceEntity table exists"""
        try:
            # Check if ReferenceEntity table exists
            result = self._conn.execute("CALL TABLE_INFO('ReferenceEntity') RETURN *")
            if result.has_next():
                logger.info("ReferenceEntity table already exists")
                return
                
        except Exception:
            # Table doesn't exist, create it
            logger.info("Creating ReferenceEntity table...")
            
        # Create the table
        create_table_query = """
        CREATE NODE TABLE IF NOT EXISTS ReferenceEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            source STRING,
            category STRING,
            level STRING,
            embedding DOUBLE[384],
            version STRING,
            url STRING
        )
        """
        
        try:
            self._conn.execute(create_table_query)
            logger.info("ReferenceEntity table created successfully")
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise
            
    def import_asvs(self, asvs_path: str) -> int:
        """
        Import ASVS requirements from markdown files
        
        Args:
            asvs_path: Path to ASVS markdown files
            
        Returns:
            Number of requirements imported
        """
        logger.info(f"Starting ASVS import from {asvs_path}")
        
        try:
            # Ensure schema exists
            self.ensure_schema()
            
            # Load ASVS data using Arrow converter
            converter = ASVSArrowConverter(asvs_path)
            table = converter.get_requirements_table()
            metadata = converter.get_metadata()
            
            logger.info(f"Loaded {table.num_rows} ASVS requirements from version {metadata.version}")
            
            # Convert Arrow table to list of requirements
            requirements = []
            for i in range(table.num_rows):
                req = {
                    'uri': table['uri'][i].as_py(),
                    'number': table['number'][i].as_py(),
                    'description': table['description'][i].as_py(),
                    'level1': table['level1'][i].as_py(),
                    'level2': table['level2'][i].as_py(),
                    'level3': table['level3'][i].as_py(),
                    'section': table['section'][i].as_py(),
                    'chapter': table['chapter'][i].as_py(),
                    'cwe': table['cwe'][i].as_py(),
                    'nist': table['nist'][i].as_py()
                }
                requirements.append(req)
                
            # Process requirements in batches
            batch_size = 50
            imported_count = 0
            
            for i in range(0, len(requirements), batch_size):
                batch = requirements[i:i + batch_size]
                imported_count += self._process_batch(batch, metadata.version)
                logger.info(f"Processed {min(i + batch_size, len(requirements))}/{len(requirements)} requirements")
                
            logger.info(f"Successfully imported {imported_count} ASVS requirements")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import ASVS: {e}")
            raise
            
    def _process_batch(self, requirements: List[Dict[str, Any]], version: str) -> int:
        """
        Process a batch of requirements
        
        Args:
            requirements: List of requirement dictionaries
            version: ASVS version
            
        Returns:
            Number of requirements processed
        """
        processed = 0
        
        for req in requirements:
            try:
                # Determine level string
                if req['level3']:
                    level = "L3"
                elif req['level2']:
                    level = "L2"
                elif req['level1']:
                    level = "L1"
                else:
                    level = "N/A"
                    
                # Create ReferenceDict for embedding
                ref_dict = ReferenceDict(
                    id=req['uri'],
                    content=req['description'],
                    metadata={
                        'title': f"ASVS {req['number']}",
                        'source': f"OWASP ASVS {version}",
                        'category': req['section'],
                        'level': level,
                        'chapter': req['chapter'],
                        'cwe': req['cwe'],
                        'nist': req['nist']
                    }
                )
                
                # Generate embedding
                # The embedder takes a list of strings, so wrap the content
                embedding_result = self._embedder([ref_dict.content])
                if not embedding_result['ok']:
                    logger.warning(f"Failed to generate embedding for {req['uri']}: {embedding_result.get('message', 'Unknown error')}")
                    continue
                    
                # Prepare data for insertion
                # Extract the first (and only) embedding from the result
                embedding_vector = embedding_result['embeddings'][0]
                
                # Insert into KuzuDB
                insert_query = """
                CREATE (r:ReferenceEntity {
                    id: $id,
                    title: $title,
                    description: $description,
                    source: $source,
                    category: $category,
                    level: $level,
                    embedding: $embedding,
                    version: $version,
                    url: $url
                })
                """
                
                parameters = {
                    'id': req['uri'],
                    'title': f"ASVS {req['number']}",
                    'description': req['description'],
                    'source': f"OWASP ASVS {version}",
                    'category': req['section'],
                    'level': level,
                    'embedding': embedding_vector.tolist() if hasattr(embedding_vector, 'tolist') else list(embedding_vector),
                    'version': version,
                    'url': f"https://github.com/OWASP/ASVS/blob/v{version}/5.0/en/{req['chapter'].split()[0]}-*.md"
                }
                
                self._conn.execute(insert_query, parameters)
                processed += 1
                
            except Exception as e:
                logger.error(f"Failed to process requirement {req.get('uri', 'unknown')}: {e}")
                continue
                
        return processed
        
    def verify_import(self) -> Dict[str, Any]:
        """
        Verify the import by checking counts and sample data
        
        Returns:
            Dictionary with verification results
        """
        try:
            # Count total references
            count_result = self._conn.execute(
                "MATCH (r:ReferenceEntity) RETURN COUNT(r) as count"
            )
            count = 0
            if count_result.has_next():
                count = count_result.get_next()[0]
                
            # Get sample references
            sample_result = self._conn.execute(
                "MATCH (r:ReferenceEntity) RETURN r.id, r.title, r.level LIMIT 5"
            )
            samples = []
            while sample_result.has_next():
                row = sample_result.get_next()
                samples.append({
                    'id': row[0],
                    'title': row[1],
                    'level': row[2]
                })
                
            # Check embedding dimensions
            embedding_check = self._conn.execute(
                "MATCH (r:ReferenceEntity) WHERE r.embedding IS NOT NULL RETURN r.id, SIZE(r.embedding) LIMIT 1"
            )
            embedding_dim = None
            if embedding_check.has_next():
                _, dim = embedding_check.get_next()
                embedding_dim = dim
                
            return {
                'total_count': count,
                'samples': samples,
                'embedding_dimension': embedding_dim,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to verify import: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Import ASVS requirements with embeddings into KuzuDB"
    )
    parser.add_argument(
        "--asvs-path",
        required=True,
        help="Path to ASVS markdown files"
    )
    parser.add_argument(
        "--db-path",
        default="./reference_guardrail.db",
        help="Path to KuzuDB database (default: ./reference_guardrail.db)"
    )
    parser.add_argument(
        "--model-name",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Sentence transformer model name"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the import after completion"
    )
    
    args = parser.parse_args()
    
    # Validate ASVS path
    asvs_path = Path(args.asvs_path)
    if not asvs_path.exists():
        logger.error(f"ASVS path does not exist: {asvs_path}")
        sys.exit(1)
        
    # Run import
    try:
        with ASVSImporter(args.db_path, args.model_name) as importer:
            # Import ASVS data
            count = importer.import_asvs(str(asvs_path))
            logger.info(f"Import completed: {count} requirements imported")
            
            # Verify if requested
            if args.verify:
                logger.info("Verifying import...")
                verification = importer.verify_import()
                if verification['success']:
                    logger.info(f"Verification successful:")
                    logger.info(f"  Total references: {verification['total_count']}")
                    logger.info(f"  Embedding dimension: {verification['embedding_dimension']}")
                    logger.info(f"  Sample references:")
                    for sample in verification['samples']:
                        logger.info(f"    - {sample['id']}: {sample['title']} ({sample['level']})")
                else:
                    logger.error(f"Verification failed: {verification.get('error', 'Unknown error')}")
                    sys.exit(1)
                    
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)
        

if __name__ == "__main__":
    main()