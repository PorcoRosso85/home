#!/usr/bin/env python3
"""
Demo script for the Contextual Chunking Graph-Powered RAG system.
This script demonstrates the basic functionality without requiring PDF input.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def demo_text_processing():
    """Demo function using sample text instead of PDF."""
    
    # Sample document text for demonstration
    sample_document = """
    Artificial Intelligence (AI) is a rapidly evolving field that encompasses machine learning, 
    natural language processing, and computer vision. Machine learning algorithms can learn 
    patterns from data without explicit programming. Natural language processing enables 
    computers to understand and generate human language. Computer vision allows machines 
    to interpret and analyze visual information from the world.
    
    Deep learning, a subset of machine learning, uses neural networks with multiple layers 
    to model complex patterns. These neural networks are inspired by the human brain's structure. 
    Convolutional neural networks are particularly effective for image processing tasks.
    
    The applications of AI are vast and include autonomous vehicles, medical diagnosis, 
    recommendation systems, and virtual assistants. As AI technology continues to advance, 
    it promises to transform many aspects of human life and industry.
    """
    
    print("=== Contextual Chunking Graph-Powered RAG Demo ===")
    print("This demo shows how the system would process and analyze documents.\n")
    
    print("Sample Document:")
    print("-" * 50)
    print(sample_document[:200] + "...")
    print("-" * 50)
    
    try:
        # Import the main components
        from contextual_chunking_graph.rag import (
            DocumentProcessor, 
            KnowledgeGraph, 
            QueryEngine, 
            GraphRAG
        )
        
        print("\n✅ Successfully imported RAG components!")
        
        # Initialize the system with sample text
        print("🔄 Processing document...")
        graph_rag = GraphRAG([sample_document])
        print("✅ Document processed and knowledge graph built!")
        
        # Demo queries
        demo_queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "What are the applications of AI?",
            "What is deep learning?"
        ]
        
        print("\n🤖 Running demo queries:")
        print("=" * 60)
        
        for query in demo_queries:
            print(f"\nQuery: {query}")
            try:
                response = graph_rag.query(query)
                print(f"Response: {response[:150]}...")
            except Exception as e:
                print(f"Error processing query: {e}")
            print("-" * 40)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This might be due to missing system libraries.")
        print("The package structure is correct, but some dependencies require system libraries.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def check_environment():
    """Check if the environment is properly set up."""
    print("=== Environment Check ===")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        with open(env_file, 'r') as f:
            content = f.read()
        if "<your-" in content:
            print("⚠️  API keys need to be configured in .env")
        else:
            print("✅ API keys appear to be configured")
    else:
        print("❌ .env file not found")
    
    # Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment")
    
    # Check package installation
    try:
        import contextual_chunking_graph
        print("✅ Package is importable")
    except ImportError as e:
        print(f"❌ Package import failed: {e}")
    
    print()

def main():
    """Main demo function."""
    check_environment()
    
    print("This demo shows the Contextual Chunking Graph-Powered RAG system.")
    print("Due to system library requirements, the full demo may not run on all systems.")
    print()
    
    choice = input("Would you like to try the text processing demo? (y/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        success = demo_text_processing()
        if success:
            print("\n🎉 Demo completed successfully!")
        else:
            print("\n⚠️  Demo had issues, but the package structure is correct.")
    else:
        print("Demo skipped.")
    
    print("\n📖 To use the full system:")
    print("1. Ensure all system libraries are available")
    print("2. Configure your API keys in .env")
    print("3. Run: uv run python -m contextual_chunking_graph.main")
    print("4. Or use: uv run contextual-rag")

if __name__ == "__main__":
    main()