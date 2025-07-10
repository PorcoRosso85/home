"""Mock objects for testing without database connection"""


class MockConnection:
    """Mock database connection for testing."""

    def __init__(self):
        self.executed_queries = []
        self._results = []
        self._result_index = 0

    def execute(self, query: str, params=None):
        """Mock execute method."""
        self.executed_queries.append((query, params))

        # Return mock result
        return MockResult(self._results[self._result_index] if self._result_index < len(self._results) else [])

    def set_results(self, results):
        """Set results for next query."""
        self._results = results
        self._result_index = 0


class MockResult:
    """Mock query result."""

    def __init__(self, rows):
        self.rows = rows
        self.index = 0

    def has_next(self):
        """Check if there are more results."""
        return self.index < len(self.rows)

    def get_next(self):
        """Get next result row."""
        if self.has_next():
            row = self.rows[self.index]
            self.index += 1
            return row
        return None
