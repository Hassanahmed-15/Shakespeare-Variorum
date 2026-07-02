const { loadJsonIndex, extractLookupCandidates } = require('./lexical-utils')

let indexCache = null

const LEME_CITATION =
  'Lexicons of Early Modern English (LEME), University of Toronto. CC BY 4.0. https://leme.library.utoronto.ca/'

const SHORT_CITATIONS = {
  cawdrey: 'Cawdrey, A Table Alphabeticall, 1604',
  bullokar: 'Bullokar, An English Expositor, 1616',
  cockeram: 'Cockeram, The English Dictionarie, 1623',
}

function loadIndex() {
  if (!indexCache) {
    const raw = loadJsonIndex('leme_period_index.json')
    indexCache = { meta: raw.meta, entries: raw.entries.entries || raw.entries }
  }
  return indexCache
}

function lookupHeadword(headword) {
  const { entries } = loadIndex()
  return entries[headword] || null
}

function lookupForText(text, { maxWords = 6, maxHits = 4 } = {}) {
  const candidates = extractLookupCandidates(text, { maxWords })
  const hits = []
  const seen = new Set()

  for (const word of candidates) {
    const sourceEntries = lookupHeadword(word)
    if (!sourceEntries) continue

    for (const entry of sourceEntries) {
      const dedupeKey = `${entry.source_id}:${entry.headword}`
      if (seen.has(dedupeKey)) continue
      seen.add(dedupeKey)
      hits.push({ query: word, entry })
      if (hits.length >= maxHits) break
    }
    if (hits.length >= maxHits) break
  }

  return {
    source: {
      citation: LEME_CITATION,
      title: 'LEME Period Lexicons',
      edition: 'Cawdrey 1604; Bullokar 1616; Cockeram 1623',
    },
    hits,
    hitCount: hits.length,
  }
}

function formatLemeBlock(lookupResult) {
  if (!lookupResult.hits.length) {
    return [
      'CONTEMPORARY PERIOD LEXICONS (LEME: Cawdrey 1604, Bullokar 1616, Cockeram 1623):',
      'No matching headwords in the indexed period dictionaries for this passage.',
      'Do not invent Elizabethan dictionary definitions.',
      `Corpus: ${LEME_CITATION}`,
    ].join('\n')
  }

  const blocks = lookupResult.hits.map(({ entry }) => {
    const short = SHORT_CITATIONS[entry.source_id] || entry.citation
    return [`▸ ${entry.headword} [${entry.source_id}, ${entry.source_year}]`, `  ${entry.text}`, `  Cite: ${short}`].join('\n')
  })

  return [
    'CONTEMPORARY PERIOD LEXICONS (LEME) — POSSIBLE ELIZABETHAN/JACOBEAN SENSES.',
    'These are hard-word dictionaries contemporary with Shakespeare, not modern Shakespeare glossaries.',
    'For Key Words & Glosses and Historical Context: cite the specific dictionary and year when used.',
    'Example citation: (Cawdrey, A Table Alphabeticall, 1604).',
    `Corpus: ${LEME_CITATION}`,
    '',
    ...blocks,
  ].join('\n')
}

function formatForUI(lookupResult) {
  return {
    citation: LEME_CITATION,
    hits: lookupResult.hits.map(({ query, entry }) => ({
      query,
      headword: entry.headword,
      text: entry.text,
      source_id: entry.source_id,
      source_year: entry.source_year,
      source_title: entry.source_title,
      citation: SHORT_CITATIONS[entry.source_id] || entry.citation,
    })),
  }
}

module.exports = { lookupForText, formatLemeBlock, formatForUI, SHORT_CITATIONS }
