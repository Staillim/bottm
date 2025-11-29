from telegram import ChatMember
from telegram.ext import ContextTypes
from config.settings import VERIFICATION_CHANNEL_ID

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Verifica si el usuario es miembro del canal"""
    try:
        member = await context.bot.get_chat_member(
            chat_id=VERIFICATION_CHANNEL_ID,
            user_id=user_id
        )
        return member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER
        ]
    except Exception as e:
        print(f"Error verificando membresía: {e}")
        return False
