const { createClient } = require('@supabase/supabase-js');
const bcrypt = require('bcryptjs');
const nodemailer = require('nodemailer');

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const SMTP_HOST = process.env.SMTP_HOST;
const SMTP_PORT = parseInt(process.env.SMTP_PORT || '587');
const SMTP_USER = process.env.SMTP_USER;
const SMTP_PASS = process.env.SMTP_PASS;
const FROM_EMAIL = process.env.FROM_EMAIL || SMTP_USER;

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Content-Type': 'application/json',
  };
}

function respond(statusCode, body) {
  return { statusCode, headers: corsHeaders(), body: JSON.stringify(body) };
}

async function sendOTPEmail(toEmail, otp) {
  const transporter = nodemailer.createTransport({
    host: SMTP_HOST,
    port: SMTP_PORT,
    secure: SMTP_PORT === 465,
    auth: { user: SMTP_USER, pass: SMTP_PASS },
  });

  await transporter.sendMail({
    from: `"Shakespeare Digital NV" <${FROM_EMAIL}>`,
    to: toEmail,
    subject: 'Your password reset code',
    text: `Your password reset code is: ${otp}\n\nThis code expires in 15 minutes.\n\nIf you did not request this, please ignore this email.`,
    html: `
      <div style="font-family:system-ui,sans-serif;max-width:420px;margin:0 auto;padding:32px 24px;">
        <h2 style="font-size:20px;font-weight:700;color:#1d1d1f;margin-bottom:8px;">Reset your password</h2>
        <p style="color:#6e6e73;font-size:14px;margin-bottom:24px;">Enter this 6-digit code in the Shakespeare Digital NV app:</p>
        <div style="font-size:36px;font-weight:700;letter-spacing:10px;color:#1d1d1f;background:#f3f4f6;border-radius:10px;padding:20px;text-align:center;margin-bottom:24px;">${otp}</div>
        <p style="color:#86868b;font-size:12px;">This code expires in <strong>15 minutes</strong>. If you did not request a password reset, ignore this email.</p>
      </div>
    `,
  });
}

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers: corsHeaders(), body: '' };
  }

  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return respond(500, { error: 'Server configuration error' });
  }

  let body;
  try {
    body = JSON.parse(event.body || '{}');
  } catch {
    return respond(400, { error: 'Invalid JSON body' });
  }

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
    auth: { autoRefreshToken: false, persistSession: false }
  });

  const { action } = body;

  // ── SEND OTP ───────────────────────────────────────────────────────────────
  if (action === 'send-otp') {
    const { email } = body;
    if (!email) return respond(400, { error: 'email is required' });

    // Check user exists (but don't reveal if they don't)
    const { data: user } = await supabase
      .from('users')
      .select('id')
      .eq('email', email.toLowerCase())
      .single();

    if (!user) {
      return respond(200, { success: true }); // Silent — don't reveal non-existence
    }

    // Generate 6-digit OTP
    const otp = Math.floor(100000 + Math.random() * 900000).toString();
    const expires_at = new Date(Date.now() + 15 * 60 * 1000).toISOString();

    // Store in password_resets table
    const { error: dbError } = await supabase
      .from('password_resets')
      .upsert({ email: email.toLowerCase(), otp, expires_at }, { onConflict: 'email' });

    if (dbError) {
      console.error('DB error storing OTP:', dbError);
      return respond(500, { error: 'Failed to generate reset code' });
    }

    // Send email
    try {
      await sendOTPEmail(email.toLowerCase(), otp);
    } catch (emailErr) {
      console.error('Email send error:', emailErr);
      return respond(500, { error: 'Failed to send email. Please try again.' });
    }

    return respond(200, { success: true });
  }

  // ── VERIFY OTP + SET NEW PASSWORD ──────────────────────────────────────────
  if (action === 'reset') {
    const { email, otp, newPassword } = body;

    if (!email || !otp || !newPassword) {
      return respond(400, { error: 'email, otp, and newPassword are required' });
    }
    if (newPassword.length < 8) {
      return respond(400, { error: 'Password must be at least 8 characters' });
    }

    const { data: reset } = await supabase
      .from('password_resets')
      .select('otp, expires_at')
      .eq('email', email.toLowerCase())
      .single();

    if (!reset) {
      return respond(400, { error: 'No reset request found. Please request a new code.' });
    }
    if (new Date(reset.expires_at) < new Date()) {
      return respond(400, { error: 'Code has expired. Please request a new one.' });
    }
    if (reset.otp !== otp.trim()) {
      return respond(400, { error: 'Incorrect code. Please check and try again.' });
    }

    const password_hash = await bcrypt.hash(newPassword, 12);
    const { error } = await supabase
      .from('users')
      .update({ password_hash })
      .eq('email', email.toLowerCase());

    if (error) {
      console.error('Password update error:', error);
      return respond(500, { error: 'Failed to update password' });
    }

    // Clean up used OTP
    await supabase.from('password_resets').delete().eq('email', email.toLowerCase());

    return respond(200, { success: true });
  }

  return respond(400, { error: 'Unknown action. Use: send-otp or reset' });
};
