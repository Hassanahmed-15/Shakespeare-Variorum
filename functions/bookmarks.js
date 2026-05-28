const { createClient } = require('@supabase/supabase-js');
const jwt = require('jsonwebtoken');

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const JWT_SECRET = process.env.JWT_SECRET || 'shakespeare-variorum-secret-change-in-prod';

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
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
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch {
    return null;
  }
}

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers: corsHeaders(), body: '' };
  }

  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return respond(500, { error: 'Server configuration error: missing Supabase credentials' });
  }

  const user = getUserFromToken(event);
  if (!user) {
    return respond(401, { error: 'Unauthorized: valid JWT required' });
  }

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

  // ── GET bookmarks ─────────────────────────────────────────────────────────
  if (event.httpMethod === 'GET') {
    const { data, error } = await supabase
      .from('bookmarks')
      .select('id, play, scene, line, label, created_at')
      .eq('user_id', user.userId)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Get bookmarks error:', error);
      return respond(500, { error: 'Failed to fetch bookmarks' });
    }

    return respond(200, { bookmarks: data });
  }

  // ── POST — add bookmark ───────────────────────────────────────────────────
  if (event.httpMethod === 'POST') {
    let body;
    try {
      body = JSON.parse(event.body || '{}');
    } catch {
      return respond(400, { error: 'Invalid JSON body' });
    }

    const { play, scene, line, label } = body;

    if (!play || !scene) {
      return respond(400, { error: 'play and scene are required' });
    }

    // Prevent duplicate bookmarks for same play+scene+line
    const { data: existing } = await supabase
      .from('bookmarks')
      .select('id')
      .eq('user_id', user.userId)
      .eq('play', play)
      .eq('scene', scene)
      .eq('line', line || null)
      .single();

    if (existing) {
      return respond(409, { error: 'Bookmark already exists for this location' });
    }

    const { data: bookmark, error } = await supabase
      .from('bookmarks')
      .insert({
        user_id: user.userId,
        play,
        scene,
        line: line || null,
        label: label || null,
      })
      .select('id, play, scene, line, label, created_at')
      .single();

    if (error) {
      console.error('Add bookmark error:', error);
      return respond(500, { error: 'Failed to add bookmark' });
    }

    return respond(201, { bookmark });
  }

  // ── DELETE — remove bookmark ──────────────────────────────────────────────
  if (event.httpMethod === 'DELETE') {
    let body;
    try {
      body = JSON.parse(event.body || '{}');
    } catch {
      return respond(400, { error: 'Invalid JSON body' });
    }

    const { id } = body;
    if (!id) {
      return respond(400, { error: 'bookmark id is required' });
    }

    const { error } = await supabase
      .from('bookmarks')
      .delete()
      .eq('id', id)
      .eq('user_id', user.userId); // ensures users can only delete their own

    if (error) {
      console.error('Delete bookmark error:', error);
      return respond(500, { error: 'Failed to delete bookmark' });
    }

    return respond(200, { success: true });
  }

  return respond(405, { error: 'Method not allowed' });
};
