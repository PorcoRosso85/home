#!/usr/bin/env python3
"""
Directory Scanner with Search - Convention-compliant implementation

規約遵守:
- クラス禁止、高階関数使用
- エラーを値として返す
- デフォルト引数禁止
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Callable, Optional, Set

# Import types
from scanner_types import (
    ScanSuccess, ScanError, ScanResult,
    DiffSuccess, DiffError, DiffResult,
    SearchSuccess, SearchError, SearchResult,
    IndexSuccess, IndexError, IndexResult,
    MetadataSuccess, MetadataError, MetadataResult,
    DirectoryInfo, DBStatus, SearchHit
)

# Mock search implementations for now
def create_text_search(conn):
    """Mock FTS implementation"""
    def create_index(fields):
        return {'ok': True, 'message': f"FTS index created on {fields}"}
    
    def search(query, conjunctive):
        if not query:
            return {'ok': False, 'error': 'empty query not allowed'}
        return {'ok': True, 'results': []}
    
    return {
        'create_index': create_index,
        'search': search
    }

def create_embedder(model_name):
    """Mock embedder"""
    def generate_embedding(text):
        if not text:
            return {'ok': False, 'error': 'Empty text'}
        # Generate fake embedding
        return {'ok': True, 'embedding': [0.1] * 384}
    return generate_embedding

def create_vector_search(conn, embedder):
    """Mock VSS implementation"""
    def search(query, k):
        if not query:
            return {'ok': False, 'error': 'empty query not allowed'}
        return {'ok': True, 'results': []}
    
    return {
        'search': search
    }


def _is_hidden(path: str) -> bool:
    """Check if path is hidden (starts with dot)
    
    Args:
        path: チェックするパス
        
    Returns:
        True: 隠しファイル/ディレクトリ
        False: 通常のファイル/ディレクトリ
    """
    return os.path.basename(path).startswith('.')


def _is_empty_dir(path: str) -> bool:
    """Check if directory is empty
    
    Args:
        path: チェックするディレクトリパス
        
    Returns:
        True: 空ディレクトリ
        False: ファイル/サブディレクトリあり
    """
    try:
        return not bool(os.listdir(path))
    except (OSError, PermissionError):
        return True


def _get_file_count(path: str) -> int:
    """Count files in directory (non-recursive)
    
    Args:
        path: カウントするディレクトリパス
        
    Returns:
        ファイル数
    """
    try:
        return len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
    except (OSError, PermissionError):
        return 0


def _get_subdirs(path: str) -> List[str]:
    """Get immediate subdirectories
    
    Args:
        path: 親ディレクトリパス
        
    Returns:
        サブディレクトリ名のリスト
    """
    try:
        return [d for d in os.listdir(path) 
                if os.path.isdir(os.path.join(path, d))]
    except (OSError, PermissionError):
        return []


def _extract_flake_description(path: str) -> Optional[str]:
    """Extract description from flake.nix
    
    Args:
        path: flake.nixを含むディレクトリパス
        
    Returns:
        descriptionフィールドの値またはNone
    """
    flake_path = os.path.join(path, 'flake.nix')
    if not os.path.exists(flake_path):
        return None
    
    try:
        with open(flake_path, 'r') as f:
            content = f.read()
        # Simple regex to find description
        match = re.search(r'description\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def _extract_package_json_description(path: str) -> Optional[str]:
    """Extract description from package.json"""
    pkg_path = os.path.join(path, 'package.json')
    if not os.path.exists(pkg_path):
        return None
    
    try:
        with open(pkg_path, 'r') as f:
            data = json.load(f)
        return data.get('description')
    except Exception:
        pass
    return None


def _extract_python_docstring(path: str) -> Optional[str]:
    """Extract docstring from main.py or __init__.py"""
    for filename in ['main.py', '__init__.py']:
        file_path = os.path.join(path, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                # Extract module docstring
                match = re.match(r'^"""(.+?)"""', content, re.DOTALL)
                if match:
                    return match.group(1).strip().split('\n')[0]
            except Exception:
                pass
    return None


def _get_readme_content(path: str) -> Optional[str]:
    """Get README content if exists"""
    for readme in ['README.md', 'readme.md', 'Readme.md']:
        readme_path = os.path.join(path, readme)
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r') as f:
                    return f.read()
            except Exception:
                pass
    return None


def _scan_directory(root_path: str, skip_hidden: bool, skip_empty: bool, 
                   max_depth: Optional[int], current_depth: int) -> List[DirectoryInfo]:
    """Recursively scan directory tree"""
    if max_depth is not None and current_depth > max_depth:
        return []
    
    results = []
    
    try:
        for item in os.listdir(root_path):
            if skip_hidden and _is_hidden(item):
                continue
                
            full_path = os.path.join(root_path, item)
            
            # Skip broken symlinks
            if os.path.islink(full_path) and not os.path.exists(full_path):
                continue
                
            if os.path.isdir(full_path):
                # Check permissions
                if not os.access(full_path, os.R_OK):
                    continue
                    
                if skip_empty and _is_empty_dir(full_path):
                    continue
                
                # Get directory info
                readme_content = _get_readme_content(full_path)
                metadata = {}
                
                # Extract metadata
                if desc := _extract_flake_description(full_path):
                    metadata['flake_description'] = desc
                if desc := _extract_package_json_description(full_path):
                    metadata['package_description'] = desc
                if desc := _extract_python_docstring(full_path):
                    metadata['python_docstring'] = desc
                
                info = DirectoryInfo(
                    path=full_path,
                    has_readme=readme_content is not None,
                    file_count=_get_file_count(full_path),
                    subdirs=_get_subdirs(full_path),
                    metadata=metadata
                )
                results.append(info)
                
                # Recurse
                results.extend(_scan_directory(
                    full_path, skip_hidden, skip_empty, 
                    max_depth, current_depth + 1
                ))
                
    except (OSError, PermissionError):
        # Skip directories we can't read
        pass
    
    return results


def create_directory_scanner(root_path: str, db_path: str) -> Dict[str, Callable]:
    """Create directory scanner with all operations
    
    Returns dictionary of operations following convention.
    """
    # Initialize database connection
    try:
        import kuzu
        if db_path == ':memory:':
            conn = kuzu.Connection(kuzu.Database(":memory:"))
        else:
            db = kuzu.Database(db_path)
            conn = kuzu.Connection(db)
    except (ImportError, AttributeError):
        # Use mock for testing
        from mock_db import get_mock_connection
        conn = get_mock_connection(db_path)
    
    # Create schema
    try:
        conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Directory(
                path STRING PRIMARY KEY,
                has_readme BOOLEAN,
                file_count INT64,
                metadata STRING,
                last_modified TIMESTAMP,
                embedding DOUBLE[384]
            )
        """)
        conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS README(
                path STRING PRIMARY KEY,
                content STRING,
                last_modified TIMESTAMP
            )
        """)
    except Exception:
        pass  # Tables might already exist
    
    # State for storing scan results
    state = {
        'last_scan': {},  # path -> last_modified mapping
        'fts_ops': None,
        'vss_ops': None,
        'embedder': None
    }
    
    def full_scan(skip_empty: bool, skip_hidden: bool,
                  generate_embeddings: bool) -> ScanResult:
        """Perform full directory scan"""
        start_time = time.time()
        
        try:
            # Scan directories
            dirs = _scan_directory(root_path, skip_hidden, skip_empty, None, 0)
            
            # Clear existing data
            try:
                conn.execute("MATCH (d:Directory) DELETE d")
                conn.execute("MATCH (r:README) DELETE r")
            except Exception:
                pass
            
            # Insert new data
            new_count = 0
            for dir_info in dirs:
                try:
                    # Insert directory
                    conn.execute("""
                        CREATE (d:Directory {
                            path: $path,
                            has_readme: $has_readme,
                            file_count: $file_count,
                            metadata: $metadata,
                            last_modified: timestamp()
                        })
                    """, {
                        'path': dir_info['path'],
                        'has_readme': dir_info['has_readme'],
                        'file_count': dir_info['file_count'],
                        'metadata': json.dumps(dir_info['metadata'])
                    })
                    
                    # Insert README if exists
                    if dir_info['has_readme']:
                        readme_content = _get_readme_content(dir_info['path'])
                        if readme_content:
                            conn.execute("""
                                CREATE (r:README {
                                    path: $path,
                                    content: $content,
                                    last_modified: timestamp()
                                })
                            """, {
                                'path': dir_info['path'],
                                'content': readme_content
                            })
                    
                    new_count += 1
                    # Update state
                    state['last_scan'][dir_info['path']] = time.time()
                    
                except Exception:
                    pass
            
            # Add root directory itself
            if not skip_empty or not _is_empty_dir(root_path):
                try:
                    conn.execute("""
                        CREATE (d:Directory {
                            path: $path,
                            has_readme: $has_readme,
                            file_count: $file_count,
                            metadata: $metadata,
                            last_modified: timestamp()
                        })
                    """, {
                        'path': root_path,
                        'has_readme': _get_readme_content(root_path) is not None,
                        'file_count': _get_file_count(root_path),
                        'metadata': '{}'
                    })
                    new_count += 1
                except Exception:
                    pass
            
            duration_ms = (time.time() - start_time) * 1000
            
            return ScanSuccess(
                ok=True,
                scanned_count=new_count,
                new_count=new_count,
                updated_count=0,
                deleted_count=0,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            return ScanError(ok=False, error=str(e))
    
    def detect_changes() -> DiffResult:
        """Detect filesystem changes since last scan"""
        try:
            added = []
            modified = []
            deleted = []
            
            # Get current state from DB
            result = conn.execute("MATCH (d:Directory) RETURN d.path")
            db_paths = set()
            while result.has_next():
                row = result.get_next()
                db_paths.add(row[0])
            
            # Scan current filesystem
            current_dirs = _scan_directory(root_path, True, False, None, 0)
            current_paths = {d['path'] for d in current_dirs}
            
            # Find added
            for path in current_paths - db_paths:
                added.append(path)
            
            # Find deleted
            for path in db_paths - current_paths:
                deleted.append(path)
            
            # Find modified (check README existence)
            for dir_info in current_dirs:
                if dir_info['path'] in db_paths:
                    # Check if README status changed
                    result = conn.execute(
                        "MATCH (d:Directory {path: $path}) RETURN d.has_readme",
                        {'path': dir_info['path']}
                    )
                    if result.has_next():
                        row = result.get_next()
                        old_has_readme = row[0]
                        if old_has_readme != dir_info['has_readme']:
                            modified.append(dir_info['path'])
                    
                    # Check if README content changed (by timestamp)
                    if dir_info['has_readme']:
                        readme_path = None
                        for readme in ['README.md', 'readme.md', 'Readme.md']:
                            full_readme_path = os.path.join(dir_info['path'], readme)
                            if os.path.exists(full_readme_path):
                                readme_path = full_readme_path
                                break
                        
                        if readme_path:
                            current_mtime = os.path.getmtime(readme_path)
                            if dir_info['path'] in state['last_scan']:
                                if current_mtime > state['last_scan'][dir_info['path']]:
                                    if dir_info['path'] not in modified:
                                        modified.append(dir_info['path'])
            
            return DiffSuccess(
                ok=True,
                added=added,
                modified=modified,
                deleted=deleted
            )
            
        except Exception as e:
            return DiffError(ok=False, error=str(e))
    
    def incremental_update() -> ScanResult:
        """Perform incremental update based on detected changes"""
        start_time = time.time()
        
        try:
            # Detect changes
            diff_result = detect_changes()
            if not diff_result['ok']:
                return ScanError(ok=False, error="Failed to detect changes")
            
            new_count = len(diff_result['added'])
            updated_count = len(diff_result['modified'])
            deleted_count = len(diff_result['deleted'])
            
            # Process deletions
            for path in diff_result['deleted']:
                conn.execute("MATCH (d:Directory {path: $path}) DELETE d", {'path': path})
                conn.execute("MATCH (r:README {path: $path}) DELETE r", {'path': path})
            
            # Process additions
            for path in diff_result['added']:
                dir_info = DirectoryInfo(
                    path=path,
                    has_readme=_get_readme_content(path) is not None,
                    file_count=_get_file_count(path),
                    subdirs=_get_subdirs(path),
                    metadata={}
                )
                
                conn.execute("""
                    CREATE (d:Directory {
                        path: $path,
                        has_readme: $has_readme,
                        file_count: $file_count,
                        metadata: $metadata,
                        last_modified: timestamp()
                    })
                """, {
                    'path': dir_info['path'],
                    'has_readme': dir_info['has_readme'],
                    'file_count': dir_info['file_count'],
                    'metadata': json.dumps(dir_info['metadata'])
                })
            
            # Process modifications
            for path in diff_result['modified']:
                # Update directory info
                has_readme = _get_readme_content(path) is not None
                conn.execute("""
                    MATCH (d:Directory {path: $path})
                    SET d.has_readme = $has_readme,
                        d.last_modified = timestamp()
                """, {
                    'path': path,
                    'has_readme': has_readme
                })
            
            duration_ms = (time.time() - start_time) * 1000
            
            return ScanSuccess(
                ok=True,
                scanned_count=new_count + updated_count,
                new_count=new_count,
                updated_count=updated_count,
                deleted_count=deleted_count,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            return ScanError(ok=False, error=str(e))
    
    def build_fts_index() -> IndexResult:
        """Build FTS index for directory search"""
        try:
            # Initialize FTS if not already done
            if state['fts_ops'] is None:
                state['fts_ops'] = create_text_search(conn)
            
            # Create index on README content
            result = state['fts_ops']['create_index'](['content'])
            
            if result['ok']:
                return IndexSuccess(ok=True, message="FTS index created")
            else:
                return IndexError(ok=False, error=result['error'])
                
        except Exception as e:
            return IndexError(ok=False, error=str(e))
    
    def search_fts(query: str) -> SearchResult:
        """Search using Full Text Search"""
        start_time = time.time()
        
        try:
            if not query:
                return SearchError(ok=False, error="Empty query not allowed")
            
            if state['fts_ops'] is None:
                state['fts_ops'] = create_text_search(conn)
            
            # Search READMEs
            fts_result = state['fts_ops']['search'](query, False)
            
            if not fts_result['ok']:
                return SearchError(ok=False, error=fts_result['error'])
            
            # Convert to SearchHit format
            hits = []
            for result in fts_result['results']:
                # Get directory info
                dir_result = conn.execute(
                    "MATCH (d:Directory {path: $path}) RETURN d",
                    {'path': result.get('path', '')}
                )
                
                if dir_result.has_next():
                    row = dir_result.get_next()
                    dir_node = row[0]
                    
                    hit = SearchHit(
                        path=result.get('path', ''),
                        score=result.get('score', 0.0),
                        snippet=result.get('content', '')[:200],
                        has_readme=dir_node.get('has_readme', False)
                    )
                    hits.append(hit)
            
            duration_ms = (time.time() - start_time) * 1000
            
            return SearchSuccess(
                ok=True,
                hits=hits,
                total=len(hits),
                duration_ms=duration_ms
            )
            
        except Exception as e:
            return SearchError(ok=False, error=str(e))
    
    def search_vss(query: str, k: int) -> SearchResult:
        """Search using Vector Similarity Search"""
        start_time = time.time()
        
        try:
            if not query:
                return SearchError(ok=False, error="Empty query not allowed")
            
            # Initialize VSS if needed
            if state['embedder'] is None:
                state['embedder'] = create_embedder('all-MiniLM-L6-v2')
            if state['vss_ops'] is None:
                state['vss_ops'] = create_vector_search(conn, state['embedder'])
            
            # Search
            vss_result = state['vss_ops']['search'](query, k)
            
            if not vss_result['ok']:
                return SearchError(ok=False, error=vss_result['error'])
            
            # Convert to SearchHit format
            hits = []
            for result in vss_result['results']:
                hit = SearchHit(
                    path=result.get('id', ''),
                    score=result.get('score', 0.0),
                    snippet=result.get('content', '')[:200],
                    has_readme=True  # VSS only indexes READMEs
                )
                hits.append(hit)
            
            duration_ms = (time.time() - start_time) * 1000
            
            return SearchSuccess(
                ok=True,
                hits=hits,
                total=len(hits),
                duration_ms=duration_ms
            )
            
        except Exception as e:
            return SearchError(ok=False, error=str(e))
    
    def search_hybrid(query: str, alpha: float) -> SearchResult:
        """Hybrid search combining FTS and VSS"""
        try:
            # Get FTS results
            fts_result = search_fts(query)
            if not fts_result['ok']:
                return fts_result
            
            # Get VSS results
            vss_result = search_vss(query, 20)
            if not vss_result['ok']:
                return vss_result
            
            # Combine scores
            path_scores = {}
            
            # Add FTS scores
            for hit in fts_result['hits']:
                path_scores[hit['path']] = {
                    'fts_score': hit['score'],
                    'vss_score': 0.0,
                    'hit': hit
                }
            
            # Add VSS scores
            for hit in vss_result['hits']:
                if hit['path'] in path_scores:
                    path_scores[hit['path']]['vss_score'] = hit['score']
                else:
                    path_scores[hit['path']] = {
                        'fts_score': 0.0,
                        'vss_score': hit['score'],
                        'hit': hit
                    }
            
            # Calculate hybrid scores
            hits = []
            for path, scores in path_scores.items():
                hybrid_score = (alpha * scores['fts_score'] + 
                               (1 - alpha) * scores['vss_score'])
                hit = scores['hit']
                hit['score'] = hybrid_score
                hits.append(hit)
            
            # Sort by hybrid score
            hits.sort(key=lambda x: x['score'], reverse=True)
            
            result = SearchSuccess(
                ok=True,
                hits=hits[:10],  # Top 10
                total=len(hits),
                duration_ms=0.0
            )
            # Add hybrid info
            result['fts_weight'] = alpha  # type: ignore
            
            return result
            
        except Exception as e:
            return SearchError(ok=False, error=str(e))
    
    def extract_metadata(path: str) -> MetadataResult:
        """Extract metadata from directory"""
        try:
            # Check README first
            if readme := _get_readme_content(path):
                # Extract first paragraph as description
                lines = readme.strip().split('\n\n')
                desc = lines[1] if len(lines) > 1 else lines[0] if lines else ''
                # Remove markdown headers
                desc = re.sub(r'^#+\s*', '', desc)
                return MetadataSuccess(
                    ok=True,
                    description=desc[:200],
                    source='readme'
                )
            
            # Check flake.nix
            if desc := _extract_flake_description(path):
                return MetadataSuccess(
                    ok=True,
                    description=desc,
                    source='flake'
                )
            
            # Check package.json
            if desc := _extract_package_json_description(path):
                return MetadataSuccess(
                    ok=True,
                    description=desc,
                    source='package.json'
                )
            
            # Check Python docstring
            if desc := _extract_python_docstring(path):
                return MetadataSuccess(
                    ok=True,
                    description=desc,
                    source='docstring'
                )
            
            # No metadata found
            return MetadataSuccess(
                ok=True,
                description=None,
                source='none'
            )
            
        except Exception as e:
            return MetadataError(ok=False, error=str(e))
    
    def get_status() -> DBStatus:
        """Get database status"""
        try:
            # Count directories
            result = conn.execute("MATCH (d:Directory) RETURN COUNT(*)")
            total_dirs = result.get_next()[0] if result.has_next() else 0
            
            # Count indexed (with embeddings)
            result = conn.execute(
                "MATCH (d:Directory) WHERE d.embedding IS NOT NULL RETURN COUNT(*)"
            )
            indexed_dirs = result.get_next()[0] if result.has_next() else 0
            
            # Get DB file size
            db_size_mb = 0.0
            if db_path != ':memory:' and os.path.exists(db_path):
                db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
            
            return DBStatus(
                total_directories=total_dirs,
                indexed_directories=indexed_dirs,
                last_scan=datetime.now().isoformat() if state['last_scan'] else None,
                db_size_mb=db_size_mb
            )
            
        except Exception:
            return DBStatus(
                total_directories=0,
                indexed_directories=0,
                last_scan=None,
                db_size_mb=0.0
            )
    
    def check_embeddings() -> bool:
        """Check if embeddings exist in database"""
        try:
            result = conn.execute(
                "MATCH (d:Directory) WHERE d.embedding IS NOT NULL RETURN COUNT(*)"
            )
            count = result.get_next()[0] if result.has_next() else 0
            return count > 0
        except Exception:
            return False
    
    # Return all operations
    return {
        'full_scan': full_scan,
        'detect_changes': detect_changes,
        'incremental_update': incremental_update,
        'build_fts_index': build_fts_index,
        'search_fts': search_fts,
        'search_vss': search_vss,
        'search_hybrid': search_hybrid,
        'extract_metadata': extract_metadata,
        'get_status': get_status,
        'check_embeddings': check_embeddings,
    }


if __name__ == "__main__":
    print("This module should be run through the CLI interface.")
    print("Usage: uv run dirscan <command>")
    print("Run 'nix develop' first to enter the development environment.")
    sys.exit(1)