const { OpenAI } = require('openai')

// Add fetch polyfill for Node.js environments that don't have it
if (!global.fetch) {
  global.fetch = require('node-fetch')
}

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

// Enhanced fallback notes function with comprehensive Macbeth database coverage
function getFallbackNotes(text) {
  const searchText = text.toLowerCase().trim()
  
  // Extract line number from the highlighted text
  const lineMatch = searchText.match(/^(\d+)\.?\s*(.*)/)
  let targetLineNumber = null
  let searchContent = searchText
  
  if (lineMatch) {
    targetLineNumber = lineMatch[1]
    searchContent = lineMatch[2].trim()
  } else {
    // Try to find line number anywhere in the text
    const numberMatch = searchText.match(/(\d+)/)
    if (numberMatch) {
      targetLineNumber = numberMatch[1]
    }
  }
  
  console.log('Looking for fallback notes for line number:', targetLineNumber, 'content:', searchContent)
  
  // Basic fallback for when JSON file is not available
  const fallbackNotes = {
    "first witch: when shall we three meet again": {
      scene: "ACT 1, SCENE 1",
      line: "1",
      play: "First Witch: When shall we three meet again",
      notes: ["Enter three Witches] This is the opening line of Macbeth, establishing the supernatural theme."]
    }
  }
  
  // Check for exact match first
  if (fallbackNotes[searchText]) {
    console.log('✅ Found exact fallback note for:', searchText)
    return [fallbackNotes[searchText]]
  }
  
  console.log('❌ No fallback notes found for:', searchText)
  return []
}

// Function to find relevant notes from play database
function normalizePlayKey(playNameRaw) {
  if (!playNameRaw) return 'macbeth'
  const s = String(playNameRaw).toLowerCase()
  if (s.includes('hamlet')) return 'hamlet'
  if (s.includes('romeo') || s.includes('juliet')) return 'romeo'
  if (s.includes('othello')) return 'othello'
  if (s.includes('lear')) return 'kinglear'
  if (s.includes('henry') && (s.includes('iv') || s.includes('4')) && s.includes('1')) return 'henryiv1'
  if (s.includes('midsummer')) return 'midsummer'
  if (s.includes('as you like it') || s.includes('asyoulikeit')) return 'asyoulikeit'
  if (s.includes('julius') && s.includes('caesar')) return 'juliuscaesar'
  if (s.includes('king') && s.includes('john')) return 'kingjohn'
  if (s.includes('love') && s.includes('labour') && s.includes('lost')) return 'loveslabourslost'
  if (s.includes('much') && s.includes('ado')) return 'muchado'
  if (s.includes('richard') && (s.includes('iii') || s.includes('3'))) return 'richardiii'
  if (s.includes('merchant') && s.includes('venice')) return 'merchantofvenice'
  if (s.includes('tempest')) return 'tempest'
  if (s.includes('winter') && s.includes('tale')) return 'winterstale'
  if (s.includes('twelfth') && s.includes('night')) return 'twelfthnight'
  if (s.includes('macbeth')) return 'macbeth'
  return 'macbeth'
}

async function findRelevantNotes(text, scene = null, playName = 'macbeth') {
  try {
    console.log(`Loading ${playName} notes from URL (serverless environment)`)
    console.log('Input text:', text)
    
    let notesData = null;
    // Netlify sets URL to the site’s primary URL (custom domain when configured).
    const baseUrl =
      process.env.URL ||
      process.env.DEPLOY_PRIME_URL ||
      'https://www.newvariorum.com';
    const timestamp = Date.now();
    
    // Map play names to their JSON files
    const playFiles = {
      'macbeth': 'macbeth_notes_cleaned_play.json',
      'hamlet': 'hamlet_notes (1).json',
      'romeo': 'ROMEO_notes.json',
      'othello': 'othello_notes_folger.json',
      'kinglear': 'kinglear_notes.json',
      'henryiv1': 'henry_iv_part1.json',
      'midsummer': 'midsummer_nights_dream.json',
      'asyoulikeit': 'as_you_like_it.json',
      'juliuscaesar': 'julius_caesar_clean_(3).json',
      'kingjohn': 'king_john.json',
      'loveslabourslost': 'loves_labours_lost.json',
      'muchado': 'much_ado_about_nothing.json',
      'richardiii': 'richard_iii.json',
      'merchantofvenice': 'merchant_of_venice.json',
      'tempest': 'the_tempest.json',
      'winterstale': 'the_winters_tale.json',
      'twelfthnight': 'twelfth_night.json'
    };
    
    const normalizedKey = normalizePlayKey(playName)
    const fileName = playFiles[normalizedKey] || playFiles['macbeth'];
    // Ensure filenames with spaces/parentheses are URL-encoded
    const encodedFileName = encodeURIComponent(fileName)
    const possibleUrls = [
      `${baseUrl}/Public/Data/${encodedFileName}?v=${timestamp}`,
      `${baseUrl}/${encodedFileName}?v=${timestamp}`,
      `https://raw.githubusercontent.com/bradrcarson/Shakespeare-Variorum/main/Public/Data/${encodedFileName}`,
      `https://raw.githubusercontent.com/bradrcarson/Shakespeare-Variorum/main/${encodedFileName}`
    ];
    
    for (const url of possibleUrls) {
      try {
        console.log(`Trying to load from: ${url}`);
        const response = await fetch(url, { 
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
          }
        });
        
        if (response.ok) {
          const fileContent = await response.text();
          console.log(`✅ SUCCESS: Loaded from ${url}`);
          console.log(`Response size: ${fileContent.length} characters`);
          
          notesData = JSON.parse(fileContent);
          console.log(`✅ Successfully loaded ${playName} notes from: ${url}`);
          console.log(`📊 Database contains ${Object.keys(notesData).length} scenes`);
          
          // Check if this is the updated version by looking for a specific line
          const firstScene = Object.keys(notesData)[0];
          if (firstScene && notesData[firstScene]) {
            const firstLine = Object.keys(notesData[firstScene])[0];
            if (firstLine && notesData[firstScene][firstLine]) {
              console.log(`🔍 First line content: "${notesData[firstScene][firstLine].play}"`);
            }
          }
          
          // Log first few scene names for verification
          const sceneNames = Object.keys(notesData).slice(0, 3);
          console.log(`📋 First scenes: ${sceneNames.join(', ')}`);
          break;
        } else {
          console.log(`❌ HTTP ${response.status} from ${url}`);
        }
      } catch (error) {
        console.log(`❌ Failed to load from ${url}: ${error.message}`);
      }
    }
    
    if (!notesData) {
      console.error(`❌ Could not load ${fileName} from any URL`);
      return getFallbackNotes(text);
    }
    
    console.log(`✅ Successfully loaded ${playName} database with`, Object.keys(notesData).length, 'scenes')
    return processNotesWithData(notesData, text)
    
  } catch (error) {
    console.error(`Error loading ${playName} notes:`, error)
    console.error('Error stack:', error.stack)
    console.log('Using fallback notes for:', text)
    return getFallbackNotes(text)
  }
}

// Helper function to process notes data
function processNotesWithData(notesData, text) {
  const lines = text.split('\n').filter(line => line.trim().length > 0)
  const foundNotes = []
  
  console.log('Processing text with comprehensive Macbeth database:', Object.keys(notesData).length, 'scenes available')
  
  // Extract line numbers from the highlighted text first
  const highlightedLineNumbers = []
  for (const line of lines) {
    // Try to extract line number from the text
    const lineMatch = line.match(/^(\d+)\.?\s*(.*)/)
    if (lineMatch) {
      highlightedLineNumbers.push({
        number: lineMatch[1],
        text: lineMatch[2].trim()
      })
    } else {
      // If no line number found, try to find it in the text
      const numberMatch = line.match(/(\d+)/)
      if (numberMatch) {
        highlightedLineNumbers.push({
          number: numberMatch[1],
          text: line.trim()
        })
      }
    }
  }
  
  console.log('Highlighted line numbers:', highlightedLineNumbers)
  
  // Track which line numbers we've already processed
  const processedLineNumbers = new Set()
  
  // Process each highlighted line number to ensure 100% coverage
  for (const highlightedLine of highlightedLineNumbers) {
    const targetLineNumber = highlightedLine.number
    
    // Skip if we've already processed this line number
    if (processedLineNumbers.has(targetLineNumber)) {
      console.log(`Already processed line ${targetLineNumber}, skipping`)
      continue
    }
    
    let lineFound = false
    
    // Search through ALL scenes for this specific line number
    for (const [sceneName, sceneData] of Object.entries(notesData)) {
      if (sceneData[targetLineNumber] && sceneData[targetLineNumber].play) {
        const lineData = sceneData[targetLineNumber]
        lineFound = true
        
        // Always include the line data, regardless of text match
        const notes = lineData.notes || []
        
        // If no notes available, add a placeholder
        if (notes.length === 0) {
          notes.push("No commentary available for this line.")
        }
        
        foundNotes.push({
          line: targetLineNumber,
          play: lineData.play,
          scene: sceneName,
          notes: notes,
          hasNotes: notes.length > 0 && notes[0] !== "No commentary available for this line."
        })
        
        console.log(`✅ Line ${targetLineNumber} from ${sceneName}: ${notes.length} note entries`)
        processedLineNumbers.add(targetLineNumber)
        break // Found the line, move to next highlighted line
      }
    }
    
    // If line number not found in any scene, add a placeholder
    if (!lineFound) {
      console.log(`⚠️  Line ${targetLineNumber} not found in any scene, adding placeholder`)
      foundNotes.push({
        line: targetLineNumber,
        play: `Line ${targetLineNumber} (text not found)`,
        scene: "Unknown Scene",
        notes: ["Line not found in database. Please check the line number."],
        hasNotes: false
      })
      processedLineNumbers.add(targetLineNumber)
    }
  }
  
  if (foundNotes.length > 0) {
    console.log(`✅ Returning ${foundNotes.length} notes with 100% line coverage`)
    foundNotes.forEach((note, index) => {
      const status = note.hasNotes ? "✅" : "⚠️"
      console.log(`${status} Note ${index + 1}: Line ${note.line} from ${note.scene} - ${note.notes.length} entries`)
    })
    return foundNotes
  }
  
  // If no line numbers found, try broader text search across all scenes
  console.log('No line numbers found, trying broader text search...')
  const broaderMatches = searchAllScenesForText(notesData, text)
  if (broaderMatches.length > 0) {
    console.log(`Found ${broaderMatches.length} broader text matches`)
    return broaderMatches
  }
  
  console.log('No matches found in database, using fallback')
  return getFallbackNotes(text)
}

// Search all scenes for text content when line numbers don't match
function searchAllScenesForText(notesData, searchText) {
  const searchLower = searchText.toLowerCase().trim()
  const results = []
  
  console.log(`Searching all scenes for text: "${searchLower}"`)
  
  // Search through all scenes and lines for text content
  for (const [sceneName, sceneData] of Object.entries(notesData)) {
    for (const [lineNumber, lineData] of Object.entries(sceneData)) {
      if (lineData.play && typeof lineData.play === 'string') {
        const playLine = lineData.play.toLowerCase().trim()
        
        // Check if the search text appears in this line
        if (playLine.includes(searchLower) || searchLower.includes(playLine)) {
          // Ensure notes are always available
          const notes = lineData.notes || []
          if (notes.length === 0) {
            notes.push("No commentary available for this line.")
          }
          
          results.push({
            line: lineNumber,
            play: lineData.play,
            scene: sceneName,
            notes: notes,
            matchType: 'text_search',
            hasNotes: notes.length > 0 && notes[0] !== "No commentary available for this line."
          })
          
          // Limit results to avoid overwhelming
          if (results.length >= 10) {
            break
          }
        }
      }
    }
    
    if (results.length >= 10) {
      break
    }
  }
  
  console.log(`Found ${results.length} text matches across all scenes with 100% coverage`)
  return results
}

// Check if the highlighted text matches the play line
function matchesText(playLine, searchText) {
  // Exact match
  if (playLine === searchText) {
    return true;
  }
  
  // Contains match (search text is part of play line)
  if (playLine.includes(searchText) && searchText.length > 3) {
    return true;
  }
  
  // Play line is part of search text
  if (searchText.includes(playLine) && playLine.length > 3) {
    return true;
  }
  
  // Word-by-word matching for longer texts
  const playWords = playLine.split(/\s+/).filter(word => word.length > 2);
  const searchWords = searchText.split(/\s+/).filter(word => word.length > 2);
  
  if (playWords.length > 0 && searchWords.length > 0) {
    const matchingWords = playWords.filter(word => 
      searchWords.some(searchWord => 
        word.includes(searchWord) || searchWord.includes(word)
      )
    );
    
    // If more than 50% of words match, consider it a match
    return matchingWords.length >= Math.min(playWords.length, searchWords.length) * 0.5;
  }
  
  return false;
}

// Handle critics analysis requests
async function handleCriticsAnalysis(body, headers) {
  try {
    const { text } = JSON.parse(body)

    console.log('🔍 Critics analysis requested for text length:', text.length)

    // Extract critic names and their bibliographic information from the text
    const foundCritics = []
    
    // Pattern 1: Name followed by colon (e.g., "Nares:", "Johnson:")
    const colonPattern = /([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:/g
    let match
    while ((match = colonPattern.exec(text)) !== null) {
      const name = match[1].trim()
      const nameLower = name.toLowerCase()
      
      // Skip obvious non-critics
      if (!['william', 'shakespeare', 'first', 'second', 'third', 'witch', 'macbeth', 'lady', 'duncan', 'banquo'].includes(nameLower)) {
        foundCritics.push({ name, type: 'colon' })
      }
    }
    
    // Pattern 2: Citation format (e.g., "Alexander Dyce, The Works of Shakespeare, London, 1857")
    const citationPattern = /([A-Z][a-z]+\s+[A-Z][a-z]+),\s+([^—]+),\s+(?:[^,]+,\s+)?\d{4}/g
    while ((match = citationPattern.exec(text)) !== null) {
      const name = match[1].trim()
      const work = match[2].trim()
      foundCritics.push({ name, work, type: 'citation' })
    }
    
    console.log('🔍 Found critics:', foundCritics.map(c => c.name).join(', '))

    if (foundCritics.length === 0) {
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          choices: [{
            message: {
              content: '<h2>📚 New Variorum Critics & Bibliography</h2><p>No critics found in this analysis.</p>'
            }
          }],
          usage: { total_tokens: 0 }
        })
      }
    }

    // Send to OpenAI to generate structured introductions
    const criticsList = foundCritics.map(c => c.name).join(', ')
    const bibliographicInfo = foundCritics.map(c => 
      c.work ? `${c.name}: ${c.work}` : c.name
    ).join('\n')

    // Create a timeout promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Request timeout')), 90000) // 90 second timeout
    })

    const fetchPromise = fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: [
          {
            role: 'system',
            content: `You are a Shakespeare scholar. Generate a short, structured introduction for each critic mentioned in the New Variorum Analysis. 

Format each entry as:
<h3>Critic Name</h3>
<p><strong>Introduction:</strong> [2-3 sentences about who they are and their significance]</p>
<p><strong>Bibliographic Information:</strong> [exact citation from the text]</p>

Only include critics that are actually mentioned in the provided text. Be concise and scholarly.`
          },
          {
            role: 'user',
            content: `Based on this New Variorum Analysis text, generate introductions for these critics: ${criticsList}

Bibliographic information found:
${bibliographicInfo}

Original text excerpt:
${text.substring(0, 300)}`
          }
        ],
        max_tokens: 1000,
        temperature: 0.3
      })
    })

    const openaiResponse = await Promise.race([fetchPromise, timeoutPromise])

    if (!openaiResponse.ok) {
      throw new Error(`OpenAI API error: ${openaiResponse.status}`)
    }

    const openaiData = await openaiResponse.json()
    const generatedContent = openaiData.choices[0].message.content

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        choices: [{
          message: {
            content: `<h2>📚 New Variorum Critics & Bibliography</h2>\n${generatedContent}`
          }
        }],
        usage: openaiData.usage
      })
    }

  } catch (error) {
    console.error('Error in critics analysis:', error)

    // Handle timeout specifically
    if (error.message === 'Request timeout') {
      return {
        statusCode: 504,
        headers,
        body: JSON.stringify({
          error: 'Request timeout',
          details: 'The critics analysis request timed out. Please try again with a shorter text selection.'
        })
      }
    }

    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        error: 'Internal server error',
        details: error.message
      })
    }
  }
}

// Netlify function handler
exports.handler = async (event, context) => {
  // Enable CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
  }

  // Handle preflight requests
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    }
  }

  try {
    const parsedBody = JSON.parse(event.body)
    const { text, level = 'basic', model = 'gpt-4o-mini', mode, playName, sceneName, type } = parsedBody

    // ── Annotation Chatbot handler ─────────────────────────────────────────
    if (type === 'annotation_chat') {
      const { systemPrompt, messages, max_tokens = 1200, temperature = 0.4 } = parsedBody
      if (!systemPrompt || !messages) {
        return { statusCode: 400, headers, body: JSON.stringify({ error: 'systemPrompt and messages required' }) }
      }
      const chatResp = await openai.chat.completions.create({
        model: 'gpt-4o',
        messages: [{ role: 'system', content: systemPrompt }, ...messages],
        max_tokens,
        temperature
      })
      const answer = chatResp.choices?.[0]?.message?.content || ''
      return { statusCode: 200, headers, body: JSON.stringify({ answer }) }
    }
    // ── End Annotation Chatbot ─────────────────────────────────────────────

    if (!text) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Text is required' })
      }
    }

    // Determine the analysis mode
    const analysisMode = mode || level

    // Handle critics analysis mode specially
    if (analysisMode === 'critics') {
      return handleCriticsAnalysis(event.body, headers)
    }

    // Define analysis structure based on mode
    const analysisStructure = {
      basic: [
        'Plain-Language Paraphrase',
        'Synopsis',
        'Key Words & Glosses'
      ],
      expert: [
        'Plain-Language Paraphrase',
        'Synopsis',
        'Language and Imagery',
        'Literary and Thematic Analysis'
      ],
      fullfathomfive: [
        'Plain-Language Paraphrase',
        'Language and Rhetoric',
        'Synopsis',
        'Key Words & Glosses',
        'Historical Context',
        'Sources',
        'Literary Analysis',
        'Critical Reception',
        'Similar phrases or themes in other plays',
        'New Variorum Analysis'
      ]
    }

    let structure = analysisStructure[analysisMode] || analysisStructure.basic
    
    // Exclude 'New Variorum Analysis' for the 21 plays without New Variorum editions
    const playsWithoutNewVariorum = [
      'allswell', 'comedyoferrors', 'measureformeasure', 'merrywives',
      'pericles', 'taming', 'troilus', 'twogentlemen',
      'henryvi1', 'henryvi2', 'henryvi3', 'henryviii',
      'richardii', 'richardiii', 'antony', 'coriolanus',
      'henryv', 'titus', 'timon', 'henryiv2', 'midsummer'
    ];
    
    if (analysisMode === 'fullfathomfive' && playsWithoutNewVariorum.includes(playName)) {
      structure = structure.filter(section => section !== 'New Variorum Analysis')
      console.log(`🚫 ${playName} - EXCLUDING New Variorum Analysis section`)
    }

    // Check if text contains multiple lines
    const lines = text.split('\n').filter(line => line.trim().length > 0)
    const isMultipleLines = lines.length >= 2 && lines.length <= 5

    // Find relevant notes from play database (only for fullfathomfive level)
    let relevantNotes = []
    if (analysisMode === 'fullfathomfive') {
      try {
        const currentPlayName = playName || 'Macbeth'
        console.log(`Attempting to load ${currentPlayName} notes for fullfathomfive level...`)
        relevantNotes = await findRelevantNotes(text, null, currentPlayName)
        console.log(`${currentPlayName} notes loaded:`, relevantNotes.length, 'notes found')
        if (relevantNotes.length > 0) {
          console.log('Notes details:', relevantNotes.map(note => ({
            line: note.line,
            scene: note.scene,
            notesCount: note.notes.length,
            hasNotes: note.hasNotes
          })))
        }
      } catch (error) {
        console.error(`Failed to load ${currentPlayName} notes, continuing without them:`, error.message)
        console.error('Error stack:', error.stack)
        relevantNotes = [] // Continue without notes if loading fails
      }
    }
    
    // Build the system prompt based on analysis mode
    let systemPrompt = ''
    const currentPlayName = playName || 'Macbeth'
    const currentSceneName = sceneName || null
    
    // Debug: Log the scene information
    console.log('🎭 DEBUG: Received sceneName from frontend:', sceneName)
    console.log('🎭 DEBUG: Using currentSceneName:', currentSceneName)
    console.log('🎭 DEBUG: Received playName from frontend:', playName)
    console.log('🎭 DEBUG: Using currentPlayName:', currentPlayName)

    if (analysisMode === 'basic') {
      systemPrompt = `You are a university professor speaking to very smart undergraduates about Shakespeare.

IMPORTANT CONTEXT: The input text will consist of 1–3 consecutive lines selected from a Shakespearean play. Analyze only those lines; do not reference or infer text outside this snippet. Focus on the content and meaning of the selected text without mentioning specific scenes, acts, or play names.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order:

**Plain-Language Paraphrase:**
**Synopsis:** (Do NOT mention any specific scene, act, or play name. Just describe the content and context of the selected text.)
**Key Words & Glosses:**

FORMAT REQUIREMENTS:
- Use EXACTLY the section headers shown above - do not change them
- 2–4 sentences per section
- Complete sentences and paragraphs
- Clear, accessible language
- Always reference "${currentPlayName}" directly
- CRITICAL: Always italicize play titles using <em>italics</em>, never use asterisks (*) or quotes around titles
- Key Words format: "word" means [definition]; "word" means [definition] (preserve capitalization)`
    } else if (analysisMode === 'expert') {
      systemPrompt = `You are a Shakespeare scholar writing for advanced students.

IMPORTANT CONTEXT: The input text will consist of 1–3 consecutive lines selected from "${currentPlayName}". Analyze only those lines; avoid referencing material outside this range.

CRITICAL WARNING: Do NOT mention any specific scenes, acts, or play names in your analysis. Focus on the content and meaning of the selected text.

FORMAT REQUIREMENTS:
- Structure your response into these sections in this exact order:

**Plain-Language Paraphrase:**
**Synopsis:** (Do NOT mention any specific scene, act, or play name. Just describe the content and context of the selected text.)
**Language and Imagery:**
**Literary and Thematic Analysis:**

- Use essay-style paragraphs (no bullets/lists)
- Each section should be 5–8 sentences
- Clear but scholarly tone
- CRITICAL: Always italicize play titles using <em>italics</em>, never use asterisks (*) or quotes around titles. Example: <em>Macbeth</em> not *Macbeth* or "Macbeth"
- Always reference "${currentPlayName}"`
    } else if (analysisMode === 'fullfathomfive') {
      console.log('Full Fathom Five level detected - using comprehensive prompt with Language and Rhetoric sections');
      console.log('DEBUG: Function version updated at', new Date().toISOString());
      
      // Check if this play should EXCLUDE New Variorum Analysis - 21 plays without NV editions
      const includeNewVariorum = !playsWithoutNewVariorum.includes(playName)
      console.log(`🎭 Play: ${playName} - Include New Variorum? ${includeNewVariorum}`)
      
      systemPrompt = `You are an expert Shakespearean scholar providing the most comprehensive analysis possible.

IMPORTANT CONTEXT: The input text will consist of 1–3 consecutive lines selected from a Shakespearean play. Analyze those lines only and avoid referencing any surrounding text. Focus on the content and meaning of the selected text without mentioning specific scenes, acts, or play names.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order. Do not skip any sections. EVERY section must be included:

**Plain-Language Paraphrase:** (REQUIRED - FIRST SECTION)  
**Language and Rhetoric:** (REQUIRED - NEW SECTION)  
**Synopsis:** (REQUIRED - Focus on the content and meaning of the selected text without mentioning specific scenes)  
**Key Words & Glosses:** (REQUIRED)  
**Historical Context:** (REQUIRED)  
**Sources:** (REQUIRED)  
**Literary Analysis:** (REQUIRED)  
**Critical Reception:** (REQUIRED)  
**Similar phrases or themes in other plays:** (REQUIRED)${includeNewVariorum ? '\n**New Variorum Analysis:** (REQUIRED)' : ''}

FORMAT REQUIREMENTS:
- Start each section with the exact heading format shown above (colons are already included).
- Provide 6–12 sentences per section; use complete, scholarly style.
- Always italicize titles using \`<em>italics</em>\`, never quote them or italicize author names.
- **Key Words & Glosses**: Use format \`"word" means [definition]; "word" means [definition]\`.
- **Language and Rhetoric**: Include (1) etymology from 1914 OED, (2) rhetorical devices, (3) meter & rhythm, with citations.

LITERARY ANALYSIS REQUIREMENTS:
- Do NOT name any specific critics or scholars — no personal names whatsoever.
- Structure the section as a series of school-based readings. For each school included, write EXACTLY 3–4 full sentences that build a genuine critical argument: state the school's interpretive lens, apply it specifically to this passage, develop the implication, and draw a conclusion. A single sentence or a vague gesture is not acceptable — every entry must read as a short critical paragraph.
- Select only the schools that have something genuinely meaningful to say about this specific passage. Do NOT force schools that do not apply — quality over quantity. Do NOT pad with superficial entries just to reach a number.
- For the schools you do include: go deep, not broad. A tight 3-sentence argument from 5 schools is far better than a 1-sentence mention of 15 schools.
- Feminist criticism must engage substantively even in male-dominated passages — analyse what the structural exclusion of women reveals about ideology, power, or the limits of the text's moral world. Do not use "absence of women" as a way to dismiss the school in one sentence.
- Draw on any of the following schools where genuinely applicable: Traditional/Humanist Criticism, New Criticism/Formalism, Historical and Biographical Criticism, Psychoanalytic Criticism, Feminist Criticism, New Historicism, Cultural Materialism, Marxist Criticism, Postcolonial Criticism, Race Studies, Queer Theory, Performance and Theater History Criticism, Ecocriticism, Disability Studies, Cognitive/Evolutionary Criticism, Textual/Editorial Criticism.
- Label each school clearly at the start of its paragraph, e.g. "From a feminist perspective,", "A Marxist reading would note,", "New Historicist criticism situates…"
- Do not invent critic names, book titles, or publication details.

LENGTH: 800–1200 words total`

      // Only add New Variorum Analysis instructions if this play should have it
      if (includeNewVariorum) {
        systemPrompt += `

**New Variorum Analysis:**
For this section, use the historical variorum notes provided below.  
- Display the EXACT notes linked to the line numbers passed in.  
- Do NOT summarize, truncate, or modify the notes in any way.  
- Do NOT invent or expand commentary beyond what is provided.  
- Show ALL notes from the database, not just summaries.
- DO NOT CUT OR TRUNCATE ANY NOTES - include the complete, full text.
- Even if notes are extremely long, you MUST include the ENTIRE text.
- Do not stop mid-sentence or cut off any part of the notes.
- Format each entry as:

[Line X] [EXACT commentary text from the provided notes]

- If no note exists for a line, output: [Line X] No commentary available.
- Notes must appear in the same order as the selected line numbers.
- Do not include notes for lines that are not explicitly selected.
- IMPORTANT: Copy the notes exactly as provided, word for word, without any changes.
- CRITICAL: Include the complete, unabridged text of every note, no matter how long.`
       
        // We no longer inline the full historical notes into the system prompt.
        // They are attached to the final response server‑side via the
        // "New Variorum Analysis" section, built directly from the JSON.
        if (relevantNotes.length === 0) {
          systemPrompt += `\n\nNOTE: No historical variorum notes were found for this text in the database. In the "New Variorum Analysis" section, state briefly that no traditional commentary was located for these lines.`
        }
      }
    } else if (analysisMode === 'followup') {
      // Special lightweight mode for "Ask a follow-up question"
      // The incoming text contains context plus a line that starts with
      // "Follow-up question:". We want to answer that question directly,
      // using the rest of the text only as background.
      systemPrompt = `You are a concise, expert Shakespeare guide answering a follow-up question about previously analyzed lines.

The user message you receive will contain:
- The current play name
- (Sometimes) the original selected passage
- (Sometimes) the previous analysis text
- A final line that begins with "Follow-up question:" followed by the user's actual question.

Your job:
- Identify the follow-up question and answer **that question only**.
- Use any other text purely as background context; do **not** summarize or critique it.
- Give a direct, helpful answer in 2–5 sentences.
- If the question is factual (e.g., "What year was the play written?"), just answer it clearly.
- Do **not** talk about "lines", "snippets", or how the input is structured unless the question explicitly asks about that.
- Do not restate the entire original passage or analysis; focus on the question.`;
    }
    
    // Build the user prompt
    let userPrompt
    if (analysisMode === 'followup') {
      userPrompt = `Here is the full context plus the follow-up question:\n\n${text}\n\nAnswer ONLY the follow-up question.`
    } else {
      userPrompt = `Text to analyze: "${text}"`
      
      if (isMultipleLines) {
        userPrompt += `\n\nThis selection contains ${lines.length} lines. Please provide analysis that considers both the individual lines and their relationship to each other.`
      }
      
      // We deliberately do NOT inline the full historical notes into the user prompt
      // any more, because they are extremely long and were causing very large
      // payloads and OpenAI timeouts. The raw notes are still attached to the
      // final response via the "New Variorum Analysis" section using relevantNotes.
      
      if (analysisMode === 'basic') {
        userPrompt += `\n\nPlease provide a Basic Analysis following the exact format specified in the system prompt.`
      } else if (analysisMode === 'expert') {
        userPrompt += `\n\nPlease provide an Expert Analysis following the exact format specified in the system prompt.`
      } else if (analysisMode === 'fullfathomfive') {
        userPrompt += `\n\nPlease provide a Full Fathom Five analysis following the exact format specified in the system prompt.`
      } else {
        userPrompt += `\n\nPlease provide a comprehensive ${analysisMode} analysis of this text.`
      }
      
      // Add critical instruction to avoid scene references
      userPrompt += `\n\nCRITICAL INSTRUCTION: Do NOT mention any specific scenes, acts, or play names in your synopsis. Focus only on the content and meaning of the selected text.`
    }
    
    // Get max_tokens from request or use default
    const maxTokens =
      analysisMode === 'fullfathomfive'
        ? 8000
        : analysisMode === 'followup'
        ? 800
        : 3000

    // Debug: Log the user prompt length
    console.log('User prompt length:', userPrompt.length)
    console.log('Max tokens:', maxTokens)
    
    // Use gpt-4o for full fathom five to handle longer responses better
    const modelToUse = analysisMode === 'fullfathomfive' ? 'gpt-4o' : model
    
    // Make the API call
    const completion = await openai.chat.completions.create({
      model: modelToUse,
      messages: [
        {
          role: "system",
          content: systemPrompt
        },
        {
          role: "user",
          content: userPrompt
        }
      ],
      temperature: analysisMode === 'fullfathomfive' ? 0.3 : 0.7,
      max_tokens: maxTokens
    })
    
    // Debug: Log response length
    console.log('Response length:', completion.choices[0].message.content.length)
    console.log('Full response preview:', completion.choices[0].message.content.substring(0, 500))
    console.log('Response ends with:', completion.choices[0].message.content.substring(completion.choices[0].message.content.length - 200))

    let response = completion.choices[0].message.content

    // Convert asterisks to proper HTML italics
    console.log('🔍 DEBUG: Original response contains asterisks:', response.includes('*'))
    console.log('🔍 DEBUG: Sample of original response:', response.substring(0, 200))
    
    // NUCLEAR APPROACH - Try EVERY possible asterisk pattern
    response = response.replace(/\*([^*]+)\*/g, '<span style="font-style: italic;">$1</span>')  // *text*
    response = response.replace(/\*([^*\n]+)\*/g, '<span style="font-style: italic;">$1</span>')  // *text* with newlines
    response = response.replace(/\*([^*\s]+)\*/g, '<span style="font-style: italic;">$1</span>')  // *text* with spaces
    response = response.replace(/\*\s*([^*]+?)\s*\*/g, '<span style="font-style: italic;">$1</span>')  // * text * with spaces
    response = response.replace(/\*([^*]*?)\*/g, '<span style="font-style: italic;">$1</span>')  // Most aggressive - any character
    
    // Extra aggressive conversion for Expert mode
    if (analysisMode === 'expert') {
      console.log('🔍 DEBUG: Applying extra Expert mode asterisk conversion')
      response = response.replace(/\*([^*]+?)\*/g, '<span style="font-style: italic;">$1</span>')  // More aggressive pattern
      response = response.replace(/\*([^*\n\r]+?)\*/g, '<span style="font-style: italic;">$1</span>')  // Handle line breaks
      response = response.replace(/\*([^*\s\n\r]+?)\*/g, '<span style="font-style: italic;">$1</span>')  // Handle spaces and breaks
      
      // Specific conversion for common play titles - FORCE ITALICS
      response = response.replace(/\*Macbeth\*/g, '<span style="font-style: italic;">Macbeth</span>')
      response = response.replace(/\*Hamlet\*/g, '<span style="font-style: italic;">Hamlet</span>')
      response = response.replace(/\*Romeo and Juliet\*/g, '<span style="font-style: italic;">Romeo and Juliet</span>')
      response = response.replace(/\*King Lear\*/g, '<span style="font-style: italic;">King Lear</span>')
      response = response.replace(/\*Othello\*/g, '<span style="font-style: italic;">Othello</span>')
      response = response.replace(/\*A Midsummer Night's Dream\*/g, '<span style="font-style: italic;">A Midsummer Night\'s Dream</span>')
      response = response.replace(/\*The Tempest\*/g, '<span style="font-style: italic;">The Tempest</span>')
      response = response.replace(/\*Twelfth Night\*/g, '<span style="font-style: italic;">Twelfth Night</span>')
      response = response.replace(/\*Much Ado About Nothing\*/g, '<span style="font-style: italic;">Much Ado About Nothing</span>')
      response = response.replace(/\*As You Like It\*/g, '<span style="font-style: italic;">As You Like It</span>')
    }
    
    console.log('🔍 DEBUG: After conversion contains asterisks:', response.includes('*'))
    console.log('🔍 DEBUG: Sample of converted response:', response.substring(0, 200))

    // Parse the response into structured sections
    let analysis = {}
    
    // Parse structured analysis
    const sections = structure
    let currentSection = null
    let currentContent = []

    const responseLines = response.split('\n')
    
    for (const line of responseLines) {
      const trimmedLine = line.trim()
      
      // Check if this line starts a new section
      const matchingSection = sections.find(section => 
        trimmedLine.toLowerCase().includes(section.toLowerCase()) ||
        trimmedLine.toLowerCase().startsWith(section.toLowerCase().replace(/\s+/g, '').toLowerCase()) ||
        trimmedLine.toLowerCase().startsWith(section.toLowerCase().replace(/[^a-zA-Z]/g, '').toLowerCase())
      )

      if (matchingSection && !currentSection) {
        currentSection = matchingSection
        currentContent = []
      } else if (matchingSection && currentSection) {
        // Save previous section
        analysis[currentSection] = currentContent.join('\n').trim()
        currentSection = matchingSection
        currentContent = []
      } else if (currentSection && trimmedLine) {
        currentContent.push(trimmedLine)
      }
    }

    // Save the last section
    if (currentSection && currentContent.length > 0) {
      analysis[currentSection] = currentContent.join('\n').trim()
    }

    // Convert asterisks to italics in all sections
    for (const section in analysis) {
      if (analysis[section]) {
        console.log(`🔍 DEBUG: Section "${section}" before conversion contains asterisks:`, analysis[section].includes('*'))
        // NUCLEAR APPROACH - Try EVERY possible asterisk pattern
        analysis[section] = analysis[section].replace(/\*([^*]+)\*/g, '<span style="font-style: italic;">$1</span>')  // *text*
        analysis[section] = analysis[section].replace(/\*([^*\n]+)\*/g, '<span style="font-style: italic;">$1</span>')  // *text* with newlines
        analysis[section] = analysis[section].replace(/\*([^*\s]+)\*/g, '<span style="font-style: italic;">$1</span>')  // *text* with spaces
        analysis[section] = analysis[section].replace(/\*\s*([^*]+?)\s*\*/g, '<span style="font-style: italic;">$1</span>')  // * text * with spaces
        analysis[section] = analysis[section].replace(/\*([^*]*?)\*/g, '<span style="font-style: italic;">$1</span>')  // Most aggressive - any character
        
        // Extra aggressive conversion for Expert mode
        if (analysisMode === 'expert') {
          console.log(`🔍 DEBUG: Applying extra Expert mode conversion to section "${section}"`)
          analysis[section] = analysis[section].replace(/\*([^*]+?)\*/g, '<span style="font-style: italic;">$1</span>')  // More aggressive pattern
          analysis[section] = analysis[section].replace(/\*([^*\n\r]+?)\*/g, '<span style="font-style: italic;">$1</span>')  // Handle line breaks
          analysis[section] = analysis[section].replace(/\*([^*\s\n\r]+?)\*/g, '<span style="font-style: italic;">$1</span>')  // Handle spaces and breaks
          
          // Specific conversion for common play titles - FORCE ITALICS
          analysis[section] = analysis[section].replace(/\*Macbeth\*/g, '<span style="font-style: italic;">Macbeth</span>')
          analysis[section] = analysis[section].replace(/\*Hamlet\*/g, '<span style="font-style: italic;">Hamlet</span>')
          analysis[section] = analysis[section].replace(/\*Romeo and Juliet\*/g, '<span style="font-style: italic;">Romeo and Juliet</span>')
          analysis[section] = analysis[section].replace(/\*King Lear\*/g, '<span style="font-style: italic;">King Lear</span>')
          analysis[section] = analysis[section].replace(/\*Othello\*/g, '<span style="font-style: italic;">Othello</span>')
          analysis[section] = analysis[section].replace(/\*A Midsummer Night's Dream\*/g, '<span style="font-style: italic;">A Midsummer Night\'s Dream</span>')
          analysis[section] = analysis[section].replace(/\*The Tempest\*/g, '<span style="font-style: italic;">The Tempest</span>')
          analysis[section] = analysis[section].replace(/\*Twelfth Night\*/g, '<span style="font-style: italic;">Twelfth Night</span>')
          analysis[section] = analysis[section].replace(/\*Much Ado About Nothing\*/g, '<span style="font-style: italic;">Much Ado About Nothing</span>')
          analysis[section] = analysis[section].replace(/\*As You Like It\*/g, '<span style="font-style: italic;">As You Like It</span>')
        }
        
        console.log(`🔍 DEBUG: Section "${section}" after conversion contains asterisks:`, analysis[section].includes('*'))
      }
    }

    // Debug: Log what sections were found
    console.log('Parsed sections:', Object.keys(analysis))
    console.log('Looking for sections:', sections)
    
    // Check if New Variorum Analysis was captured (only for plays WITH New Variorum editions)
    // Exclude the 21 plays without New Variorum editions
    if (!playsWithoutNewVariorum.includes(playName)) {
      if (analysis['New Variorum Analysis']) {
        console.log('New Variorum Analysis found, length:', analysis['New Variorum Analysis'].length)
      } else {
        console.log('New Variorum Analysis NOT found in parsed sections')
        // Try multiple patterns to find it manually in the response
        const patterns = [
          /\*\*New Variorum Analysis\*\*:?\s*([\s\S]*?)(?=\*\*|$)/i,
          /New Variorum Analysis:?\s*([\s\S]*?)(?=\*\*|$)/i,
          /New Variorum Analysis:?\s*([\s\S]*)/i
        ]
        
        for (const pattern of patterns) {
          const variorumMatch = response.match(pattern)
          if (variorumMatch) {
            console.log('Found New Variorum Analysis manually with pattern, length:', variorumMatch[1].length)
            analysis['New Variorum Analysis'] = variorumMatch[1].trim()
            break
          }
        }
        
        // If still not found, try to find it by looking for the notes content
        if (!analysis['New Variorum Analysis'] && !playsWithoutNewVariorum.includes(playName)) {
          const notesMatch = response.match(/(\[Line \d+\].*?)(?=\*\*|$)/s)
          if (notesMatch) {
            console.log('Found notes content manually, length:', notesMatch[1].length)
            analysis['New Variorum Analysis'] = notesMatch[1].trim()
          }
        }
      }
    } else {
      // For plays WITHOUT New Variorum editions, remove any New Variorum Analysis that may have been generated
      if (analysis['New Variorum Analysis']) {
        console.log(`🚫 Removing New Variorum Analysis for blacklisted play: ${playName}`)
        delete analysis['New Variorum Analysis']
      }
    }

    // If parsing failed, return the raw response
    if (Object.keys(analysis).length === 0) {
      analysis = { 'Analysis': response }
    }

    // For fullfathomfive level only, add the notes directly to the analysis object (only for plays WITH NV editions)
    if (analysisMode === 'fullfathomfive' && !playsWithoutNewVariorum.includes(playName)) {
      if (relevantNotes.length > 0) {
        let notesContent = ''
        relevantNotes.forEach((note, index) => {
          notesContent += `[Line ${note.line}] ${note.play}\n`
          note.notes.forEach((noteText, noteIndex) => {
            notesContent += `${noteText}\n\n`
          })
        })
        analysis['New Variorum Analysis'] = notesContent.trim()
      } else {
        analysis['New Variorum Analysis'] = 'No historical commentary found for the selected text in the database.'
      }
    }

    // Post-process the response to remove any scene references
    let processedResponse = response;
    
    // Remove any scene references from the synopsis
    processedResponse = processedResponse.replace(
      /In (ACT \d+, SCENE \d+|Act \d+, Scene \d+|Unknown Scene) of Macbeth/g,
      'In this passage'
    );
    processedResponse = processedResponse.replace(
      /In (ACT \d+, SCENE \d+|Act \d+, Scene \d+|Unknown Scene)/g,
      'In this passage'
    );
    
    console.log('🔧 POST-PROCESSING: Removed scene references from response');

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        choices: [{
          message: {
            content: processedResponse
          }
        }],
        analysis: analysis,
        mode: analysisMode,
        text: text,
        lineCount: lines.length,
        relevantNotes: relevantNotes,
        usage: completion.usage
      })
    }

  } catch (error) {
    console.error('Error:', error)
    
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ 
        error: 'Internal server error',
        details: error.message 
      })
    }
  }
}