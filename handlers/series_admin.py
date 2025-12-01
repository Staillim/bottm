"""
Comandos de administración para indexar series
"""
from telegram import Update
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.tmdb_api import TMDBApi
from config.settings import CHANNEL_ID, ADMIN_IDS
import re
import logging

db = DatabaseManager()
tmdb = TMDBApi()
logger = logging.getLogger(__name__)

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
    
    # Guardar ID de la serie en el contexto del usuario para las siguientes operaciones
    context.user_data['indexing_show_id'] = show.id
    context.user_data['indexing_show_name'] = show.name
    
    await update.message.reply_text(
        f"✅ Serie indexada correctamente:\n\n"
        f"📺 <b>{show.name}</b> ({show.year})\n"
        f"🎬 Temporadas: {show.number_of_seasons}\n"
        f"⭐ Calificación: {show.vote_average}/10\n\n"
        f"Ahora puedes empezar a indexar episodios.\n"
        f"Reenvía mensajes del canal y responde con el formato:\n"
        f"<code>S1x1</code> (Temporada 1, Episodio 1)\n"
        f"<code>S2x5</code> (Temporada 2, Episodio 5)\n\n"
        f"O usa el comando /indexar_episodio",
        parse_mode='HTML'
    )

async def index_episode_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja respuestas a mensajes del canal para indexar episodios
    Formato: S#x# (ej: S1x1, S2x10)
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
    
    # Parsear formato S#x#
    text = update.message.text.strip()
    pattern = r'^[Ss](\d+)[xX](\d+)$'
    match = re.match(pattern, text)
    
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
