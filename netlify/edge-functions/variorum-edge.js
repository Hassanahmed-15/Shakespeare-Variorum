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

      // Create SSE stream
      const stream = new ReadableStream({
        async start(controller) {
          try {
            // Send initial header
            controller.enqueue(new TextEncoder().encode('data: {"type": "start", "message": "Starting Full Fathom Five analysis..."}\n\n'));

            // Simplified Variorum prompt
            const fullPrompt = `You are providing a simplified but scholarly New Variorum Shakespeare-style commentary. Your analysis should capture the essential elements of Furness's approach while being more concise and accessible.

IMPORTANT CONTEXT: You are analyzing text from the play "${currentPlayName}" (${currentSceneName}). Always refer to this specific play and scene in your analysis.

MANDATORY FORMAT AND STRUCTURE:

## FULL FATHOM FIVE Analysis: "${text}" (${currentPlayName} ${currentSceneName})

### TEXTUAL VARIATIONS
Brief overview of key textual differences between early editions (Q1, F1, etc.) if any exist.

### CRITICAL COMMENTARY
Present 3-5 key critical interpretations chronologically with brief citations:
**YEAR CRITIC NAME** (*Work Title*): Brief summary of their interpretation.

Include major critics like Johnson, Coleridge, Hazlitt, and 1-2 modern scholars.

### PERFORMANCE HISTORY
How notable actors have interpreted this line (2-3 examples):
**ACTOR NAME** (period): Brief description of their interpretation.

### SOURCES & INFLUENCES
Brief mention of any known sources (Holinshed, Plutarch, etc.) or note if Shakespeare appears to have invented this.

### KEY WORDS & MEANINGS
Brief etymology and definitions of important words, preserving original capitalization.

### SHAKESPEAREAN PARALLELS
1-2 similar passages from other plays if relevant.

### DRAMATIC FUNCTION
How this passage works in the immediate scene and broader play structure.

### MODERN PERSPECTIVES
Brief mention of 1-2 modern critical approaches (feminist, psychoanalytic, etc.) if relevant.

### SYNTHESIS
Concise summary of the passage's significance and meaning.

LENGTH: 800-1200 words total

TONE: Scholarly but accessible. Focus on the most important insights rather than exhaustive detail.

Use <em>italics</em> for titles and preserve exact capitalization from the highlighted text.

Analyze this Shakespeare text: "${text}"`;

            // Send section start
            controller.enqueue(new TextEncoder().encode('data: {"type": "section", "message": "TEXTUAL COLLATION"}\n\n'));

            // Make Claude API call with streaming
            const claudePayload = {
              model: 'claude-sonnet-4-20250514',
              max_tokens: 2000,
              messages: [
                { role: 'user', content: fullPrompt }
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
            const content = claudeData.content[0].text;

            // Stream the content word by word
            const words = content.split(' ');
            for (let i = 0; i < words.length; i++) {
              const word = words[i];
              const isLastWord = i === words.length - 1;
              
              // Add space after word (except for last word)
              const wordWithSpace = isLastWord ? word : word + ' ';
              
              controller.enqueue(new TextEncoder().encode(`data: {"type": "content", "word": "${wordWithSpace}"}\n\n`));
              
              // Small delay to simulate streaming
              await new Promise(resolve => setTimeout(resolve, 50));
            }

            // Send completion signal
            controller.enqueue(new TextEncoder().encode('data: {"type": "complete"}\n\n'));
            controller.close();

          } catch (error) {
            console.error('Streaming error:', error);
            controller.enqueue(new TextEncoder().encode(`data: {"type": "error", "message": "${error.message}"}\n\n`));
            controller.close();
          }
        }
      });

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type'
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
