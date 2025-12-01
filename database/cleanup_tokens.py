"""
Script para limpiar tokens expirados de la base de datos
Ejecutar periódicamente (diario) para mantener la BD optimizada
"""
import asyncio
from datetime import datetime
from db_manager import DatabaseManager
from models import AdToken

async def cleanup_expired_tokens():
    """Elimina tokens expirados y antiguos de la base de datos"""
    db = DatabaseManager()
    await db.init_db()
    
    async with db.async_session() as session:
        # Obtener tokens expirados
        from sqlalchemy import select, delete
        
        result = await session.execute(
            select(AdToken).where(
                (AdToken.expires_at < datetime.utcnow()) |
                (AdToken.completed == True)  # Tokens completados también
            )
        )
        expired_tokens = result.scalars().all()
        
        if expired_tokens:
            print(f"🗑️ Eliminando {len(expired_tokens)} tokens expirados/completados...")
            
            # Eliminar tokens
            await session.execute(
                delete(AdToken).where(
                    (AdToken.expires_at < datetime.utcnow()) |
                    (AdToken.completed == True)
                )
            )
            await session.commit()
            print(f"✅ {len(expired_tokens)} tokens eliminados")
        else:
            print("✅ No hay tokens para limpiar")

if __name__ == "__main__":
    asyncio.run(cleanup_expired_tokens())
