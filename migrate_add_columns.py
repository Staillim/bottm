"""
Script de migración para agregar columnas expires_at e ip_address a la tabla ad_tokens
"""
import asyncio
from sqlalchemy import text
from database.db_manager import DatabaseManager
from config.settings import DATABASE_URL

async def migrate():
    """Agrega las columnas faltantes a ad_tokens"""
    db = DatabaseManager()
    
    try:
        async with db.engine.begin() as conn:
            # Verificar si las columnas ya existen
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'ad_tokens' 
                AND column_name IN ('expires_at', 'ip_address')
            """))
            
            existing_columns = [row[0] for row in result]
            
            # Agregar expires_at si no existe
            if 'expires_at' not in existing_columns:
                print("Agregando columna expires_at...")
                await conn.execute(text("""
                    ALTER TABLE ad_tokens 
                    ADD COLUMN expires_at TIMESTAMP WITHOUT TIME ZONE
                """))
                print("✅ Columna expires_at agregada")
            else:
                print("✓ Columna expires_at ya existe")
            
            # Agregar ip_address si no existe
            if 'ip_address' not in existing_columns:
                print("Agregando columna ip_address...")
                await conn.execute(text("""
                    ALTER TABLE ad_tokens 
                    ADD COLUMN ip_address VARCHAR(50)
                """))
                print("✅ Columna ip_address agregada")
            else:
                print("✓ Columna ip_address ya existe")
        
        print("\n✅ Migración completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
    finally:
        await db.engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
