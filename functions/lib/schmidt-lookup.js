const { loadJsonIndex, extractLookupCandidates } = require('./lexical-utils')

let indexCache = null
const CITATION =
  'Schmidt, Alexander. Shakespeare-Lexicon. 3rd ed., revised by Gregor Sarrazin. Berlin, 1902.'

function loadIndex() {
  if (!indexCache) {
    const { meta, entries } = loadJsonIndex('schmidt_lexicon_index.json')
    indexCache = { meta, entries }
  }
  return indexCache
}

function lookupHeadword(headword) {
  const { entries } = loadIndex()
  if (entries[headword]) return entries[headword]
  const hyphenated = headword.replace(/\s+/g, '-')
  if (entries[hyphenated]) return entries[hyphenated]
  return null
}

function lookupMisses(words) {
  const hits = []
  const misses = []
  for (const word of words) {
    const entry = lookupHeadword(word)
    if (entry) hits.push({ query: word, entry })
    else misses.push(word)
  }
  return {
    source: { citation: CITATION, title: 'Shakespeare-Lexicon', edition: '1902 (3rd ed., Sarrazin)' },
    hits,
    misses,
    hitCount: hits.length,
  }
}

function lookupForText(text, options = {}) {
  const candidates = extractLookupCandidates(text, options)
  return lookupMisses(candidates)
}

function formatSchmidtBlock(lookupResult) {
  if (!lookupResult.hits.length) {
    return [
      'LEXICAL SOURCE (Schmidt, Shakespeare-Lexicon, 1902):',
      'No matching headwords in the Schmidt index for this passage.',
      `Cite as: ${CITATION}`,
    ].join('\n')
  }

  const blocks = lookupResult.hits.map(({ entry }) => {
    const lines = [`▸ ${entry.headword}`]
    if (entry.forms) lines.push(`  (${entry.forms})`)
    lines.push(`  ${entry.text}`)
    return lines.join('\n')
  })

  return [
    'LEXICAL SOURCE (Schmidt, Shakespeare-Lexicon, 1902) — USE VERBATIM.',
    'Broader Shakespeare lexicon; retrieved in parallel with Onions. Use when Schmidt supplies a headword or a fuller entry than Onions.',
    `Cite as: ${CITATION}`,
    '',
    ...blocks,
  ].join('\n')
}

function formatForUI(lookupResult) {
  return {
    citation: CITATION,
    hits: lookupResult.hits.map(({ query, entry }) => ({
      query,
      headword: entry.headword,
      text: entry.text,
    })),
    misses: lookupResult.misses,
  }
}

module.exports = { lookupForText, lookupMisses, formatSchmidtBlock, formatForUI }
