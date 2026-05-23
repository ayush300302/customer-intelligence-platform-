import os
import requests
import json
import time

# Metrics endpoint URL
METRICS_URL = "http://127.0.0.1:8000/metrics"

def monitor_rag_performance():
    print("Connecting to live FastAPI metrics endpoint...")
    try:
        response = requests.get(METRICS_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            print("\n=============================================")
            print("   RAG Performance & Telemetry Dashboard     ")
            print("=============================================")
            print(f"Total API Requests: {data['request_count']}")
            print(f"Total API Errors  : {data['error_count']}")
            
            print("\n[Endpoint Latencies (Average)]")
            for endpoint, val in data["latency"].items():
                print(f"  - /{endpoint:<15} : {val*1000:>6.2f} ms")
                
            print("\n[ML Classifier Predictions]")
            for k, v in data["prediction_distribution"].items():
                decision = "subscribe" if k == "1" else "no_subscribe"
                print(f"  - {decision:<15} : {v:>4} predictions")
                
            print("\n[LLM/RAG Metrics]")
            stats = data["rag_retrieval_stats"]
            print(f"  - Retrieval Hit Rate  : {stats['hit_rate']*100:.1f}%")
            print(f"  - Refusal Rate        : {stats['refusal_rate']*100:.1f}%")
            print(f"  - Avg Top-K Similarity: {stats['avg_top_k_score']:.4f}")
            print(f"  - Est. Tokens Spent   : {stats['total_tokens']}")
            print("=============================================\n")
            
        else:
            print(f"Failed to fetch metrics: HTTP {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Error: FastAPI server is not running locally. Please start the server using:")
        print("  uvicorn src.serving.serve:app --reload")
    except Exception as e:
        print(f"Error checking RAG metrics: {str(e)}")

if __name__ == "__main__":
    monitor_rag_performance()
