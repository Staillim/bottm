"""
Script de prueba para verificar que el bot responde
"""
import asyncio
from telegram import Bot
from config.settings import BOT_TOKEN

async def test_bot():
    bot = Bot(token=BOT_TOKEN)
    
    # Verificar info del bot
    me = await bot.get_me()
    print(f"✅ Bot conectado: @{me.username}")
    print(f"   ID: {me.id}")
    print(f"   Nombre: {me.first_name}")
    
    # Verificar webhooks
    webhook_info = await bot.get_webhook_info()
    print(f"\n📡 Webhook Info:")
    print(f"   URL: {webhook_info.url or 'No configurado'}")
    print(f"   Updates pendientes: {webhook_info.pending_update_count}")
    
    # Verificar últimas actualizaciones
    try:
        updates = await bot.get_updates(limit=5)
        print(f"\n📬 Últimas {len(updates)} actualizaciones:")
        for update in updates:
            print(f"   Update ID: {update.update_id}")
            if update.message:
                print(f"      Mensaje de: {update.message.from_user.username}")
                print(f"      Texto: {update.message.text}")
    except Exception as e:
        print(f"\n⚠️ Error obteniendo updates: {e}")
    
    await bot.shutdown()

if __name__ == '__main__':
    asyncio.run(test_bot())
