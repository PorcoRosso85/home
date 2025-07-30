"""KuzuDB graph database adapter."""

from pathlib import Path
from typing import Any


class GraphAdapter:
    """KuzuDB adapter for graph database operations."""

    def __init__(self, db_path: str):
        """Initialize adapter with database path.
        
        Args:
            db_path: Path to database directory or ':memory:' for in-memory DB
        """
        self.db_path = db_path
        self._db = None
        self._conn = None
        # In-memory data store for testing
        self._data = {
            "requirements": {},
            "tests": {},
            "relationships": [],
            "metrics": {}
        }
        self._initialize_connection()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()

    def close(self):
        """Close database connection."""
        if self._conn:
            # KuzuDB connections close automatically when garbage collected
            self._conn = None
        if self._db:
            self._db = None

    def _initialize_connection(self) -> None:
        """Initialize KuzuDB connection."""
        # Import database factory functions
        try:
            from persistence.kuzu_py import create_connection, create_database
        except ImportError:
            # Fallback to local implementation
            from .database_helper import create_connection, create_database

        # Create database
        db_result = create_database(self.db_path)
        if isinstance(db_result, dict) and db_result.get("type") in ["DatabaseError", "ValidationError"]:
            raise RuntimeError(f"Failed to create database: {db_result['message']}")
        self._db = db_result

        # Create connection
        conn_result = create_connection(self._db)
        if isinstance(conn_result, dict) and conn_result.get("type") in ["DatabaseError", "ValidationError"]:
            raise RuntimeError(f"Failed to create connection: {conn_result['message']}")
        self._conn = conn_result

        # Initialize schema if needed
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Ensure required schema exists."""
        try:
            # Check if schema exists
            result = self._conn.execute("MATCH (n:RequirementEntity) RETURN count(n) LIMIT 1")
            # Schema exists
        except Exception:
            # Need to create schema
            self._create_schema()

    def _create_schema(self) -> None:
        """Create initial schema."""
        schema_queries = [
            # Create node tables
            "CREATE NODE TABLE RequirementEntity(id STRING, title STRING, description STRING, status STRING, PRIMARY KEY(id))",
            "CREATE NODE TABLE TestSpecification(id STRING, test_type STRING, PRIMARY KEY(id))",
            "CREATE NODE TABLE MetricResult(id STRING, requirement_id STRING, metric_name STRING, value DOUBLE, timestamp STRING, PRIMARY KEY(id))",
            # Create edge tables
            "CREATE REL TABLE VERIFIED_BY(FROM RequirementEntity TO TestSpecification)",
            "CREATE REL TABLE DEPENDS_ON(FROM TestSpecification TO TestSpecification)",
            "CREATE REL TABLE HAS_METRIC(FROM RequirementEntity TO MetricResult)"
        ]

        for query in schema_queries:
            try:
                self._conn.execute(query)
            except Exception as e:
                # Table might already exist
                if "already exists" not in str(e):
                    raise

    def get_requirement(self, requirement_id: str) -> dict[str, Any] | None:
        """Get requirement by ID.
        
        Args:
            requirement_id: The requirement ID to look up
            
        Returns:
            Requirement dict or None if not found
        """
        try:
            result = self._conn.execute(
                "MATCH (r:RequirementEntity {id: $id}) RETURN r",
                {"id": requirement_id}
            )

            if result.has_next():
                row = result.get_next()
                node = row[0]
                return {
                    "id": node["id"],
                    "title": node["title"],
                    "description": node["description"],
                    "status": node["status"]
                }
            return None

        except Exception:
            # Log error and return None
            return None

    def get_tests_for_requirement(self, requirement_id: str) -> list[dict[str, Any]]:
        """Get all tests for a requirement.
        
        Args:
            requirement_id: The requirement ID
            
        Returns:
            List of test specifications
        """
        try:
            result = self._conn.execute("""
                MATCH (r:RequirementEntity {id: $id})-[:VERIFIED_BY]->(t:TestSpecification)
                RETURN t
            """, {"id": requirement_id})

            tests = []
            while result.has_next():
                row = result.get_next()
                node = row[0]
                tests.append({
                    "id": node["id"],
                    "test_type": node["test_type"]
                })

            return tests

        except Exception:
            return []

    def get_dependencies(self, test_id: str) -> dict[str, list[str]]:
        """Get test dependencies.
        
        Args:
            test_id: The test ID
            
        Returns:
            Dict mapping test_id to list of dependency IDs
        """
        try:
            result = self._conn.execute("""
                MATCH (t:TestSpecification {id: $id})-[:DEPENDS_ON]->(dep:TestSpecification)
                RETURN dep.id
            """, {"id": test_id})

            dependencies = {test_id: []}
            while result.has_next():
                row = result.get_next()
                dependencies[test_id].append(row[0])

            return dependencies

        except Exception:
            return {test_id: []}

    def save_metric_result(self, requirement_id: str, metric_name: str, result: dict[str, Any]) -> None:
        """Save metric calculation result.
        
        Args:
            requirement_id: The requirement ID
            metric_name: Name of the metric
            result: Metric calculation result
        """
        # Save to in-memory store
        if requirement_id not in self._data["metrics"]:
            self._data["metrics"][requirement_id] = {}
        self._data["metrics"][requirement_id][metric_name] = result

        try:
            import datetime
            metric_id = f"metric_{requirement_id}_{metric_name}_{datetime.datetime.now().isoformat()}"

            # Create metric result node
            self._conn.execute("""
                CREATE (m:MetricResult {
                    id: $id,
                    requirement_id: $req_id,
                    metric_name: $name,
                    value: $value,
                    timestamp: $timestamp
                })
            """, {
                "id": metric_id,
                "req_id": requirement_id,
                "name": metric_name,
                "value": result.get("value", 0.0),
                "timestamp": datetime.datetime.now().isoformat()
            })

            # Create relationship
            self._conn.execute("""
                MATCH (r:RequirementEntity {id: $req_id})
                MATCH (m:MetricResult {id: $metric_id})
                CREATE (r)-[:HAS_METRIC]->(m)
            """, {
                "req_id": requirement_id,
                "metric_id": metric_id
            })

        except Exception:
            pass

    def get_metric_history(self, requirement_id: str, metric_name: str) -> list[dict[str, Any]]:
        """Get historical metric values.
        
        Args:
            requirement_id: The requirement ID
            metric_name: Name of the metric
            
        Returns:
            List of historical metric values
        """
        try:
            result = self._conn.execute("""
                MATCH (r:RequirementEntity {id: $req_id})-[:HAS_METRIC]->(m:MetricResult {metric_name: $name})
                RETURN m
                ORDER BY m.timestamp DESC
            """, {
                "req_id": requirement_id,
                "name": metric_name
            })

            history = []
            while result.has_next():
                row = result.get_next()
                node = row[0]
                history.append({
                    "value": node["value"],
                    "timestamp": node["timestamp"]
                })

            return history

        except Exception:
            return []

    def execute_cypher(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            
        Returns:
            List of result rows as dicts
        """
        try:
            result = self._conn.execute(query, parameters or {})

            rows = []
            while result.has_next():
                row = result.get_next()
                # Convert row to dict - this is simplified
                # In practice, would need proper column mapping
                rows.append({f"col{i}": val for i, val in enumerate(row)})

            return rows

        except Exception:
            return []

    def export_to_cypher(self, output_file: str) -> None:
        """Export current state to Cypher file.
        
        Args:
            output_file: Path to output Cypher file
        """
        try:
            cypher_lines = []

            # Export requirements
            req_result = self._conn.execute("MATCH (r:RequirementEntity) RETURN r")
            while req_result.has_next():
                node = req_result.get_next()[0]
                cypher_lines.append(
                    f"CREATE (r:RequirementEntity {{id: '{node['id']}', "
                    f"title: '{node['title']}', "
                    f"description: '{node['description']}', "
                    f"status: '{node['status']}'}});"
                )

            # Export tests
            test_result = self._conn.execute("MATCH (t:TestSpecification) RETURN t")
            while test_result.has_next():
                node = test_result.get_next()[0]
                cypher_lines.append(
                    f"CREATE (t:TestSpecification {{id: '{node['id']}', "
                    f"test_type: '{node['test_type']}'}});"
                )

            # Export VERIFIED_BY relationships
            rel_result = self._conn.execute(
                "MATCH (r:RequirementEntity)-[:VERIFIED_BY]->(t:TestSpecification) "
                "RETURN r.id, t.id"
            )
            while rel_result.has_next():
                row = rel_result.get_next()
                cypher_lines.append(
                    f"MATCH (r:RequirementEntity {{id: '{row[0]}'}}), "
                    f"(t:TestSpecification {{id: '{row[1]}'}})"
                    f"CREATE (r)-[:VERIFIED_BY]->(t);"
                )

            # Export DEPENDS_ON relationships
            dep_result = self._conn.execute(
                "MATCH (t1:TestSpecification)-[:DEPENDS_ON]->(t2:TestSpecification) "
                "RETURN t1.id, t2.id"
            )
            while dep_result.has_next():
                row = dep_result.get_next()
                cypher_lines.append(
                    f"MATCH (t1:TestSpecification {{id: '{row[0]}'}}), "
                    f"(t2:TestSpecification {{id: '{row[1]}'}})"
                    f"CREATE (t1)-[:DEPENDS_ON]->(t2);"
                )

            # Write to file
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(cypher_lines))

        except Exception:
            pass

    def begin_transaction(self):
        """Begin a new transaction.
        
        Note: KuzuDB auto-commits by default. This is for explicit transaction control.
        """
        try:
            self._conn.begin_transaction()
        except Exception:
            pass

    def commit(self):
        """Commit the current transaction."""
        try:
            self._conn.commit()
        except Exception:
            pass

    def rollback(self):
        """Rollback the current transaction."""
        try:
            self._conn.rollback()
        except Exception:
            pass

    def _load_data(self) -> dict[str, Any]:
        """Load data from in-memory store (for testing).
        
        Returns:
            Dict with requirements, tests, relationships, and metrics
        """
        return self._data

    def _save_data(self, data: dict[str, Any]) -> None:
        """Save data to in-memory store and sync with database (for testing).
        
        Args:
            data: Dict with requirements, tests, relationships, and metrics
        """
        self._data = data

        # Sync to actual database
        try:
            # Clear existing data
            self._conn.execute("MATCH (n) DETACH DELETE n")

            # Add requirements
            for req_id, req_data in data.get("requirements", {}).items():
                self._conn.execute("""
                    CREATE (r:RequirementEntity {
                        id: $id,
                        title: $title,
                        description: $description,
                        status: $status
                    })
                """, {
                    "id": req_id,
                    "title": req_data.get("title", ""),
                    "description": req_data.get("description", ""),
                    "status": req_data.get("status", "active")
                })

            # Add tests
            for test_id, test_data in data.get("tests", {}).items():
                self._conn.execute("""
                    CREATE (t:TestSpecification {
                        id: $id,
                        test_type: $test_type
                    })
                """, {
                    "id": test_id,
                    "test_type": test_data.get("test_type", "unit")
                })

            # Add relationships
            for rel in data.get("relationships", []):
                if rel["type"] == "VERIFIED_BY":
                    self._conn.execute("""
                        MATCH (r:RequirementEntity {id: $from})
                        MATCH (t:TestSpecification {id: $to})
                        CREATE (r)-[:VERIFIED_BY]->(t)
                    """, {
                        "from": rel["from"],
                        "to": rel["to"]
                    })
                elif rel["type"] == "DEPENDS_ON":
                    self._conn.execute("""
                        MATCH (t1:TestSpecification {id: $from})
                        MATCH (t2:TestSpecification {id: $to})
                        CREATE (t1)-[:DEPENDS_ON]->(t2)
                    """, {
                        "from": rel["from"],
                        "to": rel["to"]
                    })

        except Exception:
            pass
