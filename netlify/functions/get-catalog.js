const { createClient } = require('@supabase/supabase-js');

exports.handler = async (event, context) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Content-Type': 'application/json'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  try {
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_KEY;
    const botUsername = process.env.BOT_USERNAME || 'CineStelar_bot';

    if (!supabaseUrl || !supabaseKey) {
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ error: 'Supabase credentials not configured' })
      };
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    // Obtener películas
    const { data: movies, error: moviesError } = await supabase
      .from('videos')
      .select('id, title, original_title, year, overview, poster_url, backdrop_url, vote_average, runtime, genres, message_id')
      .order('id', { ascending: false });

    if (moviesError) throw moviesError;

    // Obtener series
    const { data: series, error: seriesError } = await supabase
      .from('tv_shows')
      .select('id, name, original_name, year, overview, poster_url, backdrop_url, vote_average, genres, number_of_seasons, status')
      .order('id', { ascending: false });

    if (seriesError) throw seriesError;

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        movies: movies || [],
        series: series || [],
        bot_username: botUsername,
        total_movies: movies?.length || 0,
        total_series: series?.length || 0
      })
    };

  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: error.message, movies: [], series: [] })
    };
  }
};
