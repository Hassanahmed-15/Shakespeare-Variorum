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
        systemPrompt = `You are a friendly Shakespeare teacher helping general readers understand and appreciate Shakespeare. 

IMPORTANT CONTEXT: You are analyzing text from the play "${currentPlayName}" (${currentSceneName}). Always refer to this specific play and scene in your analysis.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order. Do not skip any sections:

${sections.map((section, index) => `**${section}:**`).join('\n')}

FORMAT REQUIREMENTS:
- Start each section with the exact heading format shown above
- Provide 2-4 sentences for each section
- Use complete sentences and paragraphs
- Write in clear, accessible language
- If a section seems inapplicable, still provide a brief explanation of why
- Avoid abbreviations and shorthand
- Write ALL book titles, play titles, movie titles, and scholarly works in <em>italics</em> (e.g., <em>Macbeth</em>, <em>Hamlet</em>, <em>First Folio</em>)
- NEVER use asterisks (*) for titles - always use <em>italics</em>
- NEVER italicize author names - keep them in plain text (e.g., A.C. Bradley, Janet Adelman, Harold Bloom)
- Always write "A.C. Bradley" (not "A. circa Bradley" or "A. C. Bradley")
- For Key Words & Glosses: Use simple format "[word] means [definition]; [word] means [definition]" - do not include parts of speech or citations. Put the key words in quotation marks like this: "word" means [definition]; "word" means [definition]
- For Similar phrases or themes in other plays: Do NOT include any cross-references to other Shakespeare plays. Focus only on explaining the highlighted passage itself.
- Use proper academic formatting
- Always reference the specific play "${currentPlayName}" and scene "${currentSceneName}" in your analysis

EXAMPLE FORMAT:
**Plain-Language Paraphrase:** This passage from ${playName} means [explanation in simple terms].

**Synopsis:** This language in ${playName} [what it does in context].

**Key Words & Glosses:** "word" means [definition]; "word" means [definition].

**Pointers for Further Reading:** Consider reading [suggestions].`;

      } else if (level === 'expert') {
        systemPrompt = `You are an expert Shakespearean scholar with comprehensive knowledge of 500 years of Shakespeare scholarship.

IMPORTANT CONTEXT: You are analyzing text from the play "${playName}" (${sceneName}). Always refer to this specific play and scene in your analysis.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order. Do not skip any sections:

${sections.map((section, index) => `**${section}:**`).join('\n')}

FORMAT REQUIREMENTS:
- Start each section with the exact heading format shown above
- Provide 4-8 sentences for each section
- Use complete sentences and paragraphs
- Include detailed analysis with specific citations and evidence
- Avoid abbreviations and shorthand
- Write ALL book titles, play titles, movie titles, and scholarly works in <em>italics</em> (e.g., <em>Macbeth</em>, <em>Hamlet</em>, <em>First Folio</em>)
- NEVER use asterisks (*) for titles - always use <em>italics</em>
- NEVER italicize author names - keep them in plain text (e.g., A.C. Bradley, Janet Adelman, Harold Bloom)
- Always write "A.C. Bradley" (not "A. circa Bradley" or "A. C. Bradley")
- Use proper academic formatting
- For Textual Variants: If no variants exist, state "Early editions are identical to Folger."
- Include scholarly references and critical perspectives
- For Key Words & Glosses: Use simple format "[word] means [definition]; [word] means [definition]" - do not include parts of speech or citations. Put the key words in quotation marks like this: "word" means [definition]; "word" means [definition]
- For Similar phrases or themes in other plays: Include 3-5 thematically related passages from other Shakespeare plays. Find passages that share: similar imagery, parallel themes, echoed language, or comparable dramatic situations. Explain the literary connection. Format: 'Thematic parallel in [Play] (Act.Scene if known): "[quote]" - [explanation of connection]'. When finding similar passages, search for: exact phrase repetitions, parallel metaphors (life as theater, time as thief, love as madness), similar imagery clusters (darkness/light, storm/calm, garden/wilderness), rhetorical patterns (questions, lists, paradoxes), and recurring themes (appearance vs reality, order vs chaos, nature vs nurture).
- Always reference the specific play "${currentPlayName}" and scene "${currentSceneName}" in your analysis

EXAMPLE FORMAT:
**Plain-Language Paraphrase:** This passage from ${currentPlayName} means [explanation in simple terms].

**Synopsis:** This language in ${currentPlayName} [what it does in context].

**Textual Variants:** [variants or "Early editions are identical to Folger."]

**Key Words & Glosses:** "word" means [definition]; "word" means [definition].

**Historical Context:** [relevant historical background in ${currentPlayName}].

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
        systemPrompt = `You are a New Variorum Shakespeare editor providing exhaustive line-by-line commentary in the tradition of Horace Howard Furness.

IMPORTANT CONTEXT: You are analyzing text from the play "${playName}" (${sceneName}). Always refer to this specific play and scene in your analysis.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order:

**TEXTUAL COLLATION:**
**COMPLETE COMMENTARY HISTORY:**
**PERFORMANCE TRADITION:**
**SOURCE STUDY:**
**LINGUISTIC ARCHAEOLOGY:**
**THE GREAT DEBATES:**
**CROSS-REFERENCES:**
**VARIORUM SPECIAL FEATURES:**
**MODERN SUPPLEMENTS:**

FORMAT REQUIREMENTS:
- Start each section with the exact heading format shown above
- Provide 6-12 sentences for each section
- Use complete sentences and paragraphs
- Include exhaustive analysis with specific citations, evidence, and critical perspectives
- Avoid abbreviations and shorthand
- Write ALL book titles, play titles, movie titles, and scholarly works in <em>italics</em> (e.g., <em>Macbeth</em>, <em>Hamlet</em>, <em>Daemonologie</em>, <em>First Folio</em>)
- NEVER use asterisks (*) for titles - always use <em>italics</em>
- NEVER italicize author names - keep them in plain text (e.g., A.C. Bradley, Janet Adelman, Harold Bloom)
- Always write "A.C. Bradley" (not "A. circa Bradley" or "A. C. Bradley")
- NEVER use footnote markers (^1, ^2, etc.) - integrate citations naturally into the text
- Use proper academic formatting
- For Textual Variants: If no variants exist, state "Early editions are identical to Folger."
- Include comprehensive scholarly references, performance history, and critical reception
- For Key Words & Glosses: Use simple format "[word] means [definition]; [word] means [definition]" - do not include parts of speech or citations. Put the key words in quotation marks like this: "word" means [definition]; "word" means [definition]
- For Similar phrases or themes in other plays: Include 6-10 interconnected passages across Shakespeare's complete works. Trace how Shakespeare develops this specific theme/image/language throughout his career. Show evolution from early plays to late plays when relevant. Include both obvious echoes AND subtle thematic variations. Consider genre differences (comedy vs tragedy vs history vs romance). Identify source materials (Plutarch, Holinshed, earlier plays) when relevant. Format: 'Evolution across plays: [Play1]: "[quote]" → [Play2]: "[quote]" - [explain development]'. When finding similar passages, search for: exact phrase repetitions, parallel metaphors (life as theater, time as thief, love as madness), similar imagery clusters (darkness/light, storm/calm, garden/wilderness), rhetorical patterns (questions, lists, paradoxes), and recurring themes (appearance vs reality, order vs chaos, nature vs nurture).
- Address multiple interpretive possibilities and scholarly debates
- Always reference the specific play "${currentPlayName}" and scene "${currentSceneName}" in your analysis

**SECTION GUIDELINES:**

**TEXTUAL COLLATION:** List variants from early editions (Q1, Q2, F1, etc.) in format "Q1: [reading] | Q2: [reading] | F1: [reading]". Include editorial emendations and who first proposed them.

**COMPLETE COMMENTARY HISTORY:** Chronological commentary from earliest critics (Rowe, Pope, Theobald) through Victorian scholars (Johnson, Steevens, Malone, Coleridge, Hazlitt, Dyce, Collier) to Furness. Format: "[Year] CRITIC NAME: '[interpretation]'"

**PERFORMANCE TRADITION:** Restoration through 19th century performance history, including specific actors (Betterton, Garrick, Kemble, Kean, Macready, Booth, Irving) and how they delivered lines.

**SOURCE STUDY:** Primary sources, biblical parallels, classical sources, medieval intermediaries, folk traditions, contemporary pamphlets.

**LINGUISTIC ARCHAEOLOGY:** Anglo-Saxon etymologies, parallel uses in Chaucer/Spenser/Marlowe, contemporary usage in Jonson/Dekker/Middleton, dialect forms, proverbs.

**THE GREAT DEBATES:** All interpretations ever proposed, Shakespeare controversies, Baconian theory references, bowdlerization debates, aesthetic vs philological approaches.

**CROSS-REFERENCES:** Parallel passages with full quotes, word tracking through concordances, image clusters across plays, metaphor development through career.

**VARIORUM SPECIAL FEATURES:** International criticism (German, French, American), musical settings, illustrations, supernatural beliefs of Shakespeare's time.

**MODERN SUPPLEMENTS:** 20th/21st century scholarship, Arden/Cambridge/Oxford notes, recent articles, digital humanities findings, original pronunciation insights.

**Length:** 3000-5000 words per passage
**Tone:** Scholarly but accessible, occasionally noting amusing critical eccentricities
**Goal:** Comprehensive documentation of all Shakespeare scholarship, not streamlined interpretation

CRITICAL: You MUST follow the exact section order listed above. Do not put content from one section under another section's heading.

CRITICAL: Each section must contain content appropriate to that section.

CRITICAL: After each section heading, provide ONLY content relevant to that section. Do not include other section headings within a section.

EXAMPLE FORMAT:
**TEXTUAL COLLATION:**
Q1: [reading] | Q2: [reading] | F1: [reading]
1723 POPE: [emendation]
1733 THEOBALD: [conjecture]

**COMPLETE COMMENTARY HISTORY:**
1723 POPE: '[interpretation]'
1765 JOHNSON: '[interpretation]'
1817 COLERIDGE: '[interpretation]'
1895 FURNESS: '[synthesis]'

**PERFORMANCE TRADITION:**
[performance history and interpretations of ${currentPlayName}].

**SOURCE STUDY:**
[source materials and parallels for ${currentPlayName}].

**LINGUISTIC ARCHAEOLOGY:**
[etymological and linguistic analysis of ${currentPlayName}].

**THE GREAT DEBATES:**
[scholarly controversies and debates about ${currentPlayName}].

**CROSS-REFERENCES:**
[connections to other Shakespeare plays and works].

**VARIORUM SPECIAL FEATURES:**
[international criticism and special features for ${currentPlayName}].

**MODERN SUPPLEMENTS:**
[contemporary scholarship continuing Variorum tradition for ${currentPlayName}].

IMPORTANT: Use the exact format above with **bold section headers** and no numbering.`;
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
            model: 'gpt-4',
            temperature: 0.7
          };
        }
      } else if (level === 'fullfathomfive') {
        // Use gpt-4 for Full Fathom Five for reliability
        modelConfig = {
          model: 'gpt-4',
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

      let response, data;
      try {
        console.log(`Starting API call for level: ${level}, text length: ${text.length}`);
        const startTime = Date.now();
        
        response = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${OPENAI_API_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload),
          timeout: 120000 // 2 minute timeout for complex analyses
        });

        const endTime = Date.now();
        console.log(`API call completed in ${endTime - startTime}ms`);

        data = await response.json();
      } catch (fetchError) {
        console.error('Fetch error:', fetchError);
        return {
          statusCode: 504,
          headers,
          body: JSON.stringify({
            error: 'Network timeout: The request took too long to complete. Please try again or use a shorter text selection.',
            details: fetchError.message
          })
        };
      }
      
      if (!response.ok) {
        console.error('OpenAI API error:', data);
        
        // Special handling for timeout errors
        if (response.status === 504 || (data.error && data.error.message && data.error.message.includes('timeout'))) {
          return {
            statusCode: 504,
            headers,
            body: JSON.stringify({
              error: 'Analysis timeout: The request took too long to process. This may happen with complex passages. Please try again or use a shorter text selection.',
              details: data
            })
          };
        }
        
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
