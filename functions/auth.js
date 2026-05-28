const { createClient } = require('@supabase/supabase-js');
const bcrypt = require('bcryptjs');
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

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers: corsHeaders(), body: '' };
  }

  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return respond(500, { error: 'Server configuration error: missing Supabase credentials' });
  }

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

  let body;
  try {
    body = JSON.parse(event.body || '{}');
  } catch {
    return respond(400, { error: 'Invalid JSON body' });
  }

  const { action } = body;

  // ── REGISTER ──────────────────────────────────────────────────────────────
  if (action === 'register') {
    const { email, password, name } = body;

    if (!email || !password || !name) {
      return respond(400, { error: 'email, password, and name are required' });
    }
    if (password.length < 8) {
      return respond(400, { error: 'Password must be at least 8 characters' });
    }

    // Check if user already exists
    const { data: existing } = await supabase
      .from('users')
      .select('id')
      .eq('email', email.toLowerCase())
      .single();

    if (existing) {
      return respond(409, { error: 'An account with this email already exists' });
    }

    const password_hash = await bcrypt.hash(password, 12);

    const { data: user, error } = await supabase
      .from('users')
      .insert({ email: email.toLowerCase(), password_hash, name })
      .select('id, email, name, created_at')
      .single();

    if (error) {
      console.error('Register error:', error);
      return respond(500, { error: 'Failed to create account' });
    }

    const token = jwt.sign({ userId: user.id, email: user.email, name: user.name }, JWT_SECRET, { expiresIn: '30d' });

    return respond(201, { token, user: { id: user.id, email: user.email, name: user.name } });
  }

  // ── LOGIN ─────────────────────────────────────────────────────────────────
  if (action === 'login') {
    const { email, password } = body;

    if (!email || !password) {
      return respond(400, { error: 'email and password are required' });
    }

    const { data: user, error } = await supabase
      .from('users')
      .select('id, email, name, password_hash')
      .eq('email', email.toLowerCase())
      .single();

    if (error || !user) {
      return respond(401, { error: 'Invalid email or password' });
    }

    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) {
      return respond(401, { error: 'Invalid email or password' });
    }

    const token = jwt.sign({ userId: user.id, email: user.email, name: user.name }, JWT_SECRET, { expiresIn: '30d' });

    return respond(200, { token, user: { id: user.id, email: user.email, name: user.name } });
  }

  // ── VERIFY TOKEN ──────────────────────────────────────────────────────────
  if (action === 'verify') {
    const { token } = body;
    if (!token) return respond(400, { error: 'token is required' });

    try {
      const decoded = jwt.verify(token, JWT_SECRET);
      return respond(200, { valid: true, user: { userId: decoded.userId, email: decoded.email, name: decoded.name } });
    } catch {
      return respond(401, { valid: false, error: 'Token invalid or expired' });
    }
  }

  return respond(400, { error: 'Unknown action. Use: register, login, or verify' });
};
