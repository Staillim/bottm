"""
Comandos de administración para indexar series
"""
from telegram import Update
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.tmdb_api import TMDBApi
from config.settings import STORAGE_CHANNEL_ID, ADMIN_IDS
import re
import logging

db = DatabaseManager()
tmdb = TMDBApi()
logger = logging.getLogger(__name__)

async def auto_index_episodes(update: Update, context: ContextTypes.DEFAULT_TYPE, show):
    """
    Busca automáticamente mensajes en el canal con formato S#x# y los indexa
    Solo busca a partir del último mensaje indexado para evitar duplicados
    """
    try:
        # Verificar si ya hay episodios indexados para esta serie
        existing_episodes = await db.get_episodes_by_show(show.id)
        
        if existing_episodes:
            # Hay episodios previos, buscar solo nuevos
            # Encontrar el message_id más alto (el último indexado)
            last_message_id = max(ep.message_id for ep in existing_episodes)
            
            await update.message.reply_text(
                f"⚠️ Ya hay {len(existing_episodes)} episodio(s) indexado(s).\n\n"
                f"Para indexar MÁS episodios, reenvía el PRIMER mensaje NUEVO\n"
                f"(debe ser posterior al último ya indexado)\n\n"
                f"O usa /terminar_indexacion si ya terminaste.",
                parse_mode='HTML'
            )
        else:
            # No hay episodios previos, pedir el primero
            await update.message.reply_text(
                "⚠️ Por favor, reenvía el PRIMER episodio de la serie del canal\n"
                "(ej: el mensaje con 1x1 en el caption)\n\n"
                "Buscaré automáticamente los siguientes episodios.",
                parse_mode='HTML'
            )
        
        # Guardar contexto para cuando reenvíe el mensaje
        context.user_data['auto_index_show_id'] = show.id
        context.user_data['auto_index_show_name'] = show.name
        context.user_data['waiting_for_first_episode'] = True
        
        return 0
            
    except Exception as e:
        logger.error(f"Error en auto_index_episodes: {e}")
        return 0

async def process_auto_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa la indexación automática desde un mensaje reenviado
    """
    if not context.user_data.get('waiting_for_first_episode'):
        return False
    
    # Verificar que sea un mensaje reenviado del canal
    if not update.message.forward_from_chat:
        await update.message.reply_text("❌ Debes reenviar un mensaje del canal de almacenamiento.")
        return True
    
    show_id = context.user_data.get('auto_index_show_id')
    show_name = context.user_data.get('auto_index_show_name')
    
    if not show_id:
        await update.message.reply_text("❌ Error: No hay serie en proceso de indexación.")
        return True
    
    # Obtener ID del mensaje reenviado
    start_message_id = update.message.forward_from_message_id
    channel_id = update.message.forward_from_chat.id
    
    await update.message.reply_text(
        f"🔍 Buscando episodios desde el mensaje #{start_message_id}...\n"
        f"Solo indexaré episodios que NO estén ya en la base de datos.",
        parse_mode='HTML'
    )
    
    # Buscar episodios hacia adelante desde ese mensaje
    pattern = r'(\d+)[xX](\d+)'
    indexed_count = 0
    skipped_count = 0
    search_range = 200  # Buscar hasta 200 mensajes hacia adelante
    
    show = await db.get_tv_show_by_id(show_id)
    
    for offset in range(search_range):
        try:
            msg_id = start_message_id + offset
            
            # Intentar obtener el mensaje
            try:
                msg = await context.bot.forward_message(
                    chat_id=update.effective_user.id,
                    from_chat_id=channel_id,
                    message_id=msg_id
                )
                
                # Eliminar el mensaje reenviado inmediatamente
                await msg.delete()
                
            except Exception:
                # Mensaje no existe o no es accesible
                continue
            
            # Buscar patrón S#x# en el caption
            text_to_search = msg.caption if msg.caption else (msg.text if msg.text else "")
            
            match = re.search(pattern, text_to_search)
            if match and msg.video:
                season_number = int(match.group(1))
                episode_number = int(match.group(2))
                
                # IMPORTANTE: Verificar si ya existe para evitar duplicados
                existing = await db.get_episode(show_id, season_number, episode_number)
                if existing:
                    skipped_count += 1
                    logger.info(f"⏭️ Saltando S{season_number}x{episode_number} - ya existe")
                    continue
                
                # Buscar info en TMDB
                season_details = tmdb.get_season_details(show.tmdb_id, season_number)
                episode_info = None
                if season_details and season_details.get('episodes'):
                    for ep in season_details['episodes']:
                        if ep['episode_number'] == episode_number:
                            episode_info = ep
                            break
                
                # Guardar episodio
                episode = await db.add_episode(
                    tv_show_id=show_id,
                    file_id=msg.video.file_id,
                    message_id=msg_id,
                    season_number=season_number,
                    episode_number=episode_number,
                    title=episode_info.get('name') if episode_info else None,
                    overview=episode_info.get('overview') if episode_info else None,
                    air_date=episode_info.get('air_date') if episode_info else None,
                    runtime=episode_info.get('runtime') if episode_info else None,
                    still_path=episode_info.get('still_path') if episode_info else None,
                    channel_message_id=msg_id
                )
                
                if episode:
                    indexed_count += 1
                    if indexed_count % 5 == 0:
                        await update.message.reply_text(f"📹 {indexed_count} episodios indexados...")
        
        except Exception as e:
            logger.error(f"Error procesando mensaje {msg_id}: {e}")
            continue
    
    # Limpiar contexto
    context.user_data.pop('waiting_for_first_episode', None)
    context.user_data.pop('auto_index_show_id', None)
    context.user_data.pop('auto_index_show_name', None)
    
    if indexed_count > 0:
        seasons = await db.get_seasons_for_show(show_id)
        total_episodes = sum(count for _, count in seasons)
        
        status_msg = f"✅ Indexación completada:\n\n"
        status_msg += f"📺 <b>{show_name}</b>\n"
        status_msg += f"📹 {indexed_count} episodio(s) NUEVOS indexados\n"
        if skipped_count > 0:
            status_msg += f"⏭️ {skipped_count} ya existían (saltados)\n"
        status_msg += f"📊 Total en DB: {total_episodes} episodios\n\n"
        status_msg += f"Usa /start para buscar la serie."
        
        await update.message.reply_text(status_msg, parse_mode='HTML')
    else:
        if skipped_count > 0:
            await update.message.reply_text(
                f"ℹ️ No hay episodios nuevos.\n\n"
                f"⏭️ {skipped_count} episodio(s) ya estaban indexados.\n\n"
                f"Todo está al día! ✅",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                f"❌ No se encontraron episodios con formato #x#\n\n"
                f"Asegúrate de que los mensajes tengan el formato correcto en el caption (ej: 1x1, 2x5).",
                parse_mode='HTML'
            )
    
    return True

async def index_series_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /indexar_serie - Indexa una nueva serie con sus episodios
    
    Uso: /indexar_serie <nombre de la serie>
    Ejemplo: /indexar_serie Loki (2021)
    
    Después de indexar la serie, el admin debe responder a los mensajes del canal
    con el formato: S#x# (ej: S1x1, S2x5)
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
            f"⚠️ No se encontraron episodios con formato S#x# en el canal.\n\n"
            f"Puedes indexar manualmente respondiendo mensajes con:\n"
            f"<code>S1x1</code> (Temporada 1, Episodio 1)\n"
            f"<code>S2x5</code> (Temporada 2, Episodio 5)",
            parse_mode='HTML'
        )

async def index_episode_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja respuestas a mensajes del canal para indexar episodios
    Formato: #x# (ej: 1x1, 2x10)
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
    
    # Parsear formato #x# (puede estar en cualquier parte del texto)
    text = update.message.text.strip()
    pattern = r'(\d+)[xX](\d+)'
    match = re.search(pattern, text)
    
    if not match:
        return  # No es un formato válido, ignorar
    
    season_number = int(match.group(1))
    episode_number = int(match.group(2))
    
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
