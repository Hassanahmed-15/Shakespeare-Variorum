const onions = require('./onions-lookup')
const schmidt = require('./schmidt-lookup')
const geneva = require('./geneva-lookup')
const leme = require('./leme-lookup')

const GROUNDED_TIERS = new Set(['basic', 'expert', 'fullfathomfive'])

function applySourceGrounding({ analysisMode, text, systemPrompt, userPrompt }) {
  if (!GROUNDED_TIERS.has(analysisMode)) {
    return { systemPrompt, userPrompt, sourceLookup: null, lexicalLookup: null }
  }

  const maxWords = analysisMode === 'basic' ? 4 : 8

  const onionsResult = onions.lookupForText(text, { maxWords })
  const schmidtResult = schmidt.lookupForText(text, { maxWords })
  const lemeResult = leme.lookupForText(text, {
    maxWords,
    maxHits: analysisMode === 'basic' ? 2 : 4,
  })
  const genevaResult = geneva.lookupForText(text, {
    maxHits: analysisMode === 'basic' ? 2 : 5,
  })

  const systemAddendum = `

SOURCE GROUNDING RULES:
- Onions (1911/1919): primary Shakespeare glossary for Key Words & Glosses and archaic usage.
- Schmidt (1902): supplementary Shakespeare lexicon; retrieved in parallel with Onions for the same passage lemmas. Prefer Onions for Shakespeare-specific glosses; use Schmidt when it adds coverage or a fuller entry.
- LEME period lexicons (Cawdrey 1604, Bullokar 1616, Cockeram 1623): contemporary hard-word dictionaries — use for Elizabethan/Jacobean senses in Historical Context and Key Words when supplied.
- Geneva Bible (1599): candidate biblical parallels for Sources / historical-theological context only.
- Use supplied source text verbatim; do not cite the Oxford English Dictionary unless a supplied entry references it.
- Label Geneva matches as possible parallels unless the wording is an exact match.
- If no entry is supplied for a word, write "not in retrieved [source name]."

CITATION FORMAT (REQUIRED in Key Words & Glosses and Language and Rhetoric):
- Onions: (Onions, A Shakespeare Glossary, 1911/1919)
- Schmidt: (Schmidt, Shakespeare-Lexicon, 1902)
- LEME: (Cawdrey, A Table Alphabeticall, 1604), (Bullokar, An English Expositor, 1616), (Cockeram, The English Dictionarie, 1623), (Florio, A Worlde of Wordes, 1598), or (Cotgrave, A Dictionarie of the French and English Tongues, 1611)
- Example: "abandon" means [cast away] (Cawdrey, A Table Alphabeticall, 1604).
- Do not gloss archaic words from model memory without a retrieved entry and citation.`

  const userAddendum = `

---
${onions.formatOnionsBlock(onionsResult)}

${schmidt.formatSchmidtBlock(schmidtResult)}

${leme.formatLemeBlock(lemeResult)}

${geneva.formatGenevaBlock(genevaResult)}
---`

  const sourceLookup = {
    onions: onions.formatOnionsForUI(onionsResult),
    schmidt: schmidt.formatForUI(schmidtResult),
    leme: leme.formatForUI(lemeResult),
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
