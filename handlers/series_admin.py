"""
Comandos de administración para indexar series
"""
from telegram import Update
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.tmdb_api import TMDBApi
from config.settings import STORAGE_CHANNEL_ID, ADMIN_IDS, VERIFICATION_CHANNEL_ID
import re
import logging

db = DatabaseManager()
tmdb = TMDBApi()
logger = logging.getLogger(__name__)

async def auto_index_episodes(update: Update, context: ContextTypes.DEFAULT_TYPE, show):
    """
    Busca automáticamente mensajes en el canal con formato #x# y los indexa
    Inicia desde el último mensaje indexado guardado en la base de datos
    """
    try:
        # Obtener el último mensaje indexado desde la base de datos
        last_indexed_str = await db.get_config('last_indexed_message', '0')
        last_indexed = int(last_indexed_str)
        # Si es 0 (primera vez), empezar desde 1. Si ya hay mensajes indexados, continuar desde el siguiente
        start_message_id = 1 if last_indexed == 0 else last_indexed + 1
        
        # Determinar si es un callback o comando
        if update.callback_query:
            chat_id = update.effective_chat.id
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔍 Buscando episodios de <b>{show.name}</b> en el canal...\n"
                     f"📍 Iniciando desde mensaje #{start_message_id}\n\n"
                     f"⏳ Esto puede tomar unos momentos...",
                parse_mode='HTML'
            )
        else:
            chat_id = update.effective_chat.id
            message = await update.message.reply_text(
                f"🔍 Buscando episodios de <b>{show.name}</b> en el canal...\n"
                f"📍 Iniciando desde mensaje #{start_message_id}\n\n"
                f"⏳ Esto puede tomar unos momentos...",
                parse_mode='HTML'
            )
        
        # Iniciar búsqueda automática
        await scan_channel_for_episodes(update, context, show.id, show.name, start_message_id, chat_id)
        
        return 0
            
    except Exception as e:
        logger.error(f"Error en auto_index_episodes: {e}")
        if update.callback_query:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Error: {e}"
            )
        else:
            await update.message.reply_text(f"❌ Error: {e}")
        return 0

async def scan_channel_for_episodes(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    show_id: int, show_name: str, start_message_id: int, chat_id: int):
    """
    Escanea el canal buscando episodios de la serie
    Soporta múltiples formatos:
    - 1x1, 2x14 (formato corto)
    - 🔻Lucifer — 02x01 — Audio Latino (formato con emoji y guión largo)
    - Breaking Bad - S01E01 - 1080p.mp4 (formato S##E##)
    - Temporada 2 - Capítulo 14 (formato español)
    - Temporada 1 - Capítulo 20 (formato español)
    """
    # Patrones para detectar episodios
    # Formato: 1x1, 2x14, etc.
    pattern_short = re.compile(r'(\d+)[xX](\d+)')
    # Formato: Temporada 2 - Capítulo 14, Temporada 1 - Capítulo 20
    pattern_spanish = re.compile(r'[Tt]emporada\s*(\d+)\s*[-–—]\s*[Cc]ap[ií]tulo\s*(\d+)', re.IGNORECASE)
    # Formato: 🔻Lucifer — 02x01 — Audio Latino (con emoji y guión largo)
    pattern_emoji_dash = re.compile(r'(\d+)[xX](\d+)\s*[—–-]')
    # Formato: Breaking Bad - S01E01 - 1080p.mp4
    pattern_se_format = re.compile(r'[Ss](\d+)[Ee](\d+)')
    
    indexed_count = 0
    empty_count = 0
    MAX_EMPTY = 5
    current_message_id = start_message_id
    last_indexed_message_id = 0  # Se actualizará con cada episodio indexado
    
    try:
        while empty_count < MAX_EMPTY:
            try:
                # Intentar obtener el mensaje del canal
                message = await context.bot.forward_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=current_message_id
                )
                
                # Eliminar el mensaje reenviado inmediatamente
                await message.delete()
                
                # Verificar si el mensaje tiene video
                if not message.video:
                    empty_count += 1
                    current_message_id += 1
                    continue
                
                # Obtener caption del mensaje
                caption = message.caption or ""
                
                # Intentar encontrar el episodio con cualquiera de los patrones
                # NOTA: Ya no verificamos si el caption contiene el nombre de la serie
                # Esto permite indexar episodios con formato solo "1x1", "1x2", etc.
                match = None
                episode_title = None
                season_num = None
                episode_num = None
                
                # Primero intentar formato español "Temporada X - Capítulo Y"
                match_spanish = pattern_spanish.search(caption)
                if match_spanish:
                    match = match_spanish
                    season_num = int(match.group(1))
                    episode_num = int(match.group(2))
                    # Extraer título después del patrón
                    title_match = re.search(r'[Cc]ap[ií]tulo\s*\d+\s*[-–—]?\s*(.+)', caption)
                    episode_title = title_match.group(1).strip() if title_match else f"Episodio {episode_num}"
                
                # Si no se encontró, intentar formato S##E## (ej: S01E01)
                if not match:
                    match_se = pattern_se_format.search(caption)
                    if match_se:
                        match = match_se
                        season_num = int(match.group(1))
                        episode_num = int(match.group(2))
                        # Extraer título después del patrón
                        title_match = re.search(r'[Ss]\d+[Ee]\d+\s*[-–—]?\s*(.+)', caption)
                        episode_title = title_match.group(1).strip() if title_match else f"Episodio {episode_num}"
                
                # Si no se encontró, intentar formato corto "#x#" (incluyendo emoji-dash)
                if not match:
                    match_short = pattern_short.search(caption)
                    if match_short:
                        match = match_short
                        season_num = int(match.group(1))
                        episode_num = int(match.group(2))
                        # Extraer título después del patrón
                        title_match = re.search(r'\d+[xX]\d+\s*[-–—]?\s*(.+)', caption)
                        episode_title = title_match.group(1).strip() if title_match else f"Episodio {episode_num}"
                
                if not match:
                    empty_count += 1
                    current_message_id += 1
                    continue
                
                # Resetear contador de vacíos
                empty_count = 0
                
                # Guardar en la base de datos
                await db.add_episode(
                    tv_show_id=show_id,
                    season_number=season_num,
                    episode_number=episode_num,
                    file_id=message.video.file_id,
                    message_id=current_message_id,
                    title=episode_title
                )
                
                indexed_count += 1
                last_indexed_message_id = current_message_id
                
                # Actualizar progreso cada 5 episodios
                if indexed_count % 5 == 0:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"📊 Progreso: {indexed_count} episodios indexados...",
                        parse_mode='HTML'
                    )
                
            except Exception as e:
                # Si no se puede obtener el mensaje (probablemente no existe)
                empty_count += 1
            
            current_message_id += 1
        
        # Guardar el último mensaje procesado (si se indexó algo, guardar el último indexado;
        # si no, guardar el último mensaje revisado menos 1 para no saltar mensajes)
        if indexed_count > 0:
            await db.set_config('last_indexed_message', str(last_indexed_message_id))
        else:
            # Si no se indexó nada, guardar el último mensaje revisado
            await db.set_config('last_indexed_message', str(current_message_id - 1))
        
        if indexed_count > 0:
            # Enviar resumen
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ <b>Indexación completada!</b>\n\n"
                     f"📺 Serie: {show_name}\n"
                     f"📊 Episodios indexados: {indexed_count}\n"
                     f"💾 Último mensaje procesado: #{last_indexed_message_id}",
                parse_mode='HTML'
            )
            
            # Obtener información de la serie para el anuncio
            show = await db.get_tv_show_by_id(show_id)
            
            # Publicar en el canal de verificación
            try:
                announcement_text = (
                    f"🆕 <b>Nueva Serie Disponible</b>\n\n"
                    f"📺 {show.name} ({show.year})\n"
                    f"⭐️ Rating: {show.vote_average}/10\n"
                    f"📊 {indexed_count} episodios disponibles\n\n"
                    f"Usa el botón de abajo para ver todos los episodios!"
                )
                
                # Crear botón con deep link
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("▶️ Ver Ahora", url=f"https://t.me/{context.bot.username}?start=series_{show.id}")
                ]])
                
                if show.poster_url:
                    await context.bot.send_photo(
                        chat_id=VERIFICATION_CHANNEL_ID,
                        photo=show.poster_url,
                        caption=announcement_text,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
                else:
                    await context.bot.send_message(
                        chat_id=VERIFICATION_CHANNEL_ID,
                        text=announcement_text,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
                
                # Enviar notificaciones a grupos
                await send_group_notifications_series(context, show.name, show.year, show.id, indexed_count)
                    
            except Exception as e:
                logger.error(f"Error al publicar en el canal: {e}")
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ No se encontraron episodios de <b>{show_name}</b> "
                     f"a partir del mensaje #{start_message_id}\n\n"
                     f"Verifica que:\n"
                     f"• Los mensajes tengan video\n"
                     f"• El caption contenga '{show_name}'\n"
                     f"• El caption tenga uno de estos formatos:\n"
                     f"  - <code>1x1</code>, <code>2x14</code> (formato corto)\n"
                     f"  - <code>Temporada 1 - Capítulo 20</code> (formato español)\n"
                     f"  - <code>🔻Lucifer — 02x01 — Audio Latino</code> (formato con emoji)\n"
                     f"  - <code>Breaking Bad - S01E01 - 1080p.mp4</code> (formato S##E##)",
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Error en scan_channel_for_episodes: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Error durante el escaneo: {e}"
        )

async def index_series_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /indexar_serie - Indexa una nueva serie con sus episodios
    
    Uso: /indexar_serie <nombre de la serie>
    Ejemplo: /indexar_serie Breaking Bad
    
    El sistema detecta automáticamente episodios en estos formatos:
    - 1x1, 2x14 (formato corto)
    - 🔻Lucifer — 02x01 — Audio Latino (formato con emoji)
    - Breaking Bad - S01E01 - 1080p.mp4 (formato S##E##)
    - Temporada 1 - Capítulo 20 (formato español)
    
    Si no encuentra episodios automáticamente, puedes indexar manualmente
    respondiendo a los mensajes del canal con cualquiera de estos formatos.
    """
    user_id = update.effective_user.id
    
    # Verificar si es admin
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    # Obtener nombre de la serie
    if not context.args:
        await update.message.reply_text(
            "❌ Debes proporcionar el nombre de la serie.\n\n"
            "Uso: <code>/indexar_serie Loki (2021)</code>",
            parse_mode='HTML'
        )
        return
    
    series_name = " ".join(context.args)
    
    # Buscar serie en TMDB
    await update.message.reply_text(f"🔍 Buscando serie: <b>{series_name}</b>...", parse_mode='HTML')
    
    series_data = tmdb.search_tv_show(series_name)
    
    if not series_data:
        await update.message.reply_text(
            f"❌ No se encontró la serie <b>{series_name}</b> en TMDB.\n\n"
            "Verifica el nombre e intenta nuevamente.",
            parse_mode='HTML'
        )
        return
    
    # Verificar si ya existe en la base de datos
    existing_show = await db.get_tv_show_by_tmdb_id(series_data['tmdb_id'])
    
    if existing_show:
        await update.message.reply_text(
            f"⚠️ La serie <b>{series_data['name']}</b> ya está indexada.\n\n"
            f"ID: {existing_show.id}\n"
            f"Temporadas: {existing_show.number_of_seasons}",
            parse_mode='HTML'
        )
        return
    
    # Obtener detalles completos de la serie
    details = tmdb.get_tv_show_details(series_data['tmdb_id'])
    
    if not details:
        await update.message.reply_text("❌ Error al obtener detalles de la serie.")
        return
    
    # Guardar serie en la base de datos
    show = await db.add_tv_show(
        name=details['name'],
        tmdb_id=details['tmdb_id'],
        original_name=details.get('original_name'),
        year=details.get('year'),
        overview=details.get('overview'),
        poster_url=details.get('poster_url'),
        backdrop_url=details.get('backdrop_url'),
        vote_average=details.get('vote_average'),
        genres=", ".join(details.get('genres', [])),
        number_of_seasons=details.get('number_of_seasons'),
        status=details.get('status')
    )
    
    if not show:
        await update.message.reply_text("❌ Error al guardar la serie en la base de datos.")
        return
    
    # Buscar automáticamente episodios en el canal
    await update.message.reply_text(
        f"✅ Serie indexada correctamente:\n\n"
        f"📺 <b>{show.name}</b> ({show.year})\n"
        f"🎬 Temporadas: {show.number_of_seasons}\n"
        f"⭐ Calificación: {show.vote_average}/10\n\n"
        f"🔍 Buscando episodios en el canal...",
        parse_mode='HTML'
    )
    
    # Buscar y indexar episodios automáticamente
    indexed_count = await auto_index_episodes(update, context, show)
    
    if indexed_count > 0:
        await update.message.reply_text(
            f"✅ Indexación automática completada:\n\n"
            f"📺 <b>{show.name}</b>\n"
            f"📹 {indexed_count} episodio(s) indexado(s)\n\n"
            f"Puedes usar /start para buscar la serie.",
            parse_mode='HTML'
        )
    else:
        # Guardar ID de la serie para indexación manual
        context.user_data['indexing_show_id'] = show.id
        context.user_data['indexing_show_name'] = show.name
        
        await update.message.reply_text(
            f"⚠️ No se encontraron episodios automáticamente en el canal.\n\n"
            f"Puedes indexar manualmente respondiendo mensajes con cualquiera de estos formatos:\n\n"
            f"<b>Formato corto:</b>\n"
            f"<code>1x1</code> (Temporada 1, Episodio 1)\n"
            f"<code>2x5</code> (Temporada 2, Episodio 5)\n\n"
            f"<b>Formato español:</b>\n"
            f"<code>Temporada 1 - Capítulo 20</code>\n"
            f"<code>Temporada 2 - Capítulo 14</code>\n\n"
            f"<b>Formato con emoji:</b>\n"
            f"<code>🔻Lucifer — 02x01 — Audio Latino</code>\n\n"
            f"<b>Formato S##E##:</b>\n"
            f"<code>Breaking Bad - S01E01 - 1080p.mp4</code>",
            parse_mode='HTML'
        )

async def index_episode_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja respuestas a mensajes del canal para indexar episodios
    Soporta múltiples formatos:
    - 1x1, 2x10 (formato corto)
    - 🔻Lucifer — 02x01 — Audio Latino (formato con emoji y guión largo)
    - Breaking Bad - S01E01 - 1080p.mp4 (formato S##E##)
    - Temporada 2 - Capítulo 14 (formato español)
    """
    user_id = update.effective_user.id
    
    # Verificar si es admin
    if user_id not in ADMIN_IDS:
        return
    
    # Verificar si está respondiendo a un mensaje
    if not update.message.reply_to_message:
        return
    
    # Verificar si hay una serie en proceso de indexación
    if 'indexing_show_id' not in context.user_data:
        await update.message.reply_text(
            "❌ No hay ninguna serie en proceso de indexación.\n"
            "Usa <code>/indexar_serie</code> primero.",
            parse_mode='HTML'
        )
        return
    
    # Parsear formatos
    text = update.message.text.strip()
    
    # Formato corto: 1x1, 2x10
    pattern_short = r'(\d+)[xX](\d+)'
    # Formato español: Temporada 2 - Capítulo 14
    pattern_spanish = r'[Tt]emporada\s*(\d+)\s*[-–—]\s*[Cc]ap[ií]tulo\s*(\d+)'
    # Formato S##E##: S01E01, S02E05
    pattern_se_format = r'[Ss](\d+)[Ee](\d+)'
    
    match_short = re.search(pattern_short, text)
    match_spanish = re.search(pattern_spanish, text, re.IGNORECASE)
    match_se = re.search(pattern_se_format, text)
    
    season_number = None
    episode_number = None
    
    # Priorizar formato español si está presente
    if match_spanish:
        season_number = int(match_spanish.group(1))
        episode_number = int(match_spanish.group(2))
    elif match_se:
        season_number = int(match_se.group(1))
        episode_number = int(match_se.group(2))
    elif match_short:
        season_number = int(match_short.group(1))
        episode_number = int(match_short.group(2))
    else:
        return  # No es un formato válido, ignorar
    
    show_id = context.user_data['indexing_show_id']
    show_name = context.user_data['indexing_show_name']
    
    # Obtener información del mensaje respondido
    replied_msg = update.message.reply_to_message
    
    # Verificar si el mensaje tiene video
    if not replied_msg.video:
        await update.message.reply_text("❌ El mensaje debe contener un video.")
        return
    
    file_id = replied_msg.video.file_id
    message_id = replied_msg.message_id
    
    # Buscar detalles del episodio en TMDB
    show = await db.get_tv_show_by_id(show_id)
    season_details = tmdb.get_season_details(show.tmdb_id, season_number)
    
    episode_info = None
    if season_details and season_details.get('episodes'):
        for ep in season_details['episodes']:
            if ep['episode_number'] == episode_number:
                episode_info = ep
                break
    
    # Guardar episodio en la base de datos
    episode = await db.add_episode(
        tv_show_id=show_id,
        file_id=file_id,
        message_id=message_id,
        season_number=season_number,
        episode_number=episode_number,
        title=episode_info.get('name') if episode_info else None,
        overview=episode_info.get('overview') if episode_info else None,
        air_date=episode_info.get('air_date') if episode_info else None,
        runtime=episode_info.get('runtime') if episode_info else None,
        still_path=episode_info.get('still_path') if episode_info else None,
        channel_message_id=message_id
    )
    
    if episode:
        ep_title = episode_info.get('name', '') if episode_info else ''
        await update.message.reply_text(
            f"✅ Episodio indexado:\n\n"
            f"📺 <b>{show_name}</b>\n"
            f"🎬 S{season_number}x{episode_number:02d}"
            f"{' - ' + ep_title if ep_title else ''}\n"
            f"🆔 Episode ID: {episode.id}",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("❌ Error al indexar el episodio.")

async def finish_indexing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /terminar_indexacion - Finaliza el proceso de indexación de serie
    """
    user_id = update.effective_user.id
    
    # Verificar si es admin
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    if 'indexing_show_id' not in context.user_data:
        await update.message.reply_text("❌ No hay ninguna indexación activa.")
        return
    
    show_id = context.user_data['indexing_show_id']
    show_name = context.user_data['indexing_show_name']
    
    # Obtener estadísticas de episodios indexados
    seasons = await db.get_seasons_for_show(show_id)
    total_episodes = sum(count for _, count in seasons)
    
    # Limpiar contexto
    del context.user_data['indexing_show_id']
    del context.user_data['indexing_show_name']
    
    await update.message.reply_text(
        f"✅ Indexación finalizada:\n\n"
        f"📺 <b>{show_name}</b>\n"
        f"🎬 Temporadas indexadas: {len(seasons)}\n"
        f"📹 Total de episodios: {total_episodes}\n\n"
        "Puedes empezar a indexar otra serie con <code>/indexar_serie</code>",
        parse_mode='HTML'
    )

async def send_group_notifications_series(context, series_name, year, series_id, episode_count):
    """
    Envía notificaciones cortas a grupos configurados cuando se agrega una nueva serie
    
    Args:
        context: Contexto del bot
        series_name: Nombre de la serie
        year: Año de la serie 
        series_id: ID de la serie en la base de datos
        episode_count: Número de episodios indexados
    """
    from config.settings import NOTIFICATION_GROUPS
    
    if not NOTIFICATION_GROUPS:
        print("📝 No hay grupos configurados para notificaciones")
        return
    
    # Mensaje corto para grupos
    group_message = f"📺 Nueva serie agregada: <b>{series_name}</b> ({year}) - {episode_count} episodios"
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔍 Ver en el bot", url=f"https://t.me/{context.bot.username}?start=series_{series_id}")
    ]])
    
    print(f"📱 Enviando notificaciones de serie a {len(NOTIFICATION_GROUPS)} grupo(s)...")
    
    for group_id in NOTIFICATION_GROUPS:
        try:
            await context.bot.send_message(
                chat_id=group_id,
                text=group_message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            print(f"✅ Notificación de serie enviada al grupo {group_id}")
        except Exception as e:
            print(f"❌ Error enviando notificación de serie al grupo {group_id}: {e}")
            continue
