const { OpenAI } = require('openai')

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

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
    const { text, level = 'basic', model = 'gpt-4o-mini', mode } = JSON.parse(event.body)

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
      detailed: [
        'Plain-Language Paraphrase',
        'Language and Rhetoric',
        'Synopsis',
        'Key Words & Glosses',
        'Historical Context',
        'Literary Analysis',
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
        'Commentary',
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
    }

    const structure = analysisStructure[analysisMode] || analysisStructure.basic

    // Check if text contains multiple lines
    const lines = text.split('\n').filter(line => line.trim().length > 0)
    const isMultipleLines = lines.length >= 2 && lines.length <= 5

    // Build the system prompt
    let systemPrompt = `You are a Shakespeare scholar providing ${analysisMode} analysis.`

    if (isMultipleLines) {
      systemPrompt += `\n\nYou are analyzing ${lines.length} selected lines from Shakespeare's work. Provide a comprehensive analysis that considers the relationship between these lines and their combined meaning.`
    }

    if (analysisMode === 'fullfathomfive') {
      systemPrompt += `\n\nIn Full Fathom Five mode, you should provide both commentary (if available for the text) and analysis. If no specific commentary exists for the selected text, indicate this clearly and provide comprehensive analysis instead.`
    }

    systemPrompt += `\n\nProvide analysis in the following structure:\n${structure.map(section => `- ${section}`).join('\n')}`

    systemPrompt += `\n\nFormat your response as structured sections. For each section, provide comprehensive analysis that would be appropriate for ${analysisMode === 'basic' ? 'undergraduate students' : analysisMode === 'detailed' ? 'advanced students' : analysisMode === 'expert' ? 'graduate students and scholars' : 'advanced scholars and researchers'}.

Use proper scholarly language and provide specific examples from Shakespeare's works when relevant. Include citations and references where appropriate.

For the Commentary section (in Full Fathom Five mode), provide traditional scholarly commentary if available, or clearly state "No traditional commentary available for this text" and proceed with modern analysis.`

    // Build the user prompt
    let userPrompt = `Text to analyze: "${text}"`

    if (isMultipleLines) {
      userPrompt += `\n\nThis selection contains ${lines.length} lines. Please provide analysis that considers both the individual lines and their relationship to each other.`
    }

    userPrompt += `\n\nPlease provide a comprehensive ${analysisMode} analysis of this text.`

    // Make the API call
    const completion = await openai.chat.completions.create({
      model: model,
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
      temperature: 0.7,
      max_tokens: 3000
    })

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

    // If parsing failed, return the raw response
    if (Object.keys(analysis).length === 0) {
      analysis = { 'Analysis': response }
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        analysis: analysis,
        mode: analysisMode,
        text: text,
        lineCount: lines.length,
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
