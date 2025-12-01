import asyncio
from telegram import Bot
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID, VERIFICATION_CHANNEL_ID
import os

async def test_channel_access():
    try:
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        print(f"🤖 Bot: @{bot_info.username} (ID: {bot_info.id})")
        
        print(f"\n📺 STORAGE_CHANNEL_ID: {STORAGE_CHANNEL_ID}")
        print(f"📺 VERIFICATION_CHANNEL_ID: {VERIFICATION_CHANNEL_ID}")
        print(f"📺 VERIFICATION_CHANNEL_ID (env raw): {repr(os.getenv('VERIFICATION_CHANNEL_ID'))}")

        # Test VERIFICATION channel
        print(f"\n{'='*50}")
        print(f"TESTEANDO CANAL DE VERIFICACIÓN")
        print(f"{'='*50}")
        try:
            chat = await bot.get_chat(VERIFICATION_CHANNEL_ID)
            print(f"✅ Canal encontrado: {chat.title}")
            print(f"📝 Tipo: {chat.type}")
            print(f"👥 Username: @{chat.username if chat.username else 'N/A'}")
            
            # Verificar permisos del bot
            member = await bot.get_chat_member(VERIFICATION_CHANNEL_ID, bot_info.id)
            print(f"\n🔐 Status del bot: {member.status}")
            
            if member.status == 'administrator':
                print(f"   ✅ Can post messages: {member.can_post_messages}")
                print(f"   ✅ Can edit messages: {member.can_edit_messages}")
                print(f"   ✅ Can delete messages: {member.can_delete_messages}")
            elif member.status == 'member':
                print(f"   ⚠️  Bot es solo MIEMBRO, necesita ser ADMINISTRADOR!")
                print(f"   Para publicar, agrégalo como admin con permiso 'Post Messages'")
            else:
                print(f"   ❌ Status: {member.status}")
                
        except Exception as e:
            print(f"❌ Error al acceder al canal de verificación: {e}")
            import traceback
            traceback.print_exc()

        # Test STORAGE channel
        print(f"\n{'='*50}")
        print(f"TESTEANDO CANAL DE STORAGE")
        print(f"{'='*50}")
        try:
            chat = await bot.get_chat(STORAGE_CHANNEL_ID)
            print(f"✅ Canal encontrado: {chat.title}")
            print(f"📝 Tipo: {chat.type}")
        except Exception as e:
            print(f"❌ Error al acceder al canal de storage: {e}")

    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    asyncio.run(test_channel_access())