"""
Script para limpiar webhook y conflictos de polling en Telegram
"""
import asyncio
from telegram import Bot
from config.settings import BOT_TOKEN

async def clear_webhook():
    bot = Bot(token=BOT_TOKEN)
    
    # Eliminar webhook si existe
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook eliminado y actualizaciones pendientes descartadas")
    
    # Obtener info del bot
    me = await bot.get_me()
    print(f"🤖 Bot: @{me.username}")
    
    await bot.close()

if __name__ == "__main__":
    asyncio.run(clear_webhook())
