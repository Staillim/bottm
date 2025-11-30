import asyncio
import requests
from database.db_manager import DatabaseManager

async def test_ad_endpoint():
    """Prueba el endpoint de anuncios para diagnosticar el problema"""
    print("🧪 Probando endpoint de anuncios")
    print("=" * 50)

    try:
        # Inicializar base de datos
        db = DatabaseManager()
        await db.init_db()
        print("✅ Base de datos inicializada")

        # Crear un token de prueba
        print("\n1. Creando token de prueba...")
        token = await db.create_ad_token(user_id=12345, video_id=38)  # Usando video existente
        print(f"   Token creado: {token[:20]}...")

        # Verificar que el token existe
        print("\n2. Verificando token...")
        ad_token = await db.get_ad_token(token)
        if ad_token:
            print(f"   ✅ Token encontrado: user_id={ad_token.user_id}, video_id={ad_token.video_id}, completed={ad_token.completed}")
        else:
            print("   ❌ Token no encontrado")
            return

        # Probar el endpoint (simulando la petición de la webapp)
        print("\n3. Probando endpoint /api/ad-completed...")
        api_url = "http://localhost:5000"  # Cambiar si es diferente

        payload = {
            "token": token,
            "user_id": 12345
        }

        try:
            response = requests.post(f"{api_url}/api/ad-completed", json=payload, timeout=30)
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error en petición: {e}")
            print("   💡 El servidor Flask no está corriendo o no es accesible")

        # Verificar si el token se marcó como completado
        print("\n4. Verificando si token se completó...")
        ad_token_after = await db.get_ad_token(token)
        if ad_token_after:
            print(f"   Completed: {ad_token_after.completed}")
            if ad_token_after.completed_at:
                print(f"   Completed at: {ad_token_after.completed_at}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ad_endpoint())