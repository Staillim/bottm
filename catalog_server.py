from flask import Flask, jsonify, send_file
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Conexión directa a PostgreSQL con Transaction pooler
DB_URL = "postgresql://postgres.gbbddmpgjnuxyvitkkoz:Staillim@aws-0-us-west-2.pooler.supabase.com:6543/postgres"
BOT_USERNAME = os.getenv('BOT_USERNAME', 'CineStelar_bot')

def get_db_connection():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

@app.route('/catalog')
def catalog():
    return send_file('webapp/catalog_supabase.html')

@app.route('/api/movies')
def get_movies():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, original_title, year, overview, 
                   poster_url, backdrop_url, vote_average, runtime, genres
            FROM videos 
            ORDER BY id DESC
        """)
        movies = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"movies": movies})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/series')
def get_series():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, original_name, year, overview, 
                   poster_url, backdrop_url, vote_average, 
                   genres, number_of_seasons, status
            FROM tv_shows 
            ORDER BY id DESC
        """)
        series = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"series": series})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bot-info')
def get_bot_info():
    """Retorna información del bot para deep linking"""
    return jsonify({
        "bot_username": BOT_USERNAME,
        "deep_link_base": f"https://t.me/{BOT_USERNAME}"
    })

if __name__ == '__main__':
    print("🚀 Servidor de catálogo iniciado en http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
