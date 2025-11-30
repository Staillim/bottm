import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

# Convertir URL de SQLAlchemy a URL de PostgreSQL pura para asyncpg
parsed = urlparse(DATABASE_URL)
pg_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}{parsed.path}"

async def test_connection():
    try:
        conn = await asyncpg.connect(pg_url)
        print("✅ Conexión exitosa a Supabase")
        # Probar una consulta simple
        result = await conn.fetchval("SELECT version()")
        print(f"Versión de PostgreSQL: {result}")
        await conn.close()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())