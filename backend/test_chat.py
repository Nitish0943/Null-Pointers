import requests
import json

def test_chat():
    url = "http://localhost:8000/chat"
    payload = {
        "message": "What is the current state of the machine?",
        "history": []
    }
    
    print(f"Sending message: {payload['message']}")
    try:
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            print(f"Error {r.status_code}: {r.text}")
            return
        data = r.json()
        print("\n--- RESPONSE ---")
        print(data["response"])
        print("\n--- CONTEXT USED ---")
        print(data["context_used"])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()
