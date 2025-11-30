import requests

def test_endpoint():
    """Solo probar el endpoint sin inicializar BD"""
    print("🧪 Probando solo el endpoint /api/ad-completed")

    # Token de prueba (creado manualmente para esta prueba)
    token = "test_token_123"

    payload = {
        "token": token,
        "user_id": 12345
    }

    try:
        response = requests.post("http://localhost:5000/api/ad-completed", json=payload, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_endpoint()