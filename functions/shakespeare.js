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
      const { text, level, model } = JSON.parse(event.body);

      if (!text) {
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: 'Text is required' })
        };
      }

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
          'Pointers for Further Reading'
        ],
        fullfathomfive: [
          'Plain-Language Paraphrase',
          'Synopsis',
          'Textual Variants',
          'Key Words & Glosses',
          'Historical Context',
          'Literary Analysis',
          'Critical Reception',
          'Performance History'
        ]
      };

      // Get the sections for this level
      const sections = analysisStructure[level] || analysisStructure.basic;

      // Create the system prompt based on level
      let systemPrompt = '';
      
      if (level === 'basic') {
        systemPrompt = `You are a friendly Shakespeare teacher helping general readers understand and appreciate Shakespeare. 

IMPORTANT CONTEXT: You are analyzing text from the play "${playName}" (${sceneName}). Always refer to this specific play and scene in your analysis.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order. Do not skip any sections:

${sections.map((section, index) => `**${section}:**`).join('\n')}

FORMAT REQUIREMENTS:
- Start each section with the exact heading format shown above
- Provide 2-4 sentences for each section
- Use complete sentences and paragraphs
- Write in clear, accessible language
- If a section seems inapplicable, still provide a brief explanation of why
- Avoid abbreviations and shorthand
- Write book titles in italics
- Use proper academic formatting
- Always reference the specific play "${playName}" and scene "${sceneName}" in your analysis

EXAMPLE FORMAT:
**Plain-Language Paraphrase:** This passage from ${playName} means [explanation in simple terms].

**Synopsis:** This language in ${playName} [what it does in context].

**Key Words & Glosses:** [word] means [definition]; [word] means [definition].

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
- Write book titles in italics
- Use proper academic formatting
- For Textual Variants: If no variants exist, state "Early editions are identical to Folger."
- Include scholarly references and critical perspectives
- Always reference the specific play "${playName}" and scene "${sceneName}" in your analysis

EXAMPLE FORMAT:
**Plain-Language Paraphrase:** This passage from ${playName} means [explanation in simple terms].

**Synopsis:** This language in ${playName} [what it does in context].

**Textual Variants:** [variants or "Early editions are identical to Folger."]

**Key Words & Glosses:** [word] means [definition]; [word] means [definition].

**Historical Context:** [relevant historical background in ${playName}].

**Literary Analysis:** [detailed literary analysis of ${playName}].

**Critical Reception:** [scholarly perspectives on ${playName}].

**Pointers for Further Reading:** Consider reading [suggestions].`;
      } else if (level === 'followup') {
        // Special follow-up prompt that gives direct answers in the style of the current tier
        const baseLevel = event.body ? JSON.parse(event.body).baseLevel || 'basic' : 'basic';
        
        if (baseLevel === 'basic') {
          systemPrompt = `You are a helpful Shakespeare expert. Answer the user's question directly and clearly in a simple, accessible style.

IMPORTANT CONTEXT: You are answering questions about the play "${playName}" (${sceneName}). Always refer to this specific play and scene in your answers.

FORMAT REQUIREMENTS:
- Provide a direct, concise answer to the question
- Use clear, accessible language
- Include relevant facts and context when helpful
- Write book titles in italics
- Avoid unnecessary formatting or section headers
- Keep responses focused and to the point
- Always reference the specific play "${playName}" and scene "${sceneName}" in your answers

EXAMPLE FORMAT:
[Direct answer to the question with relevant context and facts about ${playName}]`;
        } else if (baseLevel === 'expert') {
          systemPrompt = `You are a Shakespeare scholar. Answer the user's question with academic depth and scholarly insight.

IMPORTANT CONTEXT: You are answering questions about the play "${playName}" (${sceneName}). Always refer to this specific play and scene in your answers.

FORMAT REQUIREMENTS:
- Provide a comprehensive, scholarly answer to the question
- Include relevant historical context and critical perspectives
- Use academic language and cite specific details
- Write book titles in italics
- Avoid unnecessary formatting or section headers
- Keep responses focused but thorough
- Always reference the specific play "${playName}" and scene "${sceneName}" in your answers

EXAMPLE FORMAT:
[Scholarly answer with historical context and critical analysis of ${playName}]`;
        } else if (baseLevel === 'fullfathomfive') {
          systemPrompt = `You are a Shakespeare Variorum expert. Answer the user's question with the highest level of scholarly detail and comprehensive analysis.

IMPORTANT CONTEXT: You are answering questions about the play "${playName}" (${sceneName}). Always refer to this specific play and scene in your answers.

FORMAT REQUIREMENTS:
- Provide an exhaustive, scholarly answer to the question
- Include extensive historical context, critical reception, and performance history
- Use the most detailed academic language and cite specific evidence
- Write book titles in italics
- Avoid unnecessary formatting or section headers
- Keep responses comprehensive and thorough
- Always reference the specific play "${playName}" and scene "${sceneName}" in your answers

EXAMPLE FORMAT:
[Comprehensive scholarly answer with extensive context, critical perspectives, and detailed analysis of ${playName}]`;
        }
      } else if (level === 'fullfathomfive') {
        systemPrompt = `You are a Shakespeare Variorum engine at the highest scholarly level, providing comprehensive analysis in the style of the New Variorum Shakespeare editions.

IMPORTANT CONTEXT: You are analyzing text from the play "${playName}" (${sceneName}). Always refer to this specific play and scene in your analysis.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order. Do not skip any sections:

${sections.map((section, index) => `**${section}:**`).join('\n')}

FORMAT REQUIREMENTS:
- Start each section with the exact heading format shown above
- Provide 6-12 sentences for each section
- Use complete sentences and paragraphs
- Include exhaustive analysis with specific citations, evidence, and critical perspectives
- Avoid abbreviations and shorthand
- Write book titles in italics
- Use proper academic formatting
- For Textual Variants: If no variants exist, state "Early editions are identical to Folger."
- Include comprehensive scholarly references, performance history, and critical reception
- Provide detailed footnotes
- Address multiple interpretive possibilities and scholarly debates
- Always reference the specific play "${playName}" and scene "${sceneName}" in your analysis

EXAMPLE FORMAT:
**Plain-Language Paraphrase:** This passage from ${playName} means [explanation in simple terms].

**Synopsis:** This language in ${playName} [what it does in context].

**Textual Variants:** [variants or "Early editions are identical to Folger."]

**Key Words & Glosses:** [word] means [definition]; [word] means [definition].

**Historical Context:** [relevant historical background in ${playName}].

**Literary Analysis:** [detailed literary analysis of ${playName}].

**Critical Reception:** [scholarly perspectives on ${playName}].

**Performance History:** [performance history and interpretations of ${playName}].



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
          model: 'o4-mini',
          reasoning_effort: 'medium'
          // o4-mini doesn't support custom temperature, uses default (1)
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
            model: 'o4-mini',
            reasoning_effort: 'medium'
            // o4-mini doesn't support custom temperature, uses default (1)
          };
        } else if (baseLevel === 'fullfathomfive') {
          modelConfig = {
            model: 'gpt-4.1',
            temperature: 0.7
          };
        }
      } else if (level === 'fullfathomfive') {
        // Use gpt-4.1 for Full Fathom Five to avoid timeout issues with o3
        modelConfig = {
          model: 'gpt-4.1',
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

      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
        timeout: 180000 // 3 minute timeout
      });

      const data = await response.json();
      
      if (!response.ok) {
        console.error('OpenAI API error:', data);
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
