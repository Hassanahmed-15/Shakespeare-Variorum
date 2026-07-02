const { lookupForText, formatOnionsBlock, formatOnionsForUI } = require('./onions-lookup')

const LEXICAL_GROUNDED_TIERS = new Set(['basic', 'expert', 'fullfathomfive'])

function applyLexicalGrounding({ analysisMode, text, systemPrompt, userPrompt }) {
  if (!LEXICAL_GROUNDED_TIERS.has(analysisMode)) {
    return { systemPrompt, userPrompt, lexicalLookup: null }
  }

  const lexicalLookup = lookupForText(text, {
    maxWords: analysisMode === 'basic' ? 4 : 8,
  })
  const onionsBlock = formatOnionsBlock(lexicalLookup)

  const systemAddendum = `

LEXICAL GROUNDING (Onions, A Shakespeare Glossary, 1911/1919):
- The user message includes verbatim excerpts from C. T. Onions's Shakespeare glossary.
- For **Key Words & Glosses**: use these entries when present; they are Shakespeare-specific.
- For **Language and Rhetoric** (Full Fathom Five): archaic usage and word history should follow the supplied Onions text when a headword is present.
- Do not cite the Oxford English Dictionary unless the supplied Onions entry explicitly references it.
- If a word is absent from the Onions block, write: "not in Onions glossary."`

  const userAddendum = `

---
${onionsBlock}

Missed headwords: ${lexicalLookup.misses.join(', ') || 'none'}
---`

  return {
    systemPrompt: systemPrompt + systemAddendum,
    userPrompt: userPrompt + userAddendum,
    lexicalLookup: formatOnionsForUI(lexicalLookup),
  }
}

module.exports = { applyLexicalGrounding }
