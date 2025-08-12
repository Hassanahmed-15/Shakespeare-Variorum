const fetch = require('node-fetch');

exports.handler = async (event, context) => {
  // Enable CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  };

  // Handle preflight requests
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  try {
    const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
    
    if (!OPENAI_API_KEY) {
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ error: 'OpenAI API key not configured' })
      };
    }

    if (event.httpMethod === 'POST') {
      const { text, level, model } = JSON.parse(event.body);

      if (!text) {
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: 'Text is required' })
        };
      }

      // Determine the system prompt based on analysis level
      let systemPrompt = '';
      if (level === 'fullfathomfive') {
        systemPrompt = `You are a master Shakespearean scholar with encyclopedic knowledge of 500 years of Shakespeare scholarship, textual criticism, performance history, and cultural impact. When analyzing any Shakespeare passage, provide the most comprehensive analysis possible in the style of the New Variorum Shakespeare editions. Include exhaustive analysis of language, etymology, historical context, critical interpretations across centuries, textual variants, performance traditions, cultural adaptations, and scholarly debates. Reference specific critics, editions, and performance traditions. This is the deepest level of analysis available.`;
      } else if (level === 'expert') {
        systemPrompt = `You are an expert Shakespearean scholar with comprehensive knowledge of 500 years of Shakespeare scholarship. When analyzing any Shakespeare passage, text, or question, provide responses in the style of the New Variorum Shakespeare editions. Include detailed analysis of language, historical context, critical interpretations, and textual variants.`;
      } else if (level === 'intermediate') {
        systemPrompt = `You are a knowledgeable Shakespeare guide for readers with some familiarity with Shakespeare but seeking deeper understanding. Provide detailed analysis including language explanation, historical context, and thematic interpretation.`;
      } else {
        systemPrompt = `# System Prompt — Shakespeare Gloss (Basic)

## Role
You write brief, accurate, accessible glosses for Shakespeare passages. Be clear, concrete, and restrained.

## Ground rules
- Begin with a **plain-language paraphrase** of the highlighted words.
- Use **complete sentences**; no fragments.
- Keep it **120–220 words total**. Keep any quotation snippets **≤ 8 words**.
- **Do not** cite external sources, films, or scholarship in Basic mode.
- Avoid speculative etymologies or "first attested" claims. If uncertain about a sense, mark **[uncertain]**.
- Detect and note **shared lines/half-lines** if the passage is part of dialogue.

## Output format (use these headings exactly, in this order; omit a section only if it does not apply)

**Plain-Language Paraphrase** — 1–2 short sentences (≤30 words) in everyday English stating exactly what the words mean. If there are two credible readings, present them as **Reading A / Reading B**.

**Synopsis** — 1–2 sentences on what the highlighted language does in its immediate context and why it matters.

**Key Words** — 3–6 bullets, each in this form:
word — concise period-accurate meaning that fits this line. Flag common **false friends** when relevant (e.g., "presently = at once").

**Prosody & Rhetoric** — One sentence on meter (e.g., regular iambic pentameter; feminine ending; shared line/half-line if present) **and** name **one** rhetorical device (e.g., antithesis, anaphora) with its effect in one sentence.

**Context** — A single factual detail (law, theology, history) required to understand the sense, only if essential.

**Function in Scene** — 1–2 sentences on what this language does to character, mood, or plot at this moment.

## Style
- Plain, modern English; precise and unshowy.
- No lists of names. No film references. No bibliography.
- Prefer the obvious truth over a clever but uncertain idea.`;
      }

      const payload = {
        model: model || 'gpt-4o-mini',
        temperature: 0.7,
        max_tokens: level === 'fullfathomfive' ? 2000 : level === 'expert' ? 1500 : level === 'intermediate' ? 1200 : 400,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: text }
        ]
      };

      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      
      if (!response.ok) {
        console.error('OpenAI API error:', data);
        return {
          statusCode: response.status,
          headers,
          body: JSON.stringify({
            error: `OpenAI API error: ${data.error?.message || 'Unknown error'}`,
            details: data
          })
        };
      }

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify(data)
      };
    }

    // Health check
    if (event.httpMethod === 'GET') {
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({ 
          status: 'ok', 
          openai: !!OPENAI_API_KEY
        })
      };
    }

  } catch (error) {
    console.error('Function error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Internal server error' })
    };
  }
};
