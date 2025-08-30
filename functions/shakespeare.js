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
    const { text, mode = 'basic', scene, play, followUp, previousAnalysis } = JSON.parse(event.body)

    if (!text) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Text is required' })
      }
    }

    // Define analysis structure based on mode
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
    }

    const structure = analysisStructure[mode] || analysisStructure.basic

    // Build the system prompt
    let systemPrompt = `You are a Shakespeare scholar providing ${mode} analysis. Analyze the following text from ${play} (${scene}).`

    if (followUp && previousAnalysis) {
      systemPrompt += `\n\nThis is a follow-up question about a previous analysis. Please provide a detailed response that builds upon the previous analysis.`
    } else {
      systemPrompt += `\n\nProvide analysis in the following structure:\n${structure.map(section => `- ${section}`).join('\n')}`
    }

    systemPrompt += `\n\nFormat your response as structured sections. For each section, provide comprehensive analysis that would be appropriate for ${mode === 'basic' ? 'undergraduate students' : mode === 'expert' ? 'graduate students and scholars' : 'advanced scholars and researchers'}.

Use proper scholarly language and provide specific examples from Shakespeare's works when relevant. Include citations and references where appropriate.`

    // Build the user prompt
    let userPrompt = `Text to analyze: "${text}"`

    if (followUp) {
      userPrompt += `\n\nFollow-up question: ${followUp}`
      if (previousAnalysis) {
        userPrompt += `\n\nPrevious analysis context: ${JSON.stringify(previousAnalysis)}`
      }
    }

    userPrompt += `\n\nPlease provide a comprehensive ${mode} analysis of this text.`

    // Make the API call
    const completion = await openai.chat.completions.create({
      model: "gpt-4",
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
      max_tokens: 2000
    })

    const response = completion.choices[0].message.content

    // Parse the response into structured sections
    let analysis = {}
    
    if (followUp) {
      // For follow-up questions, return the response as-is
      analysis = response
    } else {
      // Parse structured analysis
      const sections = structure
      let currentSection = null
      let currentContent = []

      const lines = response.split('\n')
      
      for (const line of lines) {
        const trimmedLine = line.trim()
        
        // Check if this line starts a new section
        const matchingSection = sections.find(section => 
          trimmedLine.toLowerCase().includes(section.toLowerCase()) ||
          trimmedLine.toLowerCase().startsWith(section.toLowerCase().replace(/\s+/g, '').toLowerCase())
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
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        analysis: analysis,
        mode: mode,
        text: text,
        scene: scene,
        play: play
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
