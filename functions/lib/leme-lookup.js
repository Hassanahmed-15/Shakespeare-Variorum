const { loadJsonIndex, extractLookupCandidates } = require('./lexical-utils')

let indexCache = null

const LEME_CITATION =
  'Lexicons of Early Modern English (LEME), University of Toronto. CC BY 4.0. https://leme.library.utoronto.ca/'

const SHORT_CITATIONS = {
  cawdrey: 'Cawdrey, A Table Alphabeticall, 1604',
  bullokar: 'Bullokar, An English Expositor, 1616',
  cockeram: 'Cockeram, The English Dictionarie, 1623',
  florio: 'Florio, A Worlde of Wordes, 1598',
  cotgrave: 'Cotgrave, A Dictionarie of the French and English Tongues, 1611',
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
      edition: 'Cawdrey 1604; Bullokar 1616; Cockeram 1623; Florio 1598; Cotgrave 1611',
    },
    hits,
    hitCount: hits.length,
  }
}

function formatLemeBlock(lookupResult) {
  if (!lookupResult.hits.length) {
    return [
      'CONTEMPORARY PERIOD LEXICONS (LEME: Cawdrey 1604, Bullokar 1616, Cockeram 1623; Florio 1598; Cotgrave 1611):',
      'No matching headwords in the indexed period dictionaries for this passage.',
      'Do not invent Elizabethan dictionary definitions.',
      `Corpus: ${LEME_CITATION}`,
    ].join('\n')
  }

  const blocks = lookupResult.hits.map(({ query, entry }) => {
    const short = SHORT_CITATIONS[entry.source_id] || entry.citation
    const lang = entry.lemma_lang ? ` (${entry.lemma_lang.toUpperCase()} lemma)` : ''
    const matchNote = entry.match_type === 'english_gloss' ? ` [English gloss match: "${query}"]` : ''
    return [`▸ ${entry.headword}${lang}${matchNote}`, `  ${entry.text}`, `  Cite: ${short}`].join('\n')
  })

  return [
    'CONTEMPORARY PERIOD LEXICONS (LEME) — POSSIBLE ELIZABETHAN/JACOBEAN SENSES.',
    'Includes English hard-word lexicons and bilingual Florio/Cotgrave entries matched via English gloss terms.',
    'For bilingual hits, cite the foreign lemma and dictionary year; note the match is via English wording in the gloss.',
    'Example: (Florio, A Worlde of Wordes, 1598) under Italian lemma Abbandonare.',
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
      lemma_lang: entry.lemma_lang,
      match_type: entry.match_type,
      source_id: entry.source_id,
      source_year: entry.source_year,
      source_title: entry.source_title,
      citation: SHORT_CITATIONS[entry.source_id] || entry.citation,
    })),
  }
}

module.exports = { lookupForText, formatLemeBlock, formatForUI, SHORT_CITATIONS }
