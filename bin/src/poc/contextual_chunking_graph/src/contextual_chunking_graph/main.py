#!/usr/bin/env python3
"""
Main entry point for the Contextual Chunking Graph-Powered RAG system.
"""

import os
import logging
from .rag import GraphRAG, load_pdf_with_llama_parse


def main():
    """Main function to run the RAG system."""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=== Contextual Chunking Graph-Powered RAG System ===")
    print("This system combines semantic and keyword search with knowledge graphs")
    print("for enhanced document retrieval and question answering.\n")
    
    # Load the PDF document
    pdf_path = input("Enter the path to your PDF file: ")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} does not exist.")
        return
    
    try:
        print("Loading and parsing document...")
        document = load_pdf_with_llama_parse(pdf_path)
        print("Document loaded successfully!")
    except Exception as e:
        logging.error(f"Failed to load or parse the PDF: {str(e)}")
        print(f"Error: {str(e)}")
        return

    # Initialize and process the document
    print("Building knowledge graph and vector store...")
    try:
        graph_rag = GraphRAG([document])
        print("System ready for queries!")
    except Exception as e:
        logging.error(f"Failed to initialize RAG system: {str(e)}")
        print(f"Error: {str(e)}")
        return

    # Query loop
    print("\nYou can now ask questions about the document.")
    print("Type 'exit' to quit.\n")
    
    while True:
        try:
            query = input("Enter your query: ").strip()
            if query.lower() in ['exit', 'quit', 'q']:
                break
            
            if not query:
                print("Please enter a valid query.")
                continue
            
            print("Processing query...")
            response = graph_rag.query(query)
            print(f"\nResponse: {response}\n")
            print("-" * 80)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logging.error(f"Error processing query: {str(e)}")
            print(f"Error: {str(e)}")

    print("Thank you for using the Contextual Chunking Graph-Powered RAG system!")


if __name__ == "__main__":
    main()