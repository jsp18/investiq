import requests
import json

def test_optimize():
    url = "http://127.0.0.1:5000/api/optimize"
    data = {
        "symbols": ["RELIANCE.NS", "TCS.NS"],
        "amount": 100000,
        "risk_tolerance": "moderate"
    }
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_optimize()
