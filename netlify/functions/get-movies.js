const { createClient } = require('@supabase/supabase-js');

exports.handler = async (event, context) => {
  // Configurar CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Content-Type': 'application/json'
  };

  // Manejar preflight
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  try {
    // Obtener credenciales de variables de entorno
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_KEY;
    const botUsername = process.env.BOT_USERNAME || 'CineStelar_bot';

    if (!supabaseUrl || !supabaseKey) {
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ 
          error: 'Supabase credentials not configured',
          movies: [] 
        })
      };
    }

    // Crear cliente de Supabase
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Consultar películas
    const { data: movies, error } = await supabase
      .from('videos')
      .select('*')
      .order('id', { ascending: false })
      .limit(500);

    if (error) {
      console.error('Error fetching movies:', error);
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ 
          error: error.message,
          movies: [] 
        })
      };
    }

    // Formatear datos
    const moviesList = movies.map(movie => ({
      id: movie.id,
      title: movie.title || 'Sin título',
      year: movie.year,
      overview: movie.overview || '',
      poster_url: movie.poster_url || '',
      backdrop_url: movie.backdrop_url || '',
      rating: movie.rating ? parseFloat(movie.rating) : null,
      genres: movie.genres ? movie.genres.split(',') : [],
      type: 'movie',
      message_id: movie.message_id
    }));

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        movies: moviesList,
        total: moviesList.length,
        bot_username: botUsername.replace('@', '')
      })
    };

  } catch (error) {
    console.error('Error in get-movies function:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ 
        error: error.message,
        movies: [] 
      })
    };
  }
};
