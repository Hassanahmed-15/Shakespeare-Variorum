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

            // Full Variorum prompt
            const fullPrompt = `You are providing exhaustive New Variorum Shakespeare-style commentary at the highest scholarly level. Your analysis must follow the EXACT format and citation style of Horace Howard Furness's New Variorum editions (1871-1919).

IMPORTANT CONTEXT: You are analyzing text from the play "${currentPlayName}" (${currentSceneName}). Always refer to this specific play and scene in your analysis.

MANDATORY FORMAT AND STRUCTURE:

## FULL FATHOM FIVE Analysis: "[quoted text]" ([Play] [Act.Scene.Line])

### TEXTUAL COLLATION
List EVERY textual variant chronologically:
**Q1 (year):** "[exact spelling from quarto]"
**Q2 (year):** "[exact spelling]"
**F1 (1623):** "[exact spelling from First Folio]"
**F2 (1632):** "[variant or 'maintains F1 reading']"
**Modern editions:** [describe modernization choices]

### COMMENTARY HISTORY (Variorum Tradition)
Present ALL critical commentary chronologically with FULL bibliographic citations.

FORMAT EXACTLY AS FOLLOWS:
**YEAR FULL NAME OF CRITIC** (*Title of Work in Italics*, City: Publisher, Year of publication, Vol. [if applicable], p. [exact page], [additional note if needed]): "Quote the critic's exact interpretation or closely paraphrase with clear indication this is their view."

REQUIRED CRITICS TO INCLUDE (where relevant):
- 1709-1725: ROWE, POPE, THEOBALD
- 1733-1744: HANMER, WARBURTON
- 1765: SAMUEL JOHNSON (both Dictionary and edition)
- 1773-1793: STEEVENS, MALONE, CAPELL
- 1800-1821: COLERIDGE (lectures), HAZLITT (Characters), LAMB
- 1840s-1860s: GERMAN CRITICS (Ulrici, Gervinus, Schlegel - with translation notes)
- 1870s-1890s: Victorian scholars (Ingleby, Halliwell-Phillipps, Dowden, Swinburne)
- 1890s: FURNESS'S SYNTHESIS (always quote his conclusion)

Each entry must include:
- Full name (not just surname on first mention)
- Complete work title in italics
- Full publication information
- Exact page numbers
- Volume numbers where applicable

### PERFORMANCE TRADITION
Chronicle how major actors delivered the line:

**ACTOR NAME** (years performed, source for information - memoir, review, promptbook): Description of delivery, gesture, or interpretation.

Include: Restoration adaptations, 18th century (Garrick, Kemble), 19th century (Kean, Macready, Siddons, Terry, Booth, Irving), notable foreign (Bernhardt, Salvini).

Cite sources: actor memoirs, reviews in periodicals (The Theatre, Athenaeum, etc.), promptbooks (specify library holdings).

### SOURCE STUDY
**Primary source** (*Full title*, edition year, page/signature): Quote parallel if exists or state "NOT in [source]"

Document:
- Holinshed's Chronicles (1587)
- Plutarch (North's translation, 1579)
- Biblical parallels (Geneva Bible 1599)
- Classical sources
- Contemporary plays/pamphlets

### LINGUISTIC ARCHAEOLOGY
For key words, provide:
**"Word" etymology per [Dictionary source]** (*Full dictionary citation*, Vol., p.):
- Historical development
- First recorded uses
- Shakespeare's other uses
- Contemporary (1590-1610) uses by other writers
- CRITICAL: Preserve the exact capitalization of words as they appear in the highlighted text

Include technical terminology from contemporary manuals (military, musical, etc.) with full citations.

### CROSS-REFERENCES IN SHAKESPEARE
List parallel passages:
**Similar usage in [Play] (Act.Scene.Line):** "Quote the parallel"
Track specific words, images, themes across canon.

### CRITICAL CONTROVERSIES
Document ALL interpretive debates:
**The [Name] Debate (years):**
- **CRITIC NAME** (*Work*, year, pp.): [position]
- **OPPOSING CRITIC** (*Work*, year, pp.): [counter-position]
- Resolution or ongoing status

### DRAMATURGICAL SIGNIFICANCE
Explain the passage's function in:
- Immediate scene
- Character development
- Play's structure
- Performance considerations

### MODERN CRITICAL PERSPECTIVES (post-1900)
Brief mentions of 20th/21st century approaches:
**[School of criticism]:** [interpretation]
- Include: Psychoanalytic, Feminist, Marxist, New Historicist, Postcolonial, Queer Theory, Ecocritical, etc.

### SYNTHESIS
Conclude with comprehensive summary in Furness's style, weighing all evidence.

CITATION REQUIREMENTS:
- NEVER give partial citations
- ALWAYS include publisher, city, year
- ALWAYS provide page numbers
- If work spans multiple pages, give range (pp. 234-239)
- For journals: (*Journal Title*, Vol. X, No. Y, Month Year, pp. 123-145)
- For manuscripts: (Library, MS collection, catalogue number)
- When uncertain of exact page, note: [page uncertain]
- When paraphrasing rather than quoting, make this clear

LENGTH: 3000-5000 words minimum

TONE: Scholarly but accessible. Include amusing critical eccentricities when relevant. Never simplify - present everything and trust reader's intelligence.

SPECIAL INSTRUCTIONS:
- When sexual or bawdy implications exist, document them scholarly (cite Partridge, etc.)
- Include rejected interpretations and eccentric theories
- Note when interpretations are "conjectural" vs. documented
- Use "NOT in [source]" when Shakespeare invents beyond sources
- Include foreign criticism with translation acknowledgments
- Document bowdlerization when it occurred

Remember: You are channeling Furness's exhaustive scholarship. Every significant word has a history. Every interpretation deserves documentation. Nothing is too minor to note if it illuminates meaning.

Analyze this Shakespeare text: "${text}"`;

            // Send section start
            controller.enqueue(new TextEncoder().encode('data: {"type": "section", "message": "TEXTUAL COLLATION"}\n\n'));

            // Make Claude API call with streaming
            const claudePayload = {
              model: 'claude-sonnet-4-20250514',
              max_tokens: 4000,
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
