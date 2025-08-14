export default async (request, context) => {
  // Handle CORS
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
      }
    });
  }

  try {
    const CLAUDE_API_KEY = Deno.env.get('CLAUDE_API_KEY');
    
    if (!CLAUDE_API_KEY) {
      return new Response(JSON.stringify({ error: 'Claude API key not configured' }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }

    if (request.method === 'POST') {
      const { text, playName, sceneName } = await request.json();

      if (!text) {
        return new Response(JSON.stringify({ error: 'Text is required' }), {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }

      // Set default values for play and scene if not provided
      const currentPlayName = playName || 'Shakespeare';
      const currentSceneName = sceneName || 'scene';

      // Helper function for Claude API calls
      async function callClaude(prompt) {
        try {
          const claudePayload = {
            model: 'claude-sonnet-4-20250514',
            max_tokens: 2000,
            messages: [
              { role: 'user', content: prompt }
            ]
          };
          
          const claudeResponse = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
              'x-api-key': `${CLAUDE_API_KEY}`,
              'Content-Type': 'application/json',
              'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify(claudePayload)
          });
          
          if (!claudeResponse.ok) {
            throw new Error(`Claude API error: ${claudeResponse.status}`);
          }
          
          const claudeData = await claudeResponse.json();
          return claudeData.content[0].text;
        } catch (error) {
          console.error('Claude API error:', error);
          return "Section temporarily unavailable.";
        }
      }
      
      // Part 1: Textual Collation & Commentary History (~1000 words)
      const part1Prompt = `Provide ONLY these sections for "${text}" from ${currentPlayName} (${currentSceneName}):

### TEXTUAL COLLATION
List all variants (Q1, Q2, F1, F2, etc.) with exact spellings

### COMMENTARY HISTORY (Variorum Tradition)
Chronological critical commentary from 1709-1890s with full citations:
- Format: **YEAR NAME** (*Title*, City: Publisher, Year, p. X): "Commentary"
- Include: Rowe, Pope, Johnson, Steevens, Malone, Coleridge, Hazlitt, Furness

Maximum 1200 words. Be specific with citations. Use <em>italics</em> for titles.`;
      
      // Part 2: Performance & Sources (~1000 words)
      const part2Prompt = `Continue analysis of "${text}" with ONLY:

### PERFORMANCE TRADITION
How major actors delivered this line (Garrick, Kemble, Siddons, Irving, etc.)

### SOURCE STUDY
- Holinshed, Plutarch, Biblical parallels
- Note if "NOT in [source]"

### LINGUISTIC ARCHAEOLOGY
Etymology and contemporary usage of key words

Maximum 1000 words. Use <em>italics</em> for titles.`;
      
      // Part 3: Cross-references & Controversies (~1000 words)
      const part3Prompt = `Continue analysis of "${text}" with ONLY:

### CROSS-REFERENCES IN SHAKESPEARE
Similar passages across the canon

### CRITICAL CONTROVERSIES
Major interpretive debates

### DRAMATURGICAL SIGNIFICANCE
Function in scene, character, play structure

Maximum 1000 words. Use <em>italics</em> for titles.`;
      
      // Part 4: Modern Perspectives & Synthesis (~800 words)
      const part4Prompt = `Complete analysis of "${text}" with:

### MODERN CRITICAL PERSPECTIVES
Brief: Psychoanalytic, Feminist, New Historicist, etc.

### SYNTHESIS
Comprehensive summary in Furness's style, weighing all evidence

Maximum 800 words. Use <em>italics</em> for titles.`;
      
      // Make all 4 API calls
      console.log('Making Part 1 API call...');
      const part1 = await callClaude(part1Prompt);
      
      console.log('Making Part 2 API call...');
      const part2 = await callClaude(part2Prompt);
      
      console.log('Making Part 3 API call...');
      const part3 = await callClaude(part3Prompt);
      
      console.log('Making Part 4 API call...');
      const part4 = await callClaude(part4Prompt);
      
      // Combine all parts
      const combinedContent = `## FULL FATHOM FIVE Analysis: "${text}" (${currentPlayName} ${currentSceneName})

${part1}

${part2}

${part3}

${part4}`;
      
      return new Response(JSON.stringify({
        choices: [{
          message: {
            content: combinedContent
          }
        }]
      }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }

    // Health check
    if (request.method === 'GET') {
      return new Response(JSON.stringify({ 
        status: 'ok', 
        claude: !!CLAUDE_API_KEY
      }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }

  } catch (error) {
    console.error('Edge function error:', error);
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
};
