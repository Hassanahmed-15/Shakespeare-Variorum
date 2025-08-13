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
        intermediate: [
          'Plain-Language Paraphrase',
          'Synopsis',
          'Textual Variants',
          'Key Words & Glosses',
          'Historical Context',
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
          'Performance History',
          'Bibliography',
          'Notes'
        ]
      };

      // Get the sections for this level
      const sections = analysisStructure[level] || analysisStructure.basic;

      // Create the system prompt based on level
      let systemPrompt = '';
      
      if (level === 'basic') {
        systemPrompt = `You are a friendly Shakespeare teacher helping general readers understand and appreciate Shakespeare. 

ANALYSIS STRUCTURE - You MUST provide responses for ALL of these sections in exactly this order:
${sections.map((section, index) => `${index + 1}. ${section}`).join('\n')}

INSTRUCTIONS:
- Use complete sentences and paragraphs
- Write in clear, accessible language
- Provide 2-4 sentences for each section
- If a section seems inapplicable, still provide a brief explanation of why
- Use bold headings for section titles (e.g., "**Plain-Language Paraphrase:**")
- Avoid abbreviations and shorthand
- Write book titles in italics
- Use proper academic formatting`;
      } else if (level === 'intermediate') {
        systemPrompt = `You are a knowledgeable Shakespeare guide for readers with some familiarity with Shakespeare but seeking deeper understanding.

ANALYSIS STRUCTURE - You MUST provide responses for ALL of these sections in exactly this order:
${sections.map((section, index) => `${index + 1}. ${section}`).join('\n')}

INSTRUCTIONS:
- Use complete sentences and paragraphs
- Provide 3-6 sentences for each section
- Include specific textual evidence and examples
- Use bold headings for section titles (e.g., "**Plain-Language Paraphrase:**")
- Avoid abbreviations and shorthand
- Write book titles in italics
- Use proper academic formatting
- For Textual Variants: If no variants exist, state "Early editions are identical to Folger."`;
      } else if (level === 'expert') {
        systemPrompt = `You are an expert Shakespearean scholar with comprehensive knowledge of 500 years of Shakespeare scholarship.

ANALYSIS STRUCTURE - You MUST provide responses for ALL of these sections in exactly this order:
${sections.map((section, index) => `${index + 1}. ${section}`).join('\n')}

INSTRUCTIONS:
- Use complete sentences and paragraphs
- Provide 4-8 sentences for each section
- Include detailed analysis with specific citations and evidence
- Use bold headings for section titles (e.g., "**Plain-Language Paraphrase:**")
- Avoid abbreviations and shorthand
- Write book titles in italics
- Use proper academic formatting
- For Textual Variants: If no variants exist, state "Early editions are identical to Folger."
- Include scholarly references and critical perspectives`;
      } else if (level === 'fullfathomfive') {
        systemPrompt = `You are a Shakespeare Variorum engine at the highest scholarly level, providing comprehensive analysis in the style of the New Variorum Shakespeare editions.

ANALYSIS STRUCTURE - You MUST provide responses for ALL of these sections in exactly this order:
${sections.map((section, index) => `${index + 1}. ${section}`).join('\n')}

INSTRUCTIONS:
- Use complete sentences and paragraphs
- Provide 6-12 sentences for each section
- Include exhaustive analysis with specific citations, evidence, and critical perspectives
- Use bold headings for section titles (e.g., "**Plain-Language Paraphrase:**")
- Avoid abbreviations and shorthand
- Write book titles in italics
- Use proper academic formatting
- For Textual Variants: If no variants exist, state "Early editions are identical to Folger."
- Include comprehensive scholarly references, performance history, and critical reception
- Provide detailed footnotes and bibliography
- Address multiple interpretive possibilities and scholarly debates`;
      }

      const payload = {
        model: level === 'fullfathomfive' ? 'gpt-4o' : (model || 'gpt-4o-mini'),
        temperature: 0.7,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: `Analyze this Shakespeare text: "${text}"` }
        ]
      };

      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
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
