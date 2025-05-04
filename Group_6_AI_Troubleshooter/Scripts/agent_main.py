"""
Main entry point for the multi-agent RAG system.
"""
import os
import sys
import json
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

from agents.orchestrator import Orchestrator


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Multi-Agent RAG System")
    parser.add_argument('--index_path', type=str, required=True, 
                        help='Path to existing FAISS index')
    parser.add_argument('--query', type=str, 
                        default="Error: Cannot connect to target 'TargetPC1': Cannot connect to target.",
                        help='Query to be processed')
    parser.add_argument('--model', type=str, default="gpt-4o-mini",
                        help='LLM model to use')
    parser.add_argument('--image', type=str, default=None,
                        help='Path to image file to analyze')
    return parser.parse_args()


def setup_environment():
    """Setup environment variables and API keys"""
    # Load environment variables
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')

    # Configure Google API
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if google_api_key:
        genai.configure(api_key=google_api_key)
    else:
        print("Warning: GOOGLE_API_KEY not found in environment variables.")
        
    # Validate OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        sys.exit(1)


def print_result(result):
    """Pretty print the result"""
    print("\n--- Final Output ---")
    
    print("\nResponse:")
    print(result.final_response)
    
    if result.reference_links:
        print("\nReference Links:")
        for ref in result.reference_links:
            print(f"- {ref.title}: {ref.url}")
    else:
        print("\nReference Links: None")
    
    if result.relevant_docs:
        print("\nRelevant Documents:")
        for i, doc in enumerate(sorted(result.relevant_docs, key=lambda x: x.score, reverse=True)):
            print(f"\n[{i+1}] Score: {doc.score:.2f}")
            print(f"URL: {doc.url}")
            print(f"Preview: {doc.content_preview}")
    else:
        print("\nRelevant Documents: None")
    print("\nJSON Output:")
    print(json.dumps(result.model_dump(), indent=2))


def main():
    # Parse command line arguments
    args = parse_args()
    
    # Setup environment
    setup_environment()
    
    print(f"Initializing RAG system with index path: {args.index_path}")
    
    # Create orchestrator
    orchestrator = Orchestrator(
        faiss_index_path=args.index_path,
        model=args.model
    )
    
    # Load image if provided
    image_bytes = None
    if args.image and os.path.exists(args.image):
        print(f"Loading image from {args.image}")
        with open(args.image, 'rb') as f:
            image_bytes = f.read()
    
    # Process query
    result = orchestrator.run(args.query, image_bytes)
    
    # Print result
    print_result(result)


if __name__ == "__main__":
    main()