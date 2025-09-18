# Templates Package

This package contains template implementations for the requirement/graph system.

## Available Templates

### search_requirements

Performs semantic search on requirements using hybrid search (vector similarity + keyword search).

**Input Format:**
```json
{
  "template": "search_requirements",
  "parameters": {
    "query": "search terms",
    "limit": 10
  }
}
```

**Parameters:**
- `query` (required): The search query string
- `limit` (optional): Maximum number of results to return (default: 10)

**Output Format:**
```json
{
  "status": "success",
  "query": "search terms",
  "count": 2,
  "results": [
    {
      "id": "req_001",
      "title": "Requirement Title",
      "content": "Requirement description",
      "score": 0.95,
      "source": "hybrid"
    }
  ]
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": {
    "type": "ErrorType",
    "message": "Error description"
  }
}
```

## Usage Example

```python
from application.templates import process_search_template

# Create search adapter factory
def search_factory():
    from application.search_adapter import SearchAdapter
    return SearchAdapter(db_path="/path/to/db")

# Execute search
result = process_search_template(
    {
        "query": "architecture requirements",
        "limit": 5
    },
    search_factory
)
```

## Integration with Template Processor

The search template is automatically available through the main template processor:

```python
from application.template_processor import process_template

result = process_template(
    {
        "template": "search_requirements",
        "parameters": {
            "query": "your search query"
        }
    },
    repository,
    search_factory
)
```