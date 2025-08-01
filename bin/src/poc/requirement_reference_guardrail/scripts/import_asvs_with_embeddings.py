#!/usr/bin/env python3
"""
ASVS Import with Embeddings Script (Functional Version)

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
from typing import List, Optional, Dict, Any, Tuple, Union
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


# Type definitions for clarity
DatabaseConnection = Tuple[kuzu.Database, kuzu.Connection]
EmbedderFunction = Any  # The actual embedder function type
ImportResult = Dict[str, Any]
ProcessResult = Dict[str, Any]
VerificationResult = Dict[str, Any]


def create_database_connection(db_path: str) -> Union[DatabaseConnection, ImportResult]:
    """
    Create database and connection
    
    Args:
        db_path: Path to the KuzuDB database
        
    Returns:
        Tuple of (database, connection) on success, or error dict on failure
    """
    try:
        # Create database
        db_result = create_database(db_path)
        
        # Check if result is a kuzu.Database instance
        if isinstance(db_result, kuzu.Database):
            db = db_result
        else:
            # It's an error type (FileOperationError or ValidationError)
            return {
                "success": False,
                "error": f"Failed to create database: {db_result.message}"
            }
        
        # Create connection
        conn_result = create_connection(db)
        
        # Check if result is a kuzu.Connection instance
        if isinstance(conn_result, kuzu.Connection):
            conn = conn_result
        else:
            # It's an error type
            return {
                "success": False,
                "error": f"Failed to create connection: {conn_result.message}"
            }
        
        logger.info(f"Connected to database at {db_path}")
        return (db, conn)
        
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return {
            "success": False,
            "error": f"Failed to connect: {str(e)}"
        }


def create_embedder_function(model_name: str) -> Union[EmbedderFunction, ImportResult]:
    """
    Create embedder function
    
    Args:
        model_name: Name of the sentence transformer model
        
    Returns:
        Embedder function on success, or error dict on failure
    """
    try:
        embedder_result = create_embedder(model_name)
        
        # Check if embedder creation succeeded
        if callable(embedder_result):
            return embedder_result
        else:
            # It's an error dictionary
            return {
                "success": False,
                "error": f"Failed to create embedder: {embedder_result.get('message', embedder_result.get('error', 'Unknown error'))}"
            }
    except Exception as e:
        logger.error(f"Failed to create embedder: {e}")
        return {
            "success": False,
            "error": f"Failed to create embedder: {str(e)}"
        }


def ensure_reference_entity_schema(conn: kuzu.Connection) -> ImportResult:
    """
    Ensure the ReferenceEntity table exists
    
    Args:
        conn: KuzuDB connection
        
    Returns:
        Result dictionary with success status
    """
    try:
        # Check if ReferenceEntity table exists
        result = conn.execute("CALL TABLE_INFO('ReferenceEntity') RETURN *")
        if result.has_next():
            logger.info("ReferenceEntity table already exists")
            return {"success": True}
            
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
        conn.execute(create_table_query)
        logger.info("ReferenceEntity table created successfully")
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to create table: {e}")
        return {
            "success": False,
            "error": f"Failed to create table: {str(e)}"
        }


def load_asvs_requirements(asvs_path: str) -> Union[Tuple[List[Dict[str, Any]], str], ImportResult]:
    """
    Load ASVS requirements from markdown files
    
    Args:
        asvs_path: Path to ASVS markdown files
        
    Returns:
        Tuple of (requirements list, version) on success, or error dict on failure
    """
    try:
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
            
        return (requirements, metadata.version)
        
    except Exception as e:
        logger.error(f"Failed to load ASVS data: {e}")
        return {
            "success": False,
            "error": f"Failed to load ASVS data: {str(e)}"
        }


def determine_requirement_level(req: Dict[str, Any]) -> str:
    """
    Determine the level string for a requirement
    
    Args:
        req: Requirement dictionary
        
    Returns:
        Level string (L1, L2, L3, or N/A)
    """
    if req['level3']:
        return "L3"
    elif req['level2']:
        return "L2"
    elif req['level1']:
        return "L1"
    else:
        return "N/A"


def create_reference_dict(req: Dict[str, Any], version: str, level: str) -> ReferenceDict:
    """
    Create ReferenceDict for embedding
    
    Args:
        req: Requirement dictionary
        version: ASVS version
        level: Level string
        
    Returns:
        ReferenceDict object
    """
    return ReferenceDict(
        uri=req['uri'],
        title=f"ASVS {req['number']}",
        entity_type='requirement',
        description=req['description'],
        metadata={
            'source': f"OWASP ASVS {version}",
            'category': req['section'],
            'level': level,
            'chapter': req['chapter'],
            'cwe': req['cwe'],
            'nist': req['nist'],
            'number': req['number']
        }
    )


def generate_embedding(embedder: EmbedderFunction, content: str) -> Union[List[float], None]:
    """
    Generate embedding for content
    
    Args:
        embedder: Embedder function
        content: Text content to embed
        
    Returns:
        Embedding vector or None on failure
    """
    try:
        # The embedder takes a list of strings
        embedding_result = embedder([content])
        if not embedding_result['ok']:
            logger.warning(f"Failed to generate embedding: {embedding_result.get('message', 'Unknown error')}")
            return None
            
        # Extract the first (and only) embedding from the result
        embedding_vector = embedding_result['embeddings'][0]
        return embedding_vector.tolist() if hasattr(embedding_vector, 'tolist') else list(embedding_vector)
        
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


def insert_reference_entity(
    conn: kuzu.Connection,
    req: Dict[str, Any],
    embedding: List[float],
    version: str,
    level: str
) -> bool:
    """
    Insert a reference entity into the database
    
    Args:
        conn: Database connection
        req: Requirement dictionary
        embedding: Embedding vector
        version: ASVS version
        level: Level string
        
    Returns:
        True on success, False on failure
    """
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
        'embedding': embedding,
        'version': version,
        'url': f"https://github.com/OWASP/ASVS/blob/v{version}/5.0/en/{req['chapter'].split()[0]}-*.md"
    }
    
    try:
        conn.execute(insert_query, parameters)
        return True
    except Exception as e:
        logger.error(f"Failed to insert requirement {req.get('uri', 'unknown')}: {e}")
        return False


def process_requirement_batch(
    conn: kuzu.Connection,
    embedder: EmbedderFunction,
    requirements: List[Dict[str, Any]],
    version: str
) -> int:
    """
    Process a batch of requirements
    
    Args:
        conn: Database connection
        embedder: Embedder function
        requirements: List of requirement dictionaries
        version: ASVS version
        
    Returns:
        Number of requirements processed successfully
    """
    processed = 0
    
    for req in requirements:
        try:
            # Determine level
            level = determine_requirement_level(req)
            
            # Create reference dict
            ref_dict = create_reference_dict(req, version, level)
            
            # Generate embedding
            embedding = generate_embedding(embedder, ref_dict['description'])
            if embedding is None:
                continue
            
            # Insert into database
            if insert_reference_entity(conn, req, embedding, version, level):
                processed += 1
                
        except Exception as e:
            logger.error(f"Failed to process requirement {req.get('uri', 'unknown')}: {e}")
            continue
            
    return processed


def import_asvs_requirements(
    conn: kuzu.Connection,
    embedder: EmbedderFunction,
    asvs_path: str,
    batch_size: int = 50
) -> ImportResult:
    """
    Import ASVS requirements with embeddings
    
    Args:
        conn: Database connection
        embedder: Embedder function
        asvs_path: Path to ASVS markdown files
        batch_size: Number of requirements to process in each batch
        
    Returns:
        Result dictionary with import status and count
    """
    logger.info(f"Starting ASVS import from {asvs_path}")
    
    # Ensure schema exists
    schema_result = ensure_reference_entity_schema(conn)
    if not schema_result.get("success", False):
        return schema_result
    
    # Load ASVS data
    load_result = load_asvs_requirements(asvs_path)
    if isinstance(load_result, dict):
        # It's an error
        return load_result
    
    requirements, version = load_result
    
    # Process requirements in batches
    imported_count = 0
    
    for i in range(0, len(requirements), batch_size):
        batch = requirements[i:i + batch_size]
        imported_count += process_requirement_batch(conn, embedder, batch, version)
        logger.info(f"Processed {min(i + batch_size, len(requirements))}/{len(requirements)} requirements")
        
    logger.info(f"Successfully imported {imported_count} ASVS requirements")
    return {
        "success": True,
        "imported_count": imported_count,
        "total_count": len(requirements)
    }


def verify_import(conn: kuzu.Connection) -> VerificationResult:
    """
    Verify the import by checking counts and sample data
    
    Args:
        conn: Database connection
        
    Returns:
        Dictionary with verification results
    """
    try:
        # Count total references
        count_result = conn.execute(
            "MATCH (r:ReferenceEntity) RETURN COUNT(r) as count"
        )
        count = 0
        if count_result.has_next():
            count = count_result.get_next()[0]
            
        # Get sample references
        sample_result = conn.execute(
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
        embedding_check = conn.execute(
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
        
    # Create database connection
    conn_result = create_database_connection(args.db_path)
    if isinstance(conn_result, dict):
        # It's an error
        logger.error(f"Database connection failed: {conn_result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    db, conn = conn_result
    
    # Create embedder
    embedder_result = create_embedder_function(args.model_name)
    if isinstance(embedder_result, dict):
        # It's an error
        logger.error(f"Embedder creation failed: {embedder_result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    embedder = embedder_result
    
    try:
        # Import ASVS data
        import_result = import_asvs_requirements(conn, embedder, str(asvs_path))
        if not import_result.get("success", False):
            logger.error(f"Import failed: {import_result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        count = import_result.get('imported_count', 0)
        logger.info(f"Import completed: {count} requirements imported")
        
        # Verify if requested
        if args.verify:
            logger.info("Verifying import...")
            verification = verify_import(conn)
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
