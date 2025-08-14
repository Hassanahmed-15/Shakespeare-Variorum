const fetch = require('node-fetch');

exports.handler = async (event, context) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
  };

  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  try {
    const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
    const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY;
    
    if (!OPENAI_API_KEY) {
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ error: 'OpenAI API key not configured' })
      };
    }

    if (event.httpMethod === 'POST') {
      const { text, level, model, playName, sceneName } = JSON.parse(event.body);

      if (!text) {
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: 'Text is required' })
        };
      }

      // Set default values for play and scene if not provided
      const currentPlayName = playName || 'Shakespeare';
      const currentSceneName = sceneName || 'scene';

      // Define the uniform structure for all analysis levels
      const analysisStructure = {
        basic: [
          'Plain-Language Paraphrase',
          'Synopsis',
          'Key Words & Glosses',
          'Pointers for Further Reading'
        ],

        expert: [
          'Plain-Language Paraphrase',
          'Synopsis',
          'Textual Variants',
          'Key Words & Glosses',
          'Historical Context',
          'Sources',
          'Literary Analysis',
          'Critical Reception',
          'Similar phrases or themes in other plays',
          'Pointers for Further Reading'
        ],
        fullfathomfive: [
          'TEXTUAL COLLATION',
          'COMPLETE COMMENTARY HISTORY',
          'PERFORMANCE TRADITION',
          'SOURCE STUDY',
          'LINGUISTIC ARCHAEOLOGY',
          'THE GREAT DEBATES',
          'CROSS-REFERENCES',
          'VARIORUM SPECIAL FEATURES',
          'MODERN SUPPLEMENTS'
        ]
      };

      // Get the sections for this level
      const sections = analysisStructure[level] || analysisStructure.basic;

      // Create the system prompt based on level
      let systemPrompt = '';
      
      if (level === 'basic') {
        systemPrompt = `You are a university professor speaking to very smart undergraduates about Shakespeare. 

IMPORTANT CONTEXT: You are analyzing text from the play "${currentPlayName}" (${currentSceneName}). Always refer to this specific play and scene in your analysis.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order. Do not skip any sections:

**Plain-Language Paraphrase:**
**Synopsis:**
**Key Words & Glosses:**
**Pointers for Further Reading:**

FORMAT REQUIREMENTS:
- Use EXACTLY the section headers shown above - do not change them
- Do not add any additional colons to the headers
- Provide 2-4 sentences for each section
- Use complete sentences and paragraphs
- Write in clear, accessible language
- If a section seems inapplicable, still provide a brief explanation of why
- Avoid abbreviations and shorthand
- CRITICAL: Write ALL book titles, play titles, movie titles, films, novels, articles, and scholarly works in <em>italics</em> (e.g., <em>Macbeth</em>, <em>Hamlet</em>, <em>First Folio</em>, <em>The Chronicles of Scotland England, and Ireland</em>)
- NEVER use quotation marks for titles - always use <em>italics</em>
- NEVER put book titles, play titles, or any media titles in quotation marks
- NEVER use asterisks (*) for titles - always use <em>italics</em>
- NEVER italicize author names - keep them in plain text (e.g., A.C. Bradley, Janet Adelman, Harold Bloom)
- Always write "A.C. Bradley" (not "A. circa Bradley" or "A. C. Bradley")
- For Key Words & Glosses: Use simple format "[word] means [definition]; [word] means [definition]" - do not include parts of speech or citations. Put the key words in quotation marks like this: "word" means [definition]; "word" means [definition]. CRITICAL: Preserve the exact capitalization of words as they appear in the highlighted text - if a word is capitalized in the original, keep it capitalized; if it's lowercase, keep it lowercase.
- For Similar phrases or themes in other plays: Do NOT include any cross-references to other Shakespeare plays. Focus only on explaining the highlighted passage itself.
- Use proper academic formatting
- Always reference the specific play "${currentPlayName}" and scene "${currentSceneName}" in your analysis

EXAMPLE FORMAT:
**Plain-Language Paraphrase:** This passage from ${playName} means [explanation in simple terms].

**Synopsis:** This language in ${playName} [what it does in context].

**Key Words & Glosses:** "word" means [definition]; "word" means [definition].

**Pointers for Further Reading:** Consider reading [suggestions].`;

      } else if (level === 'expert') {
        systemPrompt = `CRITICAL FORMATTING RULE: You MUST use EXACTLY these section headers and add ONE colon after each. DO NOT add extra colons:

**Plain-Language Paraphrase**
**Synopsis**
**Textual Variants**
**Key Words & Glosses**
**Historical Context**
**Sources**
**Literary Analysis**
**Critical Reception**
**Similar phrases or themes in other plays**
**Pointers for Further Reading**

EXAMPLE OF CORRECT FORMAT:
**Sources:** [content here]
**Similar phrases or themes in other plays:** [content here]

You are an expert Shakespearean scholar with comprehensive knowledge of 500 years of Shakespeare scholarship.

IMPORTANT CONTEXT: You are analyzing text from the play "${playName}" (${sceneName}). Always refer to this specific play and scene in your analysis.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order. Do not skip any sections. Add ONE colon after each header.

WARNING: Use "Sources:" NOT "Sources::". Use "Similar phrases or themes in other plays:" NOT "Similar phrases or themes in other plays::". NEVER add extra colons.
- Provide 4-8 sentences for each section
- Use complete sentences and paragraphs
- Include detailed analysis with specific citations and evidence
- Avoid abbreviations and shorthand
- CRITICAL: Write ALL book titles, play titles, movie titles, films, novels, articles, and scholarly works in <em>italics</em> (e.g., <em>Macbeth</em>, <em>Hamlet</em>, <em>First Folio</em>, <em>Romeo and Juliet</em>, <em>The Tempest</em>, <em>The Chronicles of Scotland England, and Ireland</em>)
- NEVER use quotation marks for titles - always use <em>italics</em>
- NEVER put book titles, play titles, or any media titles in quotation marks
- ALWAYS italicize ALL titles - this is non-negotiable
- NEVER use asterisks (*) for titles - always use <em>italics</em>
- NEVER italicize author names - keep them in plain text (e.g., A.C. Bradley, Janet Adelman, Harold Bloom)
- Always write "A.C. Bradley" (not "A. circa Bradley" or "A. C. Bradley")
- Use proper academic formatting
- For Textual Variants: If no variants exist, state "Early editions are identical to Folger."
- Include scholarly references and critical perspectives
- For Key Words & Glosses: Use the 1914 Oxford English Dictionary (OED) for definitions, Arden critical notes for contextual meanings, and A Shakespeare Glossary (Oxford: Clarendon Press, 1911) for Shakespeare-specific usage. Use simple format "[word] means [definition]; [word] means [definition]" - do not include parts of speech or citations. Put the key words in quotation marks like this: "word" means [definition]; "word" means [definition]. 

CRITICAL CAPITALIZATION RULE: Look at the highlighted Shakespeare text. If a word appears as "screw" in the original, use "screw" not "Screw". If a word appears as "Macbeth" in the original, use "Macbeth" not "macbeth". Copy the EXACT capitalization from the highlighted text. This is non-negotiable.
- For Similar phrases or themes in other plays: Include 3-5 thematically related passages from other Shakespeare plays. Find passages that share: similar imagery, parallel themes, echoed language, or comparable dramatic situations. Explain the literary connection. Format: 'Thematic parallel in [Play] (Act.Scene if known): "[quote]" - [explanation of connection]'. When finding similar passages, search for: exact phrase repetitions, parallel metaphors (life as theater, time as thief, love as madness), similar imagery clusters (darkness/light, storm/calm, garden/wilderness), rhetorical patterns (questions, lists, paradoxes), and recurring themes (appearance vs reality, order vs chaos, nature vs nurture).
- For Sources: Identify specific sources Shakespeare drew on for plot, character, or content. Include primary sources (Plutarch's Lives, Holinshed's Chronicles, North's translation), earlier plays he adapted (Kyd's Spanish Tragedy, Marlowe's works), contemporary works, classical sources, medieval romances, or other influences. Explain how Shakespeare transformed or adapted these sources.
- Always reference the specific play "${currentPlayName}" and scene "${currentSceneName}" in your analysis

EXAMPLE FORMAT:
**Plain-Language Paraphrase:** This passage from ${currentPlayName} means [explanation in simple terms].

**Synopsis:** This language in ${currentPlayName} [what it does in context].

**Textual Variants:** [variants or "Early editions are identical to Folger."]

**Key Words & Glosses:** "word" means [definition]; "word" means [definition].

**Historical Context:** [relevant historical background in ${currentPlayName}].

**Sources:** [specific sources Shakespeare drew on for plot, character, or content - e.g., Plutarch, Holinshed, earlier plays, contemporary works, etc.].

**Literary Analysis:** [detailed literary analysis of ${currentPlayName}].

**Critical Reception:** [scholarly perspectives on ${currentPlayName}].

**Similar phrases or themes in other plays:** [connections to other Shakespeare plays and works].

**Pointers for Further Reading:** Consider reading [suggestions].`;
      } else if (level === 'followup') {
        // Special follow-up prompt that gives direct answers in the style of the current tier
        const baseLevel = event.body ? JSON.parse(event.body).baseLevel || 'basic' : 'basic';
        
        if (baseLevel === 'basic') {
          systemPrompt = `You are a helpful Shakespeare expert. Answer the user's question directly and clearly in a simple, accessible style.

IMPORTANT CONTEXT: You are answering questions about the play "${currentPlayName}" (${currentSceneName}). Always refer to this specific play and scene in your answers.

FORMAT REQUIREMENTS:
- Provide a direct, concise answer to the question
- Use clear, accessible language
- Include relevant facts and context when helpful
- Write ALL book titles, play titles, movie titles, and scholarly works in <em>italics</em> (e.g., <em>Macbeth</em>, <em>Hamlet</em>, <em>First Folio</em>)
- NEVER use asterisks (*) for titles - always use <em>italics</em>
- NEVER italicize author names - keep them in plain text (e.g., A.C. Bradley, Janet Adelman, Harold Bloom)
- Always write "A.C. Bradley" (not "A. circa Bradley" or "A. C. Bradley")
- Avoid unnecessary formatting or section headers
- Keep responses focused and to the point
- Always reference the specific play "${currentPlayName}" and scene "${currentSceneName}" in your answers

EXAMPLE FORMAT:
[Direct answer to the question with relevant context and facts about <em>${currentPlayName}</em>]`;
        } else if (baseLevel === 'expert') {
          systemPrompt = `You are a Shakespeare scholar. Answer the user's question with academic depth and scholarly insight.

IMPORTANT CONTEXT: You are answering questions about the play "${currentPlayName}" (${currentSceneName}). Always refer to this specific play and scene in your answers.

FORMAT REQUIREMENTS:
- Structure your answer with clear sections using <strong>bold headers</strong>
- Provide a comprehensive, scholarly answer to the question
- Include relevant historical context and critical perspectives
- Use academic language and cite specific details
- Write ALL book titles, play titles, movie titles, and scholarly works in <em>italics</em> (e.g., <em>Macbeth</em>, <em>Hamlet</em>, <em>Daemonologie</em>, <em>First Folio</em>)
- NEVER use asterisks (*) for titles - always use <em>italics</em>
- NEVER italicize author names - keep them in plain text (e.g., A.C. Bradley, Janet Adelman, Harold Bloom)
- Always write "A.C. Bradley" (not "A. circa Bradley" or "A. C. Bradley")
- Write in essay-style paragraphs - NO bullet points, NO numbering, NO lists
- Use flowing, connected sentences that build on each other
- Break up long paragraphs into readable sections
- Keep responses focused but thorough
- Always reference the specific play "${currentPlayName}" and scene "${currentSceneName}" in your answers

EXAMPLE FORMAT:

<strong>Direct Answer:</strong>
[Concise answer to the question]

<strong>Historical Context:</strong>
[Flowing essay paragraphs with connected sentences about historical background and context - NO bullet points or numbering]

<strong>Scholarly Evidence:</strong>
[Academic sources and evidence presented in essay format with smooth transitions between ideas]

<strong>Significance:</strong>
[Why this matters in the context of <em>${currentPlayName}</em>, written in flowing paragraphs]`;
        } else if (baseLevel === 'fullfathomfive') {
          systemPrompt = `You are a Shakespeare Variorum expert. Answer the user's question with the highest level of scholarly detail and comprehensive analysis.

IMPORTANT CONTEXT: You are answering questions about the play "${currentPlayName}" (${currentSceneName}). Always refer to this specific play and scene in your answers.

FORMAT REQUIREMENTS:
- Structure your answer with clear sections using <strong>bold headers</strong>
- Provide an exhaustive, scholarly answer to the question
- Include extensive historical context, critical reception, and performance history
- Use the most detailed academic language and cite specific evidence
- Write ALL book titles, play titles, movie titles, and scholarly works in <em>italics</em> (e.g., <em>Macbeth</em>, <em>Hamlet</em>, <em>Daemonologie</em>, <em>First Folio</em>)
- NEVER use asterisks (*) for titles - always use <em>italics</em>
- NEVER italicize author names - keep them in plain text (e.g., A.C. Bradley, Janet Adelman, Harold Bloom)
- Always write "A.C. Bradley" (not "A. circa Bradley" or "A. C. Bradley")
- Write in essay-style paragraphs - NO bullet points, NO numbering, NO lists
- Use flowing, connected sentences that build on each other
- Break up long paragraphs into readable sections
- Keep responses comprehensive and thorough
- Always reference the specific play "${currentPlayName}" and scene "${currentSceneName}" in your answers

EXAMPLE FORMAT:

<strong>Direct Answer:</strong>
[Comprehensive answer to the question]

<strong>Historical Context:</strong>
[Extensive historical background and context presented in flowing essay paragraphs - NO bullet points or numbering]

<strong>Scholarly Evidence:</strong>
[Detailed academic sources and evidence in essay format with smooth transitions]

<strong>Critical Reception:</strong>
[Scholarly perspectives and interpretations written in connected paragraphs]

<strong>Significance:</strong>
[Why this matters in the context of <em>${currentPlayName}</em>, presented in essay style]`;
        }
      } else if (level === 'fullfathomfive') {
        systemPrompt = `You are providing exhaustive New Variorum Shakespeare-style commentary at the highest scholarly level. Your analysis must follow the EXACT format and citation style of Horace Howard Furness's New Variorum editions (1871-1919).

IMPORTANT CONTEXT: You are analyzing text from the play "${playName}" (${sceneName}). Always refer to this specific play and scene in your analysis.

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
Include: Psychoanalytic, Feminist, Marxist, New Historicist, Postcolonial, Queer Theory, Ecocritical, etc.

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

Remember: You are channeling Furness's exhaustive scholarship. Every significant word has a history. Every interpretation deserves documentation. Nothing is too minor to note if it illuminates meaning.`;
      }

      // Smart model routing based on text length and analysis level
      let modelConfig = {
        model: 'gpt-4o-mini' // default
      };
      
      // Check text length for large source notes
      const textLength = text.length;
      const isLargeText = textLength > 5000; // Threshold for "huge source notes"
      
      if (level === 'basic') {
        modelConfig = {
          model: 'gpt-4.1-mini',
          temperature: 0.7
        };
      } else if (level === 'expert') {
        modelConfig = {
          model: 'gpt-4',
          temperature: 0.7
        };
      } else if (level === 'followup') {
        // Use appropriate model based on base level
        const baseLevel = event.body ? JSON.parse(event.body).baseLevel || 'basic' : 'basic';
        if (baseLevel === 'basic') {
          modelConfig = {
            model: 'gpt-4.1-mini',
            temperature: 0.7
          };
        } else if (baseLevel === 'expert') {
          modelConfig = {
            model: 'gpt-4',
            temperature: 0.7
          };
        } else if (baseLevel === 'fullfathomfive') {
          modelConfig = {
            model: 'gpt-4o',
            temperature: 0.7
          };
        }
      } else if (level === 'fullfathomfive') {
        // Use gpt-4o for Full Fathom Five for enhanced reasoning
        modelConfig = {
          model: 'gpt-4o',
          temperature: 0.7
        };
      }
      
      // Build payload with conditional temperature
      const payload = {
        model: modelConfig.model,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: `Analyze this Shakespeare text: "${text}"` }
        ]
      };
      
      // Only add temperature for models that support it
      if (modelConfig.temperature !== undefined) {
        payload.temperature = modelConfig.temperature;
      }
      
      // Add reasoning_effort for models that support it
      if (modelConfig.reasoning_effort !== undefined) {
        payload.reasoning_effort = modelConfig.reasoning_effort;
      }

      // Set max_tokens for Full Fathom Five to ensure complete responses
      if (level === 'fullfathomfive') {
        payload.max_tokens = 8000; // Ensure we get a full response
      }

      let response, data;
      try {
        console.log(`Starting API call for level: ${level}, text length: ${text.length}`);
        const startTime = Date.now();
        
        // Use Claude API for Full Fathom Five, OpenAI for other levels
        if (level === 'fullfathomfive') {
                  if (!CLAUDE_API_KEY) {
          return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Claude API key not configured for Full Fathom Five analysis' })
          };
        }
          
          // Claude API payload format
          const claudePayload = {
            model: "claude-3-5-sonnet-20241022",
            max_tokens: 8000,
            messages: [
              { role: 'user', content: `${systemPrompt}\n\nAnalyze this Shakespeare text: "${text}"` }
            ]
          };
          
                      response = await fetch('https://api.anthropic.com/v1/messages', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${CLAUDE_API_KEY}`,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
              },
              body: JSON.stringify(claudePayload),
              timeout: 300000 // 5 minute timeout for complex analyses
            });
        } else {
          // OpenAI API for Basic and Expert levels
          response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${OPENAI_API_KEY}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload),
            timeout: 300000 // 5 minute timeout for complex analyses
          });
        }

        const endTime = Date.now();
        console.log(`API call completed in ${endTime - startTime}ms`);

        data = await response.json();
      } catch (fetchError) {
        console.error('Fetch error:', fetchError);
        return {
          statusCode: 504,
          headers,
          body: JSON.stringify({
            error: 'Network timeout: The request took longer than 5 minutes to complete. Please try again or use a shorter text selection.',
            details: fetchError.message
          })
        };
      }
      
      if (!response.ok) {
        console.error(`${level === 'fullfathomfive' ? 'Claude' : 'OpenAI'} API error:`, data);
        
        // Special handling for timeout errors
        if (response.status === 504 || (data.error && data.error.message && data.error.message.includes('timeout'))) {
          return {
            statusCode: 504,
            headers,
            body: JSON.stringify({
              error: 'Analysis timeout: The request took longer than 5 minutes to process. This may happen with very complex passages. Please try again or use a shorter text selection.',
              details: data
            })
          };
        }
        
        return {
          statusCode: response.status,
          headers,
          body: JSON.stringify({
            error: `${level === 'fullfathomfive' ? 'Claude' : 'OpenAI'} API error: ${data.error?.message || 'Unknown error'}`,
            details: data
          })
        };
      }

      // Handle different response formats
      if (level === 'fullfathomfive') {
        // Claude API response format
        return {
          statusCode: 200,
          headers,
          body: JSON.stringify({
            choices: [{
              message: {
                content: data.content[0].text
              }
            }]
          })
        };
      } else {
        // OpenAI API response format (unchanged)
        return {
          statusCode: 200,
          headers,
          body: JSON.stringify(data)
        };
      }
    }

    // Health check
    if (event.httpMethod === 'GET') {
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({ 
          status: 'ok', 
          openai: !!OPENAI_API_KEY,
          claude: !!CLAUDE_API_KEY
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
