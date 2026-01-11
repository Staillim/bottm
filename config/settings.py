import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'CineStelar_bot')
VERIFICATION_CHANNEL_ID = int(os.getenv('VERIFICATION_CHANNEL_ID'))
VERIFICATION_CHANNEL_USERNAME = os.getenv('VERIFICATION_CHANNEL_USERNAME')
STORAGE_CHANNEL_ID = int(os.getenv('STORAGE_CHANNEL_ID'))

# Lista de canales donde publicar (separados por coma)
# Puede ser vacío para solo usar VERIFICATION_CHANNEL_ID
PUBLICATION_CHANNELS = [
    int(id.strip()) 
    for id in os.getenv('PUBLICATION_CHANNELS', '').split(',') 
    if id.strip() and id.strip().lstrip('-').isdigit()
]

# Si no hay canales adicionales configurados, usar solo el de verificación
if not PUBLICATION_CHANNELS:
    PUBLICATION_CHANNELS = [VERIFICATION_CHANNEL_ID]
elif VERIFICATION_CHANNEL_ID not in PUBLICATION_CHANNELS:
    # Asegurar que el canal de verificación siempre esté incluido
    PUBLICATION_CHANNELS.insert(0, VERIFICATION_CHANNEL_ID)

# Lista de grupos donde enviar notificaciones de nuevas películas/series (separados por coma)
NOTIFICATION_GROUPS = [
    int(id.strip()) 
    for id in os.getenv('NOTIFICATION_GROUPS', '').split(',') 
    if id.strip() and id.strip().lstrip('-').isdigit()
]

DATABASE_URL = os.getenv('DATABASE_URL')
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:5000/ad_viewer.html')
API_SERVER_URL = os.getenv('API_SERVER_URL', 'http://localhost:5000')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
