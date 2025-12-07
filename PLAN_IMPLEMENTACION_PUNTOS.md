# ===========================================
# PLAN DE IMPLEMENTACIÓN: SISTEMA DE PUNTOS/TOKENS
# ===========================================
# Fecha: Diciembre 2025
# Versión: 1.0
# Duración estimada: 5-7 días
# ===========================================

## 📋 **FASE 1: BASE DE DATOS (Día 1)**
### ✅ **Paso 1.1: Ejecutar SQL en Supabase**
```bash
# En Supabase Dashboard → SQL Editor
# Ejecutar el archivo: supabase_points_system.sql
```

### ✅ **Paso 1.2: Verificar tablas creadas**
```sql
-- Verificar que las tablas existen
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('user_points', 'referrals', 'points_transactions');
```

---

## 📋 **FASE 2: MODELOS DE DATOS (Día 1-2)**
### ✅ **Paso 2.1: Extender models.py**
```python
# Agregar a database/models.py

class UserPoints(Base):
    __tablename__ = 'user_points'

    user_id = Column(BigInteger, primary_key=True, index=True)
    points_balance = Column(Integer, default=0, nullable=False)
    total_earned = Column(Integer, default=0, nullable=False)
    total_used = Column(Integer, default=0, nullable=False)
    last_earned_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Referral(Base):
    __tablename__ = 'referrals'

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    referred_id = Column(BigInteger, ForeignKey('users.user_id'))
    referral_code = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), default='pending')
    referral_link = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), default=lambda: datetime.utcnow() + timedelta(days=7))

    referrer = relationship("User", foreign_keys=[referrer_id])
    referred = relationship("User", foreign_keys=[referred_id])

class PointsTransaction(Base):
    __tablename__ = 'points_transactions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)
    points_amount = Column(Integer, nullable=False)
    reason = Column(String(100))
    reference_id = Column(Integer)
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User")
```

### ✅ **Paso 2.2: Extender DatabaseManager**
```python
# Agregar métodos a database/db_manager.py

# ======================== MÉTODOS PARA PUNTOS ========================

async def get_user_points(self, user_id: int) -> int:
    """Obtiene el balance de puntos de un usuario"""
    async with self.async_session() as session:
        result = await session.execute(
            select(UserPoints.points_balance).where(UserPoints.user_id == user_id)
        )
        balance = result.scalar()
        return balance or 0

async def create_or_update_user_points(self, user_id: int, points_change: int, reason: str, reference_id: int = None) -> bool:
    """Crea o actualiza puntos de usuario con transacción"""
    async with self.async_session() as session:
        try:
            # Obtener balance actual
            result = await session.execute(
                select(UserPoints).where(UserPoints.user_id == user_id)
            )
            user_points = result.scalar_one_or_none()

            if user_points:
                new_balance = max(0, min(5, user_points.points_balance + points_change))
                balance_before = user_points.points_balance
                user_points.points_balance = new_balance
                user_points.total_earned += max(0, points_change)
                user_points.total_used += max(0, -points_change)
                if points_change > 0:
                    user_points.last_earned_at = datetime.utcnow()
            else:
                # Usuario nuevo
                new_balance = max(0, min(5, points_change))
                balance_before = 0
                user_points = UserPoints(
                    user_id=user_id,
                    points_balance=new_balance,
                    total_earned=max(0, points_change),
                    total_used=max(0, -points_change)
                )
                if points_change > 0:
                    user_points.last_earned_at = datetime.utcnow()
                session.add(user_points)

            # Crear transacción
            transaction = PointsTransaction(
                user_id=user_id,
                transaction_type='earned' if points_change > 0 else 'used',
                points_amount=abs(points_change),
                reason=reason,
                reference_id=reference_id,
                balance_before=balance_before,
                balance_after=new_balance
            )
            session.add(transaction)

            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            print(f"Error updating user points: {e}")
            return False

async def use_user_points(self, user_id: int, points: int = 1) -> bool:
    """Usa puntos de un usuario (retorna True si tuvo éxito)"""
    current_balance = await self.get_user_points(user_id)
    if current_balance >= points:
        return await self.create_or_update_user_points(user_id, -points, 'video_without_ad')
    return False

# ======================== MÉTODOS PARA REFERIDOS ========================

async def create_referral(self, referrer_id: int, referral_code: str, referral_link: str) -> bool:
    """Crea un nuevo referido pendiente"""
    async with self.async_session() as session:
        try:
            referral = Referral(
                referrer_id=referrer_id,
                referral_code=referral_code,
                referral_link=referral_link
            )
            session.add(referral)
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            print(f"Error creating referral: {e}")
            return False

async def get_referral_by_code(self, referral_code: str) -> Referral:
    """Obtiene un referido por código"""
    async with self.async_session() as session:
        result = await session.execute(
            select(Referral).where(Referral.referral_code == referral_code)
        )
        return result.scalar_one_or_none()

async def complete_referral(self, referral_code: str, referred_id: int) -> bool:
    """Completa un referido cuando el usuario invitado se registra"""
    async with self.async_session() as session:
        try:
            result = await session.execute(
                select(Referral).where(Referral.referral_code == referral_code)
            )
            referral = result.scalar_one_or_none()

            if not referral or referral.status != 'pending':
                return False

            # Verificar que no sea auto-referido
            if referral.referrer_id == referred_id:
                return False

            # Verificar que el referido no haya sido referido antes
            existing = await session.execute(
                select(Referral).where(
                    Referral.referred_id == referred_id,
                    Referral.status == 'completed'
                )
            )
            if existing.scalar_one_or_none():
                return False

            # Completar referido
            referral.referred_id = referred_id
            referral.status = 'completed'
            referral.completed_at = datetime.utcnow()

            await session.commit()

            # Otorgar puntos al referrer (usando función de BD)
            await session.execute(
                text("SELECT award_referral_points(:referrer_id, :referred_id)"),
                {"referrer_id": referral.referrer_id, "referred_id": referred_id}
            )

            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            print(f"Error completing referral: {e}")
            return False

async def get_user_referral_stats(self, user_id: int) -> dict:
    """Obtiene estadísticas de referidos de un usuario"""
    async with self.async_session() as session:
        # Total de referidos
        result = await session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
        )
        total = result.scalar()

        # Completados
        result = await session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_id == user_id,
                Referral.status == 'completed'
            )
        )
        completed = result.scalar()

        # Pendientes
        result = await session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_id == user_id,
                Referral.status == 'pending'
            )
        )
        pending = result.scalar()

        return {
            'total': total or 0,
            'completed': completed or 0,
            'pending': pending or 0
        }
```

---

## 📋 **FASE 3: UTILIDADES Y HELPERS (Día 2)**
### ✅ **Paso 3.1: Crear utils/referral_system.py**
```python
# utils/referral_system.py
import secrets
import hashlib
from typing import Optional

class ReferralSystem:
    @staticmethod
    def generate_referral_code(user_id: int) -> str:
        """Genera un código único de referido"""
        # Crear hash único basado en user_id y timestamp
        random_bytes = secrets.token_bytes(16)
        data = f"{user_id}_{random_bytes.hex()}"
        code = hashlib.sha256(data.encode()).hexdigest()[:8].upper()
        return f"REF{code}"

    @staticmethod
    def generate_referral_link(bot_username: str, referral_code: str) -> str:
        """Genera el link completo de referido"""
        return f"https://t.me/{bot_username}?start=ref_{referral_code}"

    @staticmethod
    def parse_referral_code(text: str) -> Optional[str]:
        """Extrae código de referido de un mensaje /start"""
        if text.startswith("ref_"):
            return text[4:]  # Remover "ref_" prefix
        return None

    @staticmethod
    def validate_referral_activity(user_id: int, db) -> bool:
        """Valida que el usuario tenga actividad suficiente para completar referido"""
        # Verificar que se unió al canal
        # Verificar que usó el bot al menos una vez
        # Verificar que no es cuenta nueva/fake
        # TODO: Implementar validaciones específicas
        return True
```

### ✅ **Paso 3.2: Extender utils/points_manager.py**
```python
# utils/points_manager.py
from database.db_manager import DatabaseManager

class PointsManager:
    MAX_POINTS = 5
    POINTS_PER_REFERRAL = 1

    def __init__(self, db: DatabaseManager):
        self.db = db

    async def get_user_balance(self, user_id: int) -> int:
        """Obtiene balance actual de puntos"""
        return await self.db.get_user_points(user_id)

    async def can_use_points(self, user_id: int, points: int = 1) -> bool:
        """Verifica si usuario puede usar puntos"""
        balance = await self.get_user_balance(user_id)
        return balance >= points

    async def award_referral_points(self, referrer_id: int, referred_id: int) -> bool:
        """Otorga puntos por referido completado"""
        # Verificar límite máximo
        current_balance = await self.get_user_balance(referrer_id)
        if current_balance >= self.MAX_POINTS:
            return False

        # Otorgar puntos
        return await self.db.create_or_update_user_points(
            referrer_id,
            self.POINTS_PER_REFERRAL,
            'referral_completed',
            reference_id=None  # TODO: Obtener ID del referido
        )

    async def use_points_for_video(self, user_id: int) -> bool:
        """Usa 1 punto para ver video sin anuncio"""
        return await self.db.use_user_points(user_id, 1)

    async def get_user_stats(self, user_id: int) -> dict:
        """Obtiene estadísticas completas del usuario"""
        balance = await self.get_user_balance(user_id)
        referral_stats = await self.db.get_user_referral_stats(user_id)

        return {
            'balance': balance,
            'max_balance': self.MAX_POINTS,
            'referral_stats': referral_stats,
            'can_earn_more': balance < self.MAX_POINTS
        }
```

---

## 📋 **FASE 4: HANDLERS Y COMANDOS (Día 3-4)**
### ✅ **Paso 4.1: Crear handlers/referral_commands.py**
```python
# handlers/referral_commands.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS
from utils.referral_system import ReferralSystem
from utils.points_manager import PointsManager

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /referral - Obtener link de referido"""
    user = update.effective_user
    db = context.bot_data['db']
    points_manager = PointsManager(db)

    # Obtener estadísticas del usuario
    stats = await points_manager.get_user_stats(user.id)

    # Generar código si no existe
    # TODO: Verificar si ya tiene código activo
    referral_code = ReferralSystem.generate_referral_code(user.id)
    referral_link = ReferralSystem.generate_referral_link(context.bot.username, referral_code)

    # Guardar referido en BD
    await db.create_referral(user.id, referral_code, referral_link)

    # Crear mensaje
    text = f"""
🎁 <b>Sistema de Referidos</b>

📊 <b>Tus Estadísticas:</b>
• Puntos disponibles: <b>{stats['balance']}/{stats['max_balance']}</b>
• Referidos totales: <b>{stats['referral_stats']['total']}</b>
• Completados: <b>{stats['referral_stats']['completed']}</b>
• Pendientes: <b>{stats['referral_stats']['pending']}</b>

🔗 <b>Tu Link de Referido:</b>
<code>{referral_link}</code>

📱 <b>¿Cómo funciona?</b>
1. Comparte tu link con amigos
2. Cuando se unan y usen el bot → ¡Ganas 1 punto!
3. Máximo {stats['max_balance']} puntos por usuario
4. Cada punto = 1 video sin anuncio

⚠️ <b>Importante:</b> Solo referidos válidos cuentan (deben unirse al canal y usar el bot)
"""

    keyboard = [
        [InlineKeyboardButton("📋 Copiar Link", callback_data=f"copy_referral_{referral_code}")],
        [InlineKeyboardButton("📊 Ver Estadísticas", callback_data="referral_stats")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="referral_help")]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /points - Ver balance de puntos"""
    user = update.effective_user
    db = context.bot_data['db']
    points_manager = PointsManager(db)

    stats = await points_manager.get_user_stats(user.id)

    text = f"""
💰 <b>Tus Puntos</b>

⭐ <b>Balance actual:</b> {stats['balance']}/{stats['max_balance']} puntos

📈 <b>Estadísticas:</b>
• Total ganados: {stats['referral_stats']['completed']}
• Total usados: {stats['referral_stats']['total'] - stats['referral_stats']['completed'] - stats['referral_stats']['pending']}
• Referidos pendientes: {stats['referral_stats']['pending']}

🎯 <b>Próximo objetivo:</b>
"""

    if stats['balance'] < stats['max_balance']:
        remaining = stats['max_balance'] - stats['balance']
        text += f"Gana {remaining} punto(s) más para llegar al máximo"
    else:
        text += "¡Has alcanzado el límite máximo de puntos!"

    text += "\n\n💡 <i>Recuerda: Los puntos se usan automáticamente cuando ves videos</i>"

    await update.message.reply_text(text, parse_mode='HTML')

async def handle_referral_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja callbacks de referidos"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    if data.startswith("copy_referral_"):
        referral_code = data.replace("copy_referral_", "")
        # TODO: Implementar copiado al portapapeles o mostrar link

    elif data == "referral_stats":
        # Mostrar estadísticas detalladas
        await show_referral_stats(query, context)

    elif data == "referral_help":
        # Mostrar ayuda del sistema
        await show_referral_help(query)

async def show_referral_stats(query, context):
    """Muestra estadísticas detalladas de referidos"""
    db = context.bot_data['db']
    points_manager = PointsManager(db)

    stats = await points_manager.get_user_stats(query.from_user.id)

    text = f"""
📊 <b>Estadísticas de Referidos</b>

💰 <b>Puntos:</b>
• Disponibles: {stats['balance']}/{stats['max_balance']}
• Total ganados: {stats['referral_stats']['completed']}
• Total usados: Histórico no disponible

👥 <b>Referidos:</b>
• Total creados: {stats['referral_stats']['total']}
• Completados: {stats['referral_stats']['completed']}
• Pendientes: {stats['referral_stats']['pending']}
• Expirados: {stats['referral_stats']['total'] - stats['referral_stats']['completed'] - stats['referral_stats']['pending']}

🎯 <b>Conversión:</b> {stats['referral_stats']['completed']/max(1, stats['referral_stats']['total'])*100:.1f}%
"""

    await query.edit_message_text(text, parse_mode='HTML')

async def show_referral_help(query):
    """Muestra ayuda del sistema de referidos"""
    text = """
🆘 <b>Ayuda - Sistema de Referidos</b>

🎯 <b>¿Cómo ganar puntos?</b>
1. Usa el comando /referral
2. Copia tu link único
3. Compártelo con amigos/amigos
4. Cuando se unan al canal y usen el bot → ¡Ganas puntos!

⭐ <b>¿Qué son los puntos?</b>
• Cada punto = 1 video sin anuncio
• Máximo 5 puntos por usuario
• No expiran (mientras uses el bot)

⚠️ <b>Reglas importantes:</b>
• No puedes referirte a ti mismo
• Cada persona solo puede ser referida una vez
• El referido debe unirse al canal y usar el bot
• Los referidos expiran en 7 días

🔍 <b>¿Cómo se usan los puntos?</b>
• Automáticamente cuando pides un video
• Si tienes puntos → Saltas el anuncio
• Si no tienes → Ves anuncio normal

📞 <b>¿Dudas?</b>
Contacta a @admin si tienes problemas
"""

    await query.edit_message_text(text, parse_mode='HTML')
```

### ✅ **Paso 4.2: Modificar handlers/start.py**
```python
# Agregar al inicio de handle_start_command en handlers/start.py

# Verificar si viene de un referido
if context.args and len(context.args) > 0:
    arg = context.args[0]

    # Sistema de referidos
    if arg.startswith("ref_"):
        referral_code = ReferralSystem.parse_referral_code(arg)
        if referral_code:
            # Procesar referido
            success = await db.complete_referral(referral_code, user.id)
            if success:
                await update.message.reply_text(
                    "🎉 ¡Bienvenido! Has sido referido por un amigo.\n"
                    "Tu referrer ha ganado puntos por traerte aquí.",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "👋 ¡Bienvenido al bot!\n"
                    "Parece que este link de referido no es válido.",
                    parse_mode='HTML'
                )
        # Continuar con flujo normal
```

### ✅ **Paso 4.3: Modificar handlers/start.py - send_video_by_message_id**
```python
# Modificar send_video_by_message_id para usar puntos

async def send_video_by_message_id(update, context, video_msg_id, user_id):
    """Envía Mini App con anuncio cuando viene desde canal"""
    db = context.bot_data['db']
    points_manager = PointsManager(db)

    try:
        # Usar método existente optimizado
        video = await db.get_video_by_message_id(video_msg_id)

        if not video:
            await update.message.reply_text(
                "❌ Video no encontrado.\n\n"
                "Puede que haya sido eliminado o no esté disponible."
            )
            return

        # VERIFICAR SI USUARIO TIENE PUNTOS
        has_points = await points_manager.can_use_points(user_id)

        if has_points:
            # USAR PUNTO Y ENVIAR SIN ANUNCIO
            success = await points_manager.use_points_for_video(user_id)
            if success:
                await update.message.reply_text(
                    "⭐ <b>¡Punto usado!</b> Viendo video sin anuncio...",
                    parse_mode='HTML'
                )
                # Enviar directamente sin anuncio
                await send_video_directly(update, context, video, user_id)
            else:
                # Error usando puntos, enviar con anuncio
                await send_video_with_ad(update, context, video, user_id)
        else:
            # NO TIENE PUNTOS - ENVIAR CON ANUNCIO NORMAL
            await send_video_with_ad(update, context, video, user_id)

    except Exception as e:
        print(f"Error buscando video: {e}")
        await update.message.reply_text(
            "❌ Error al buscar el video. Por favor intenta más tarde."
        )
        return
```

---

## 📋 **FASE 5: INTEGRACIÓN Y REGISTRO (Día 4)**
### ✅ **Paso 5.1: Modificar main.py**
```python
# Agregar imports
from handlers.referral_commands import (
    referral_command, points_command, handle_referral_callbacks
)

# Agregar handlers
application.add_handler(CommandHandler("referral", referral_command))
application.add_handler(CommandHandler("points", points_command))
application.add_handler(CallbackQueryHandler(handle_referral_callbacks, pattern="^(copy_referral_|referral_)"))
```

### ✅ **Paso 5.2: Actualizar help_command**
```python
help_text = """
📚 *Ayuda del Bot*

*Comandos disponibles:*
/start - Iniciar y ver menú principal
/buscar <término> - Buscar videos (modo antiguo)
/search <término> - Search videos (English)
/help - Mostrar esta ayuda

*Sistema de Puntos:*
/referral - Obtener link de referido para ganar puntos
/points - Ver tu balance de puntos

*Comandos de Administración:*
/indexar - Indexar nuevas películas automáticamente
/indexar_manual <msg_id> - Indexar película específica
/reindexar <msg_id> - Re-indexar película existente
/repost - Re-publicar videos antiguos en nuevo canal
/indexar_serie <serie> - Indexar nueva serie
/terminar_indexacion - Finalizar indexación de serie
/stats - Ver estadísticas del bot

*Cómo usar:*
1. Únete al canal de verificación
2. Verifica tu membresía
3. Usa el menú interactivo para elegir películas o series
4. Busca por nombre y selecciona lo que quieres ver

*Sistema de Puntos:*
• Gana puntos compartiendo el bot con amigos
• Cada referido válido = 1 punto (máx 5)
• Cada punto = 1 video sin anuncio
• Los puntos se usan automáticamente

*Ejemplos de búsqueda:*
• Thor
• Loki (2021)
• Breaking Bad
"""
```

---

## 📋 **FASE 6: TESTING Y OPTIMIZACIONES (Día 5-6)**
### ✅ **Paso 6.1: Crear script de testing**
```python
# test_points_system.py
import asyncio
from database.db_manager import DatabaseManager
from utils.points_manager import PointsManager
from utils.referral_system import ReferralSystem

async def test_points_system():
    """Test básico del sistema de puntos"""
    db = DatabaseManager()
    await db.connect()
    points_manager = PointsManager(db)

    # Test 1: Crear puntos para usuario
    print("Test 1: Creando puntos...")
    success = await points_manager.award_referral_points(123456789, 987654321)
    print(f"Resultado: {success}")

    # Test 2: Ver balance
    print("Test 2: Verificando balance...")
    balance = await points_manager.get_user_balance(123456789)
    print(f"Balance: {balance}")

    # Test 3: Usar puntos
    print("Test 3: Usando puntos...")
    success = await points_manager.use_points_for_video(123456789)
    print(f"Resultado: {success}")

    # Test 4: Generar código de referido
    print("Test 4: Generando código de referido...")
    code = ReferralSystem.generate_referral_code(123456789)
    link = ReferralSystem.generate_referral_link("testbot", code)
    print(f"Código: {code}")
    print(f"Link: {link}")

    await db.close()
    print("✅ Tests completados")

if __name__ == "__main__":
    asyncio.run(test_points_system())
```

### ✅ **Paso 6.2: Optimizaciones finales**
- Agregar rate limiting para comandos de referidos
- Implementar cache Redis para balances de puntos
- Agregar métricas de uso del sistema
- Crear dashboard admin para referidos

---

## 📋 **FASE 7: DEPLOYMENT Y MONITOREO (Día 7)**
### ✅ **Paso 7.1: Deploy a producción**
```bash
# Commit y push cambios
git add .
git commit -m "feat: Implementar sistema completo de puntos y referidos

- Nuevas tablas: user_points, referrals, points_transactions
- Sistema de referidos con códigos únicos
- Comando /referral y /points
- Integración automática con envío de videos
- Anti-farming measures y validaciones
- Funciones de BD para transacciones seguras"
git push origin main
```

### ✅ **Paso 7.2: Monitoreo inicial**
- Verificar que las tablas se crearon correctamente
- Probar comandos básicos
- Monitorear logs por errores
- Verificar funcionamiento del sistema de puntos

---

## 🎯 **MÉTRICAS DE ÉXITO**
- ✅ Sistema funcional sin errores críticos
- ✅ Usuarios pueden ganar puntos por referidos
- ✅ Videos se envían sin anuncios cuando hay puntos
- ✅ Anti-farming funcionando correctamente
- ✅ Rendimiento no afectado (< 500ms latencia adicional)

## 🚨 **POSIBLES PROBLEMAS Y SOLUCIONES**
1. **Referidos duplicados**: Validación en BD con constraints únicas
2. **Abuso del sistema**: Rate limiting y validación de actividad
3. **Puntos negativos**: Constraints CHECK en BD
4. **Performance**: Indexes optimizados y queries eficientes

---
*Duración total: 5-7 días | Complejidad: Media-Alta | Riesgo: Bajo*