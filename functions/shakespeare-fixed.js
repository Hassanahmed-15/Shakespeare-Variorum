const { OpenAI } = require('openai')
const fs = require('fs').promises
const path = require('path')

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
    console.log(`Loading ${playName} notes from JSON file`)
    
    let notesData = null;
    
    // Map play names to their JSON files
    const playFiles = {
      'macbeth': 'macbeth_notes_cleaned_play.json',
      'hamlet': 'hamlet_notes (1).json',
      'romeo': 'ROMEO_notes.json',
      'othello': 'othello_notes.json',
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
      const possiblePaths = [
      path.join(process.cwd(), `Public/Data/${fileName}`),
      path.join(process.cwd(), fileName),
      path.join(__dirname, `../Public/Data/${fileName}`),
      path.join(__dirname, `../${fileName}`)
  ];
    
    for (const filePath of possiblePaths) {
      try {
        console.log(`Trying to load from: ${filePath}`);
        const fileContent = await fs.readFile(filePath, 'utf8');
        notesData = JSON.parse(fileContent);
        console.log(`✅ Successfully loaded ${playName} notes from: ${filePath}`);
        console.log(`📊 Database contains ${Object.keys(notesData).length} scenes`);
        break;
      } catch (error) {
        console.log(`❌ Failed to load from ${filePath}: ${error.message}`);
      }
    }
    
    if (!notesData) {
      console.error(`❌ Could not load ${fileName} from any location`);
      return getFallbackNotes(text);
    }
    
    console.log(`✅ Successfully loaded ${playName} database with`, Object.keys(notesData).length, 'scenes')
    return processNotesWithData(notesData, text)
    
  } catch (error) {
    console.error(`Error loading ${playName} notes:`, error)
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
    const { text, level = 'basic', model = 'gpt-4o-mini', mode, playName, sceneName } = JSON.parse(event.body)

    if (!text) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Text is required' })
      }
    }

    // Determine the analysis mode
    const analysisMode = mode || level

    // Define analysis structure based on mode
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
        'Language and Imagery',
        'Literary and Thematic Analysis',
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
        'Pointers for Further Reading',
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
      console.log('🔧 Final analysis structure:', structure)
    } else if (analysisMode === 'fullfathomfive') {
      console.log(`✅ ${playName} - INCLUDING New Variorum Analysis section`)
      console.log('🔧 Final analysis structure:', structure)
    }

    // Check if text contains multiple lines
    const lines = text.split('\n').filter(line => line.trim().length > 0)
    const isMultipleLines = lines.length >= 2 && lines.length <= 5

    // Find relevant notes from play database (only for Full Fathom Five)
    let relevantNotes = []
    if (analysisMode === 'fullfathomfive') {
      try {
        const currentPlayName = playName || 'Macbeth'
        relevantNotes = await findRelevantNotes(text, null, currentPlayName)
        console.log(`${currentPlayName} notes loaded:`, relevantNotes.length, 'notes found')
        console.log('Notes details:', relevantNotes)
      } catch (error) {
        console.error(`Failed to load ${currentPlayName} notes, continuing without them:`, error.message)
        relevantNotes = [] // Continue without notes if loading fails
      }
    }
    
    // Build the system prompt based on analysis mode
    let systemPrompt = ''
    const currentPlayName = playName || 'Macbeth'
    const currentSceneName = sceneName || 'Unknown Scene'
    
    // Debug: Log the scene information
    console.log('🎭 DEBUG: Received sceneName from frontend:', sceneName)
    console.log('🎭 DEBUG: Using currentSceneName:', currentSceneName)
    console.log('🎭 DEBUG: Received playName from frontend:', playName)
    console.log('🎭 DEBUG: Using currentPlayName:', currentPlayName)

    if (analysisMode === 'basic') {
      systemPrompt = `You are a university professor speaking to very smart undergraduates about Shakespeare.

IMPORTANT CONTEXT: You are analyzing text from a Shakespearean play. Focus on the content and meaning of the selected text without mentioning specific scenes, acts, or play names.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order:

**Plain-Language Paraphrase:**
**Synopsis:** (Do NOT mention any specific scene, act, or play name. Just describe the content and context of the selected text.)
**Key Words & Glosses:**
**Pointers for Further Reading:**

FORMAT REQUIREMENTS:
- Use EXACTLY the section headers shown above - do not change them
- 2–4 sentences per section
- Complete sentences and paragraphs
- Clear, accessible language
- Always reference "${currentPlayName}" and "${currentSceneName}" directly
- Titles in <em>italics</em>, never in quotes or asterisks
- Key Words format: "word" means definition; "word" means definition (preserve capitalization)`
    } else if (analysisMode === 'expert') {
      systemPrompt = `You are a Shakespeare scholar writing for advanced students.

IMPORTANT CONTEXT: Analyze text from "${currentPlayName}" (${currentSceneName}).

CRITICAL WARNING: Do NOT default to Act 1, Scene 1 in your synopsis. The current scene is ${currentSceneName}. Your synopsis must focus specifically on the events and context of ${currentSceneName}, not the opening scene of the play.

SYNOPSIS REQUIREMENT: Your synopsis must begin with "In ${currentSceneName} of Macbeth" and describe the specific events of that scene. If you write "In Act 1, Scene 1" when the current scene is ${currentSceneName}, your response will be incorrect.

FORMAT REQUIREMENTS:
- Structure your response into these sections in this exact order:

**Plain-Language Paraphrase:**
**Synopsis:** (Do NOT mention any specific scene, act, or play name. Just describe the content and context of the selected text.)
**Language and Imagery:**
**Literary and Thematic Analysis:**
**Pointers for Further Reading:**

- Use essay-style paragraphs (no bullets/lists)
- Each section should be 5–8 sentences
- Clear but scholarly tone
- Titles in <em>italics</em>, never in quotes or asterisks
- Always reference "${currentPlayName}" and "${currentSceneName}"`
    } else if (analysisMode === 'fullfathomfive') {
      console.log('Full Fathom Five level detected - using comprehensive prompt with Textual Variants and Language and Rhetoric sections');
      console.log('DEBUG: Function version updated at', new Date().toISOString());
      
      // Check if this play has New Variorum Analysis - exclude the 21 plays without editions
      const playsWithoutNewVariorum = [
        'allswell', 'comedyoferrors', 'measureformeasure', 'merrywives',
        'pericles', 'taming', 'troilus', 'twogentlemen',
        'henryvi1', 'henryvi2', 'henryvi3', 'henryviii',
        'richardii', 'richardiii', 'antony', 'coriolanus',
        'henryv', 'titus', 'timon', 'henryiv2'
      ];
      const includeNewVariorum = !playsWithoutNewVariorum.includes(playName)
      
      systemPrompt = `You are an expert Shakespearean scholar providing the most comprehensive analysis possible.

IMPORTANT CONTEXT: You are analyzing text from a Shakespearean play. Focus on the content and meaning of the selected text without mentioning specific scenes, acts, or play names.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order. Do not skip any sections. EVERY section must be included:

**Textual Variants:** (REQUIRED - FIRST SECTION)  
**Plain-Language Paraphrase:** (REQUIRED)  
**Language and Rhetoric:** (REQUIRED - NEW SECTION)  
**Synopsis:** (REQUIRED - Focus on the specific events and context of ${currentSceneName}, not Act 1, Scene 1)  
**Key Words & Glosses:** (REQUIRED)  
**Historical Context:** (REQUIRED)  
**Sources:** (REQUIRED)  
**Literary Analysis:** (REQUIRED)  
**Critical Reception:** (REQUIRED)  
**Similar phrases or themes in other plays:** (REQUIRED)  
**Pointers for Further Reading:** (REQUIRED)${includeNewVariorum ? '\n**New Variorum Analysis:** (REQUIRED)' : ''}

FORMAT REQUIREMENTS:
- Start each section with the exact heading format shown above (colons are already included).
- Provide 6–12 sentences per section; use complete, scholarly style.
- Always italicize titles using \`<em>italics</em>\`, never quote them or italicize author names.
- **Key Words & Glosses**: Use format \`"word" means [definition]; "word" means [definition]\`.
- **Textual Variants**: If none exist, say "Early editions are identical to Folger."
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

      // Add New Variorum Analysis instructions only if it's not As You Like It
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
      }
       
      // Add play notes if available (only if New Variorum Analysis is included)
      if (relevantNotes.length > 0 && includeNewVariorum) {
        systemPrompt += `\n\nIMPORTANT: You have access to historical variorum notes from the ${currentPlayName} database. Here are the relevant notes found:`
        
        relevantNotes.forEach((note, index) => {
          systemPrompt += `\n\n[Line ${note.line}] ${note.play}`
          note.notes.forEach((noteText, noteIndex) => {
            systemPrompt += `\n\nNote ${noteIndex + 1}: ${noteText}`
          })
        })
        
        systemPrompt += `\n\nUse these exact notes in your "New Variorum Analysis" section. Format each note as: [Line X] [Commentary from notes]. Do not add any additional commentary or speculation.`
      }
    }

    // Build the user prompt
    let userPrompt = `Text to analyze: "${text}"`

    if (isMultipleLines) {
      userPrompt += `\n\nThis selection contains ${lines.length} lines. Please provide analysis that considers both the individual lines and their relationship to each other.`
    }

    if (analysisMode === 'basic') {
      userPrompt += `\n\nPlease provide a Basic Analysis following the exact format specified in the system prompt.`
    } else if (analysisMode === 'expert') {
      userPrompt += `\n\nPlease provide an Expert Analysis following the exact format specified in the system prompt.`
    } else if (analysisMode === 'fullfathomfive') {
      userPrompt += `\n\nPlease provide a Full Fathom Five analysis following the exact format specified in the system prompt.`
      
      // Only add notes for plays that have New Variorum Analysis
      if (relevantNotes.length > 0 && includeNewVariorum) {
        console.log('Adding notes to prompt. Total notes found:', relevantNotes.length)
        relevantNotes.forEach((note, index) => {
          console.log(`Note ${index + 1}: Line ${note.line}, ${note.notes.length} note entries`)
          note.notes.forEach((noteText, noteIndex) => {
            console.log(`  Note entry ${noteIndex + 1} length:`, noteText.length)
          })
        })
        
        userPrompt += `\n\nHISTORICAL VARIORUM NOTES TO USE:`
        relevantNotes.forEach((note, index) => {
          userPrompt += `\n\n[Line ${note.line}] ${note.play}`
          note.notes.forEach((noteText, noteIndex) => {
            // Include the complete, full text of every note
            userPrompt += `\n${noteText}`
          })
        })
        userPrompt += `\n\nCRITICAL INSTRUCTIONS: Use these EXACT notes in your "New Variorum Analysis" section. Copy them word for word without any changes, summaries, or modifications. Show ALL notes from the database, not just parts of them. DO NOT TRUNCATE OR CUT ANY NOTES. Include the complete, full text of every note. Even if the notes are very long, you MUST include the ENTIRE text. Do not stop mid-sentence or cut off. Format each note as: [Line X] [EXACT commentary text from notes]. Do not add any additional commentary or speculation.

ABSOLUTE REQUIREMENT: Every single character of the provided notes must appear in your response. NO EXCEPTIONS. You must copy the notes exactly as provided, word for word, character for character. FAILURE TO INCLUDE COMPLETE NOTES WILL RESULT IN INCOMPLETE ANALYSIS.

IMPORTANT: The notes above are the COMPLETE notes from the database. You MUST include ALL of them in your "New Variorum Analysis" section. Do not summarize, do not truncate, do not cut off. Copy them exactly as shown above.`
      }
    } else {
      userPrompt += `\n\nPlease provide a comprehensive ${analysisMode} analysis of this text.`
    }
    
    // Add critical instruction to avoid scene references
    userPrompt += `\n\nCRITICAL INSTRUCTION: Do NOT mention any specific scenes, acts, or play names in your synopsis. Focus only on the content and meaning of the selected text.`

    // Get max_tokens from request or use default
    const maxTokens = (analysisMode === 'fullfathomfive' ? 8000 : 3000)

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

    const response = completion.choices[0].message.content

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

    // Debug: Log what sections were found
    console.log('Parsed sections:', Object.keys(analysis))
    console.log('Looking for sections:', sections)
    
    // Check if New Variorum Analysis was captured (only for plays with New Variorum editions)
    // Exclude the 21 plays without New Variorum editions
    const playsWithoutNewVariorum = [
      'allswell', 'comedyoferrors', 'measureformeasure', 'merrywives',
      'pericles', 'taming', 'troilus', 'twogentlemen',
      'henryvi1', 'henryvi2', 'henryvi3', 'henryviii',
      'richardii', 'richardiii', 'antony', 'coriolanus',
      'juliuscaesar', 'henryv', 'titus', 'timon', 'henryiv2'
    ];
    
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
        
        // If still not found, try to find it by looking for the notes content (only for plays with New Variorum)
        if (!analysis['New Variorum Analysis'] && !playsWithoutNewVariorum.includes(playName)) {
          const notesMatch = response.match(/(\[Line \d+\].*?)(?=\*\*|$)/s)
          if (notesMatch) {
            console.log('Found notes content manually, length:', notesMatch[1].length)
            analysis['New Variorum Analysis'] = notesMatch[1].trim()
          }
        }
      }
    }

    // If parsing failed, return the raw response
    if (Object.keys(analysis).length === 0) {
      analysis = { 'Analysis': response }
    }

    // For Full Fathom Five, add the notes directly to the analysis object (only for plays with New Variorum editions)
    if (analysisMode === 'fullfathomfive' && relevantNotes.length > 0 && !playsWithoutNewVariorum.includes(playName)) {
      let notesContent = ''
      relevantNotes.forEach((note, index) => {
        notesContent += `[Line ${note.line}] ${note.play}\n`
        note.notes.forEach((noteText, noteIndex) => {
          notesContent += `${noteText}\n\n`
        })
      })
      analysis['New Variorum Analysis'] = notesContent.trim()
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
