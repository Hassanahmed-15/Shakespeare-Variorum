const onions = require('./onions-lookup')
const schmidt = require('./schmidt-lookup')
const geneva = require('./geneva-lookup')

const GROUNDED_TIERS = new Set(['basic', 'expert', 'fullfathomfive'])

function applySourceGrounding({ analysisMode, text, systemPrompt, userPrompt }) {
  if (!GROUNDED_TIERS.has(analysisMode)) {
    return { systemPrompt, userPrompt, sourceLookup: null, lexicalLookup: null }
  }

  const maxWords = analysisMode === 'basic' ? 4 : 8

  const onionsResult = onions.lookupForText(text, { maxWords })
  const schmidtResult = schmidt.lookupMisses(onionsResult.misses.slice(0, maxWords))
  const genevaResult = geneva.lookupForText(text, {
    maxHits: analysisMode === 'basic' ? 2 : 5,
  })

  const systemAddendum = `

SOURCE GROUNDING RULES:
- Onions (1911/1919): primary Shakespeare glossary for Key Words & Glosses and archaic usage.
- Schmidt (1902): supplementary lexicon for headwords Onions does not cover.
- Geneva Bible (1599): candidate biblical parallels for Sources / historical-theological context only.
- Use supplied source text verbatim; do not cite the Oxford English Dictionary unless a supplied entry references it.
- Label Geneva matches as possible parallels unless the wording is an exact match.
- If no entry is supplied for a word, write "not in retrieved [source name]."

CITATION FORMAT (REQUIRED in Key Words & Glosses and Language and Rhetoric):
- End every gloss drawn from Onions with: (Onions, A Shakespeare Glossary, 1911/1919)
- End every gloss drawn from Schmidt with: (Schmidt, Shakespeare-Lexicon, 1902)
- Example: "incarnadine" means [to tinge with red] (Onions, A Shakespeare Glossary, 1911/1919).
- Example: "coil" means [turmoil, bustle, confusion] (Schmidt, Shakespeare-Lexicon, 1902).
- Do not gloss archaic words from model memory without a retrieved entry and citation.`

  const userAddendum = `

---
${onions.formatOnionsBlock(onionsResult)}

${schmidt.formatSchmidtBlock(schmidtResult)}

${geneva.formatGenevaBlock(genevaResult)}
---`

  const sourceLookup = {
    onions: onions.formatOnionsForUI(onionsResult),
    schmidt: schmidt.formatForUI(schmidtResult),
    geneva: geneva.formatForUI(genevaResult),
  }

  return {
    systemPrompt: systemPrompt + systemAddendum,
    userPrompt: userPrompt + userAddendum,
    sourceLookup,
    lexicalLookup: sourceLookup.onions,
  }
}

module.exports = { applySourceGrounding }
