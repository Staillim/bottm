import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'CineStelar_bot')
VERIFICATION_CHANNEL_ID = int(os.getenv('VERIFICATION_CHANNEL_ID'))
VERIFICATION_CHANNEL_USERNAME = os.getenv('VERIFICATION_CHANNEL_USERNAME')
STORAGE_CHANNEL_ID = int(os.getenv('STORAGE_CHANNEL_ID'))
DATABASE_URL = os.getenv('DATABASE_URL')
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:5000/ad_viewer.html')
API_SERVER_URL = os.getenv('API_SERVER_URL', 'http://localhost:5000')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
