"""
Demonstration of Embedding-based Semantic Search for References
Shows how embeddings enable finding similar references by meaning, not just keywords
"""
from embed_pkg.embedding_repository import create_embedding_repository
from asvs_reference.reference_repository import DatabaseError, ValidationError
import json


def print_separator(title: str = ""):
    """Print a section separator"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}\n")


def print_reference(ref: dict, score: float = None):
    """Pretty print a reference"""
    print(f"URI: {ref['uri']}")
    print(f"Title: {ref['title']}")
    if ref.get('description'):
        print(f"Description: {ref['description']}")
    if score is not None:
        print(f"Similarity Score: {score:.3f}")
    print()


def main():
    """Demonstrate embedding-based semantic search capabilities"""
    print_separator("Embedding Similarity Demo - Semantic Reference Search")
    
    # Step 1: Create an embedding-enabled repository
    print("1. Creating embedding repository with sentence transformer model...")
    repo = create_embedding_repository(
        db_path=":memory:",
        model_name="all-MiniLM-L6-v2"  # Small, fast model for demos
    )
    
    if isinstance(repo, dict) and repo.get("type") == "DatabaseError":
        print(f"Error creating repository: {repo['message']}")
        return
    
    print("✓ Repository created successfully")
    
    # Step 2: Add references with meaningful descriptions
    print_separator("2. Adding References with Descriptions")
    
    references = [
        {
            "uri": "req:auth:secure-login",
            "title": "Secure Login Implementation",
            "description": "Users must authenticate using strong passwords with multi-factor authentication support",
            "entity_type": "requirement"
        },
        {
            "uri": "req:auth:password-policy",
            "title": "Password Complexity Requirements",
            "description": "Passwords must be at least 12 characters with uppercase, lowercase, numbers, and symbols",
            "entity_type": "requirement"
        },
        {
            "uri": "req:data:encryption",
            "title": "Data Encryption at Rest",
            "description": "All sensitive user information must be encrypted using AES-256 when stored in the database",
            "entity_type": "requirement"
        },
        {
            "uri": "req:api:rate-limiting",
            "title": "API Rate Limiting",
            "description": "Implement throttling to prevent abuse and ensure fair usage of API endpoints",
            "entity_type": "requirement"
        },
        {
            "uri": "req:logging:security-events",
            "title": "Security Event Logging",
            "description": "Log all authentication attempts, access control decisions, and security-relevant actions",
            "entity_type": "requirement"
        }
    ]
    
    for ref in references:
        result = repo["save_with_embedding"](ref)
        if isinstance(result, dict) and result.get("type") in ["DatabaseError", "ValidationError"]:
            print(f"✗ Error saving {ref['uri']}: {result['message']}")
        else:
            print(f"✓ Saved: {ref['uri']} - {ref['title']}")
    
    # Step 3: Demonstrate semantic search capabilities
    print_separator("3. Semantic Search Demonstrations")
    
    # Test queries that showcase semantic understanding
    test_queries = [
        {
            "query": "user authentication and verification",
            "expected": ["req:auth:secure-login", "req:auth:password-policy"],
            "explanation": "Finds authentication-related requirements even without exact keyword matches"
        },
        {
            "query": "protect sensitive data storage",
            "expected": ["req:data:encryption"],
            "explanation": "Understands 'protect' relates to encryption and security"
        },
        {
            "query": "prevent API abuse and overload",
            "expected": ["req:api:rate-limiting"],
            "explanation": "Connects 'abuse' and 'overload' to rate limiting concept"
        },
        {
            "query": "audit trail and compliance tracking",
            "expected": ["req:logging:security-events"],
            "explanation": "Links 'audit trail' to security event logging"
        }
    ]
    
    for test in test_queries:
        print(f"Query: '{test['query']}'")
        print(f"({test['explanation']})")
        print()
        
        # Find similar references
        results = repo["find_similar_by_text"](test["query"], limit=3)
        
        if isinstance(results, dict) and results.get("type") == "ValidationError":
            print(f"Error: {results['message']}")
            continue
        
        print("Top matches:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['uri']} (score: {result['similarity_score']:.3f})")
            print(f"     {result['title']}")
        
        print()
    
    # Step 4: Show cross-domain semantic connections
    print_separator("4. Cross-Domain Semantic Connections")
    
    print("Query: 'security best practices'")
    print("(Should find multiple security-related requirements across domains)")
    print()
    
    results = repo["find_similar_by_text"]("security best practices", limit=5)
    
    print("Found connections across different requirement areas:")
    for result in results:
        domain = result['uri'].split(':')[1]
        print(f"  - [{domain}] {result['title']} (score: {result['similarity_score']:.3f})")
    
    # Step 5: Demonstrate advantage over keyword search
    print_separator("5. Semantic vs Keyword Search Comparison")
    
    print("Semantic Query: 'prevent unauthorized access'")
    semantic_results = repo["find_similar_by_text"]("prevent unauthorized access", limit=3)
    
    print("\nSemantic search results:")
    for result in semantic_results:
        print(f"  ✓ {result['uri']} - {result['title']}")
        print(f"    Relevance: {result['similarity_score']:.3f}")
    
    print("\nKeyword search would miss these connections because:")
    print("  - 'prevent' doesn't appear in 'Secure Login Implementation'")
    print("  - 'unauthorized' doesn't appear in 'Password Complexity Requirements'")
    print("  - But semantically, both are about access control!")
    
    print_separator()
    print("Summary: Embeddings enable finding references by meaning, not just keywords.")
    print("This allows for more intuitive discovery of related requirements and better")
    print("traceability across your system.")


if __name__ == "__main__":
    main()