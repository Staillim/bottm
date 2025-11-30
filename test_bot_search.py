import asyncio
from database.db_manager import DatabaseManager
from utils.verification import is_user_member
from telegram.ext import ContextTypes
from unittest.mock import MagicMock

class MockBot:
    def __init__(self):
        self.bot_data = {'db': None}

    async def get_chat_member(self, chat_id, user_id):
        # Simular que el usuario está verificado
        from telegram import ChatMember
        member = MagicMock()
        member.status = ChatMember.MEMBER
        return member

class MockContext:
    def __init__(self, bot):
        self.bot = bot

async def simulate_search_command(query, user_id=12345):
    """Simula exactamente lo que hace el comando /buscar"""
    print(f"🔍 Simulando búsqueda: '{query}' para usuario {user_id}")

    # Crear mock del bot y contexto
    mock_bot = MockBot()
    mock_context = MockContext(mock_bot)

    # Inicializar base de datos
    db = DatabaseManager()
    await db.init_db()
    mock_bot.bot_data['db'] = db

    # Paso 1: Verificar membresía
    print("1. Verificando membresía...")
    is_member = await is_user_member(user_id, mock_context)
    print(f"   Usuario verificado: {is_member}")

    if not is_member:
        print("❌ Usuario no verificado - búsqueda bloqueada")
        return

    # Paso 2: Buscar videos
    print("2. Buscando videos...")
    videos = await db.search_videos(query)
    print(f"   Videos encontrados: {len(videos)}")

    if not videos:
        print(f"😔 No se encontraron resultados para: '{query}'")
        return

    # Paso 3: Mostrar resultados
    print("3. Resultados:")
    for idx, video in enumerate(videos, 1):
        print(f"   {idx}. {video.title}")

    return videos

async def test_simulations():
    try:
        # Probar búsquedas que deberían funcionar
        test_queries = ["hulk", "cadáver", "ahora"]

        for query in test_queries:
            print(f"\n{'='*50}")
            await simulate_search_command(query)
            print()

    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simulations())