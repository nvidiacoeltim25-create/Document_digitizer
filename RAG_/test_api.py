import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_chat(query: str, top_k: int = 5):
    """Test the chat endpoint"""
    try:
        payload = {
            "query": query,
            "top_k": top_k
        }
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        print(f"\nChat Request: {response.status_code}")
        result = response.json()
        print(f"Query: {result['query']}")
        print(f"Response: {result['response']}")
        print(f"Context Found: {result['context_found']}")
        return response.status_code == 200
    except Exception as e:
        print(f"Chat request failed: {e}")
        return False

def test_retrieve(query: str, top_k: int = 5):
    """Test the retrieve endpoint"""
    try:
        payload = {
            "query": query,
            "top_k": top_k
        }
        response = requests.post(f"{BASE_URL}/retrieve", json=payload)
        print(f"\nRetrieve Request: {response.status_code}")
        result = response.json()
        print(f"Query: {result['query']}")
        print(f"Context Count: {result['context_count']}")
        print(f"Context: {result['context'][:2]}...")  # Show first 2 results
        return response.status_code == 200
    except Exception as e:
        print(f"Retrieve request failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing RAG Chatbot API...")
    
    # Test health
    if test_health():
        print("✅ Health check passed")
    else:
        print("❌ Health check failed")
        exit(1)
    
    # Test sample queries
    test_queries = [
        "Who signed the document?",
        "What is the main topic of the document?",
        "Can you summarize the key points?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Testing Query: {query}")
        print(f"{'='*50}")
        
        # Test chat endpoint
        test_chat(query)
        
        # Test retrieve endpoint
        test_retrieve(query)