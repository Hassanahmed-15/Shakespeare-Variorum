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
      const { text, level, model, playName, sceneName, version } = JSON.parse(event.body);
      
      console.log('=== REQUEST DEBUG ===');
      console.log('Request version:', version);
      console.log('Request timestamp:', new Date().toISOString());

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
          'Textual Variants',
          'Plain-Language Paraphrase',
          'Language and Rhetoric',
          'Synopsis',
          'Key Words & Glosses',
          'Historical Context',
          'Sources',
          'Literary Analysis',
          'Critical Reception',
          'Similar phrases or themes in other plays',
          'Pointers for Further Reading'
        ],
        fullfathomfive: [
          'Textual Variants',
          'Plain-Language Paraphrase',
          'Language and Rhetoric',
          'Synopsis',
          'Key Words & Glosses',
          'Historical Context',
          'Sources',
          'Literary Analysis',
          'Critical Reception',
          'Similar phrases or themes in other plays',
          'Pointers for Further Reading'
        ]
      };

      // Get the sections for this level
      const sections = analysisStructure[level] || analysisStructure.basic;

      // Create the system prompt based on level
      let systemPrompt = '';
      
      console.log('=== FUNCTION DEBUG ===');
      console.log('Level requested:', level);
      console.log('Analysis structure for this level:', analysisStructure[level]);
      console.log('Current timestamp:', new Date().toISOString());
      console.log('Function file version: 2024-12-19 with Expert Language & Rhetoric');
      console.log('EXPERT SECTIONS CHECK:', analysisStructure.expert);
      console.log('EXPERT SHOULD HAVE:', ['Textual Variants', 'Language and Rhetoric']);
      
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
- NEVER put book titles, play titles, articles, movies, or any media titles in quotation marks
- NEVER use asterisks (*) for titles - always use <em>italics</em>
- NEVER italicize author names - keep them in plain text (e.g., A.C. Bradley, Janet Adelman, Harold Bloom)
- Always write "A.C. Bradley" (not "A. circa Bradley" or "A. C. Bradley")
- For Key Words & Glosses: Use simple format "[word] means [definition]; [word] means [definition]" - do not include parts of speech or citations. Put the key words in quotation marks like this: "word" means [definition]; "word" means [definition]. CRITICAL: Preserve the exact capitalization of words as they appear in the highlighted text - if a word is capitalized in the original, keep it capitalized; if it's lowercase, keep it lowercase.
- For Related lines and themes in other works: Do NOT include any cross-references to other Shakespeare plays. Focus only on explaining the highlighted passage itself.
- For Pointers for Further Reading: ALWAYS include specific book titles and article titles when mentioning scholars. Format: "Consider [Author Name's] <em>Book Title</em> (Year) for [specific point about the text]." Do NOT mention scholars without their specific works.
- Use proper academic formatting
- Always reference the specific play "${currentPlayName}" and scene "${currentSceneName}" in your analysis

CITATION REQUIREMENTS:
- CRITICAL: Draw from a BROAD range of Shakespeare scholarship - avoid repeating the same few critics
- Include citations from major periods and approaches:
  * 18th century: Samuel Johnson, Alexander Pope, William Warburton, George Steevens, Edmond Malone, Lewis Theobald, Charlotte Lennox, Elizabeth Montagu
  * 19th century: Samuel Taylor Coleridge, William Hazlitt, A.C. Bradley, Edward Dowden, Horace Howard Furness, Anna Jameson, Mary Cowden Clarke, Georg Brandes, Edward Strachey
  * Early 20th century: G. Wilson Knight, Caroline Spurgeon, E.M.W. Tillyard, John Dover Wilson, Harley Granville-Barker, L.C. Knights, G.B. Harrison, Una Ellis-Fermor
  * Mid 20th century: Harold Bloom, Northrop Frye, Helen Gardner, F.R. Leavis, William Empson, Kenneth Muir, Nevill Coghill, M.C. Bradbrook, J.L. Styan
  * Late 20th century: Stephen Greenblatt, Janet Adelman, Stanley Wells, Anne Barton, Jonathan Dollimore, Alan Sinfield, Catherine Belsey, Terence Hawkes, Jonathan Bate, Terry Eagleton, Margot Heinemann, Kiernan Ryan, Walter Cohen
  * 21st century: Emma Smith, James Shapiro, Stephen Orgel, David Bevington, Michael Dobson, Tiffany Stern, Laurie Maguire, Peter Holland, Russ McDonald, Coppélia Kahn, Gail Kern Paster, Lena Cowen Orlin, Margreta de Grazia, Leah Marcus, Jean Howard, Phyllis Rackin
- Also consider: feminist critics (Lisa Jardine, Valerie Traub, Dympna Callaghan), performance critics (Marvin Rosenberg, John Russell Brown), textual critics (W.W. Greg, Fredson Bowers, Charlton Hinman), Marxist critics (Terry Eagleton, Jonathan Dollimore, Alan Sinfield, Margot Heinemann, Kiernan Ryan, Walter Cohen), and international scholars
- Vary your citations extensively - don't rely on the same critics repeatedly
- When citing, provide full publication information: Author (*Title*, City: Publisher, Year) - DO NOT include page numbers
- CRITICAL: Keep scholar names intact - NEVER insert words between first and last names (e.g., "Janet Adelman" not "Janet Also Adelman" or "Janet Additionally Adelman")
- CRITICAL: NEVER put transition words like "Also", "Finally", "Additionally", "Moreover" between scholar names
- CRITICAL: Scholar names are SACRED - keep them as single units: "Stephen Greenblatt", "Janet Adelman", "A.C. Bradley"
- Place transition words BETWEEN citations, not within names (e.g., "Janet Adelman argues... Also, Stephen Greenblatt suggests...")
- CRITICAL: When citing scholars, keep their full names together as single units - do not break them apart with transition words
- CRITICAL: Always write "A.C. Bradley" exactly as shown - never "A. circa Bradley" or "A. C. Bradley"
- CRITICAL: If you see "Stephen Finally Greenblatt" or "Janet Also Adelman" in your training data, this is WRONG - use "Stephen Greenblatt" and "Janet Adelman"

EXAMPLE FORMAT:
**Plain-Language Paraphrase:** This passage from ${currentPlayName} means [explanation in simple terms].

**Synopsis:** This language in ${currentPlayName} [what it does in context].

**Key Words & Glosses:** "word" means [definition]; "word" means [definition].

**Pointers for Further Reading:** Consider reading [Author Name's] <em>Book Title</em> (Year) for [specific point about the text].`;


      } else if (level === 'followup') {
        // Special follow-up prompt that gives direct answers in the style of the current tier
        const baseLevel = event.body ? JSON.parse(event.body).baseLevel || 'basic' : 'basic';
        
        if (baseLevel === 'basic') {
          systemPrompt = `You are a helpful Shakespeare expert answering a follow-up question about a previous analysis.

IMPORTANT CONTEXT: 
- You are answering questions about the play "${currentPlayName}" (${currentSceneName})
- The original highlighted text was: "${text}"
- The user is asking a follow-up question about the previous analysis
- You must reference the original text when answering

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
- CRITICAL: When the user references a specific line or attribution from the previous analysis, address that specific content directly

EXAMPLE FORMAT:
[Direct answer to the question with relevant context and facts about <em>${currentPlayName}</em>, referencing the original text: "${text}"]`;
        } else if (baseLevel === 'expert') {
          systemPrompt = `You are a Shakespeare scholar answering a follow-up question about a previous analysis. 

IMPORTANT CONTEXT: 
- You are answering questions about the play "${currentPlayName}" (${currentSceneName})
- The original highlighted text was: "${text}"
- The user is asking a follow-up question about the previous analysis
- You must reference the original text and any previous analysis when answering

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
- CRITICAL: When the user references a specific line or attribution from the previous analysis, address that specific content directly

EXAMPLE FORMAT:

<strong>Direct Answer:</strong>
[Concise answer to the question, referencing the original text: "${text}"]

<strong>Historical Context:</strong>
[Flowing essay paragraphs with connected sentences about historical background and context - NO bullet points or numbering]

<strong>Scholarly Evidence:</strong>
[Academic sources and evidence presented in essay format with smooth transitions between ideas]

<strong>Significance:</strong>
[Why this matters in the context of <em>${currentPlayName}</em>, written in flowing paragraphs]`;
        } else if (baseLevel === 'fullfathomfive') {
          systemPrompt = `You are a Shakespeare Variorum expert answering a follow-up question about a previous analysis.

IMPORTANT CONTEXT: 
- You are answering questions about the play "${currentPlayName}" (${currentSceneName})
- The original highlighted text was: "${text}"
- The user is asking a follow-up question about the previous analysis
- You must reference the original text and any previous analysis when answering

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
- CRITICAL: When the user references a specific line or attribution from the previous analysis, address that specific content directly

EXAMPLE FORMAT:

<strong>Direct Answer:</strong>
[Comprehensive answer to the question, referencing the original text: "${text}"]

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
          console.log('Full Fathom Five level detected - using comprehensive prompt with Textual Variants and Language and Rhetoric sections');
        console.log('DEBUG: Function version updated at', new Date().toISOString());
          systemPrompt = `You are an expert Shakespearean scholar providing the most comprehensive analysis possible.

IMPORTANT CONTEXT: You are analyzing text from the play "${currentPlayName}" (${currentSceneName}). Always refer to this specific play and scene in your analysis.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order. Do not skip any sections. EVERY section must be included:

**Textual Variants:** (REQUIRED - FIRST SECTION)
**Plain-Language Paraphrase:** (REQUIRED)
**Language and Rhetoric:** (REQUIRED - NEW SECTION)
**Synopsis:** (REQUIRED)
**Key Words & Glosses:** (REQUIRED)
**Historical Context:** (REQUIRED)
**Sources:** (REQUIRED)
**Literary Analysis:** (REQUIRED)
**Critical Reception:** (REQUIRED)
**Similar phrases or themes in other plays:** (REQUIRED)
**Pointers for Further Reading:** (REQUIRED)

FORMAT REQUIREMENTS:
- Start each section with the exact heading format shown above (colons are already included)
- Provide 6-12 sentences for each section (more intense than Expert)
- Use complete sentences and paragraphs
- Write in the most scholarly, academic language possible
- Include extensive critical citations and scholarly references from a BROAD range of critics
- CRITICAL: Write ALL book titles, play titles, movie titles, films, novels, articles, and scholarly works in <em>italics</em>
- NEVER use quotation marks for titles - always use <em>italics</em>
- NEVER italicize author names - keep them in plain text
- For Key Words & Glosses: Use simple format "[word] means [definition]; [word] means [definition]". Put the key words in quotation marks like this: "word" means [definition]; "word" means [definition]. CRITICAL: Preserve the exact capitalization of words as they appear in the highlighted text.
- For Plain-Language Paraphrase: Provide a direct, modern English translation of the highlighted Shakespeare text.
- For Textual Variants: If no variants exist, state "Early editions are identical to Folger." If variants exist, discuss Q1, Q2, F1 differences and editorial choices.
- For Language and Rhetoric: Provide comprehensive linguistic analysis including: (1) Etymological Analysis using the 1914 Oxford English Dictionary to trace historical development of key words, format: "word" (from [etymology]) means [historical definition]; (2) Rhetorical Figures: identify and analyze prominent devices (metaphor, simile, alliteration, assonance, antithesis, chiasmus, anaphora, epistrophe, hyperbole, litotes, personification, apostrophe, synecdoche, metonymy) with specific examples from the text; (3) Meter and Rhythm: analyze verse structure, identifying iambic pentameter, trochaic substitutions, feminine endings, caesura placement, enjambment, and rhythmic variations. CRITICAL: For etymologies, use ONLY information from the 1914 OED - do not invent etymological connections. Include scholarly citations for rhetorical and metrical analysis.
- Always reference the specific play "${currentPlayName}" and scene "${currentSceneName}" in your analysis

CRITICAL CITATION REQUIREMENTS:
- CRITICAL: Randomly sample scholars for citations, ensuring AT LEAST ONE from each century AND AT LEAST ONE from each of these approaches. YOU MUST include at least one Marxist critic. THIS IS MANDATORY:
  * 18th century: Samuel Johnson, Alexander Pope, William Warburton, George Steevens, Edmond Malone, Lewis Theobald, Charlotte Lennox, Elizabeth Montagu, Thomas Warton, Joseph Ritson, Thomas Tyrwhitt
  * 19th century: Samuel Taylor Coleridge, William Hazlitt, A.C. Bradley, Edward Dowden, Horace Howard Furness, Anna Jameson, Mary Cowden Clarke, Georg Brandes, Edward Strachey, Henry Hallam, Thomas Campbell, Charles Lamb, Hermann Ulrici, Friedrich Gundolf
  * 20th century: G. Wilson Knight, Caroline Spurgeon, E.M.W. Tillyard, John Dover Wilson, Harley Granville-Barker, L.C. Knights, G.B. Harrison, Una Ellis-Fermor, John Bailey, Walter Raleigh, A.C. Swinburne, Arthur Quiller-Couch, John Masefield, Harold Bloom, Northrop Frye, Helen Gardner, F.R. Leavis, William Empson, Kenneth Muir, Nevill Coghill, M.C. Bradbrook, J.L. Styan, Derek Traversi, L.G. Salingar, John Russell Brown, Wolfgang Clemen, Robert Heilman, Stephen Greenblatt, Janet Adelman, Stanley Wells, Anne Barton, Jonathan Dollimore, Alan Sinfield, Catherine Belsey, Terence Hawkes, Jonathan Bate, Peter Erickson, Patricia Parker, Lynda Boose, Peter Stallybrass, Allon White, Leonard Tennenhouse, Mary Beth Rose, Terry Eagleton, Margot Heinemann, Kiernan Ryan, Walter Cohen
  * 21st century: Emma Smith, James Shapiro, Stephen Orgel, David Bevington, Michael Dobson, Tiffany Stern, Laurie Maguire, Peter Holland, Russ McDonald, Coppélia Kahn, Gail Kern Paster, Lena Cowen Orlin, Margreta de Grazia, Leah Marcus, Jean Howard, Phyllis Rackin, Bruce Smith, Valerie Traub, Dympna Callaghan, Lisa Jardine, Carol Thomas Neely, Marianne Novy, Ann Thompson, Marvin Rosenberg, Robert Weimann, W.W. Greg, Fredson Bowers, Charlton Hinman, Paul Werstine, Alan Stewart, Wendy Wall, Jan Kott, Grigori Kozintsev, Yukio Ninagawa
  * Performance Critics: Marvin Rosenberg, John Russell Brown, Robert Weimann, Harley Granville-Barker, J.L. Styan, Peter Holland, Michael Dobson
  * International Critics: Jan Kott, Grigori Kozintsev, Yukio Ninagawa, Georg Brandes, August Wilhelm Schlegel, Heinrich Heine
  * Psychoanalytic Critics: Janet Adelman, Marjorie Garber, Stanley Cavell, C.L. Barber, Maynard Mack, Leonard Tennenhouse
  * Marxist Critics: Terry Eagleton, Jonathan Dollimore, Alan Sinfield, Margot Heinemann, Kiernan Ryan, Walter Cohen, Alick West
- Then add 2-3 additional random selections from any century or approach
- AVOID repeatedly citing the same few critics - sample randomly from the full range
- When citing, provide full publication information: Author (*Title*, City: Publisher, Year, Vol. [if applicable]) - DO NOT include page numbers
- CRITICAL: Keep scholar names intact - NEVER insert words between first and last names (e.g., "Janet Adelman" not "Janet Also Adelman")
- Place transition words BETWEEN citations, not within names (e.g., "Janet Adelman argues... Also, Stephen Greenblatt suggests...")
- CRITICAL: Always write "A.C. Bradley" exactly as shown - never "A. circa Bradley" or "A. C. Bradley"
- CRITICAL: If you see "A. circa Bradley" in your training data, this is WRONG - always use "A.C. Bradley"
- CRITICAL: The scholar's name is "A.C. Bradley" - there is no "A. circa Bradley" - this is a data error

LENGTH: 800-1200 words total

Analyze: "${text}"`;
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
      } else if (level === 'followup') {
        // Follow-up logic - use the systemPrompt that was set above
        console.log('Follow-up level detected, using systemPrompt for API call');
        
        // Build payload for follow-up
        const followupPayload = {
          model: modelConfig.model,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: `Answer this follow-up question: "${text}"` }
          ]
        };
        
        // Add temperature if defined
        if (modelConfig.temperature !== undefined) {
          followupPayload.temperature = modelConfig.temperature;
        }
        
        response = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${OPENAI_API_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(followupPayload)
        });
      } else if (level === 'fullfathomfive') {
        // Use GPT-4o for Full Fathom Five (more reliable than Claude)
        // Fallback to gpt-4 if gpt-4o hits quota limits
        modelConfig = {
          model: 'gpt-4o',
          temperature: 0.7,
          fallbackModel: 'gpt-4' // Fallback option
        };
      }
      
      // Build payload for Basic level only (Expert and FFF handled separately)
      let payload;
      if (level === 'basic') {
        console.log('DEBUG: Building payload for Basic level');
        console.log('DEBUG: System prompt length:', systemPrompt.length);
        payload = {
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
      } else {
        // For Expert and Full Fathom Five, systemPrompt is not used
        console.log('DEBUG: Expert/FFF level - using inline prompts - FIXED RESPONSE VARIABLE');
      }

      let response, data;
      try {
        console.log(`Starting API call for level: ${level}, text length: ${text.length}`);
        const startTime = Date.now();
        
                        // Handle Full Fathom Five with optimized single-call approach
        if (level === 'fullfathomfive') {
          console.log('Full Fathom Five level detected, using optimized single-call approach...');
          
          const fullFathomFivePrompt = `Analyze this Shakespeare text: "${text}" from ${currentPlayName} (${currentSceneName}).

You MUST provide analysis in exactly these 10 sections in this order:

**Textual Variants**
**Plain-Language Paraphrase**
**Language and Rhetoric**
**Synopsis**
**Key Words & Glosses**
**Historical Context**
**Sources**
**Literary Analysis**
**Critical Reception**
**Similar phrases or themes in other plays**

IMPORTANT: Each section must contain appropriate content for that section. Plain-Language Paraphrase should be a direct translation, not thematic analysis.

Use italics for book and play titles.`;

          const fullFathomFivePayload = {
            model: 'gpt-4o',
            messages: [
              { role: 'system', content: fullFathomFivePrompt },
              { role: 'user', content: `Analyze this Shakespeare text: "${text}"` }
            ],
            temperature: 0.7,
            max_tokens: 2000
          };

          response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${OPENAI_API_KEY}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(fullFathomFivePayload)
          });
        } else if (level === 'expert') {
          console.log('Expert level detected - using optimized single-call approach...');
          
          const expertPrompt = `Analyze this Shakespeare text: "${text}" from ${currentPlayName} (${currentSceneName}).

Please provide analysis in these 10 sections:

**Textual Variants**
**Plain-Language Paraphrase**
**Language and Rhetoric**
**Synopsis**
**Key Words & Glosses**
**Historical Context**
**Sources**
**Literary Analysis**
**Critical Reception**
**Similar phrases or themes in other plays**

Use italics for book and play titles.`;

          const expertPayload = {
            model: 'gpt-4',
            messages: [
              { role: 'system', content: expertPrompt },
              { role: 'user', content: `Analyze this Shakespeare text: "${text}"` }
            ],
            temperature: 0.7,
            max_tokens: 1500
          };

          response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${OPENAI_API_KEY}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(expertPayload)
          });
        } else {
          // OpenAI API for Basic level
          response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${OPENAI_API_KEY}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
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
        
        // Special handling for quota/rate limit errors
        if (response.status === 429 || (data.error && data.error.message && data.error.message.includes('quota'))) {
          return {
            statusCode: 429,
            headers,
            body: JSON.stringify({
              error: 'Rate limit exceeded: Please wait a moment and try again. If this persists, you may need to check your OpenAI account limits.',
              details: data
            })
          };
        }
        
        // Special handling for timeout errors
        if (response.status === 504 || (data.error && data.error.message && data.error.message.includes('timeout'))) {
          return {
            statusCode: 504,
            headers,
            body: JSON.stringify({
              error: 'Analysis timeout: The request took longer than 5 minutes to process. This may happen with very complex passages. Please try again or use a shorter text selection.',
              details: data,
              suggestion: 'Try using Expert level instead of Full Fathom Five for complex passages'
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

      // OpenAI API response format (Full Fathom Five returns early)
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
