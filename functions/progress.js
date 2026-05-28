const { createClient } = require('@supabase/supabase-js');
const jwt = require('jsonwebtoken');

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const JWT_SECRET = process.env.JWT_SECRET || 'shakespeare-variorum-secret-change-in-prod';

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Content-Type': 'application/json',
  };
}

function respond(statusCode, body) {
  return { statusCode, headers: corsHeaders(), body: JSON.stringify(body) };
}

function getUserFromToken(event) {
  const auth = event.headers.authorization || event.headers.Authorization || '';
  const token = auth.replace(/^Bearer\s+/i, '');
  if (!token) return null;
  try { return jwt.verify(token, JWT_SECRET); } catch { return null; }
}

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers: corsHeaders(), body: '' };
  }

  const user = getUserFromToken(event);
  if (!user) return respond(401, { error: 'Unauthorized' });

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

  // ── GET all progress for user ─────────────────────────────────────────────
  if (event.httpMethod === 'GET') {
    const { data, error } = await supabase
      .from('reading_progress')
      .select('play, scene, scene_index, total_scenes, last_read_at')
      .eq('user_id', user.userId)
      .order('last_read_at', { ascending: false });

    if (error) return respond(500, { error: 'Failed to fetch progress' });
    return respond(200, { progress: data });
  }

  // ── POST — upsert progress for a play ─────────────────────────────────────
  if (event.httpMethod === 'POST') {
    let body;
    try { body = JSON.parse(event.body || '{}'); } catch { return respond(400, { error: 'Invalid JSON' }); }

    const { play, scene, scene_index, total_scenes } = body;
    if (!play || !scene) return respond(400, { error: 'play and scene are required' });

    const { error } = await supabase
      .from('reading_progress')
      .upsert({
        user_id: user.userId,
        play,
        scene,
        scene_index: scene_index || 0,
        total_scenes: total_scenes || 0,
        last_read_at: new Date().toISOString(),
      }, { onConflict: 'user_id,play' });

    if (error) {
      console.error('Progress upsert error:', error);
      return respond(500, { error: 'Failed to save progress' });
    }

    return respond(200, { success: true });
  }

  return respond(405, { error: 'Method not allowed' });
};
