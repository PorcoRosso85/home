"""
Templates package for requirement/graph application layer

Available templates:
- search_requirements: Semantic search functionality for requirements
"""
from .search_requirements import process_search_template, search_requirements

__all__ = ["process_search_template", "search_requirements"]