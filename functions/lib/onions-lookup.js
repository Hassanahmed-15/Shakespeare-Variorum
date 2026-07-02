/**
 * C. T. Onions, A Shakespeare Glossary (Clarendon Press, 1911; rev. 1919).
 * Public-domain source: https://archive.org/details/shakespearegloss00oniouoft
 */

const fs = require('fs')
const path = require('path')

let glossaryIndex = null

const STOPWORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
  'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
  'would', 'shall', 'should', 'may', 'might', 'must', 'can', 'could',
  'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
  'us', 'them', 'my', 'thy', 'thine', 'your', 'his', 'its', 'our', 'their',
  'this', 'that', 'these', 'those', 'not', 'no', 'so', 'if', 'then', 'than',
  'o', 'oh', 'ay', 'nay', 'yet', 'still', 'now', 'here', 'there', 'when',
  'where', 'why', 'how', 'all', 'some', 'more', 'most', 'such', 'what',
  'nor', 'and', 'but', 'let', 'come', 'go', 'see', 'say', 'make', 'take',
])

const LEMMA_OVERRIDES = {
  doth: 'do',
  dost: 'do',
  hath: 'have',
  hast: 'have',
  wherefore: 'wherefore',
  incarnardine: 'incarnadine',
  fadom: 'fathom',
}

function loadGlossaryIndex() {
  if (glossaryIndex) return glossaryIndex

  const candidates = [
    path.join(__dirname, '../../data/onions_glossary_index.json'),
    path.join(__dirname, '../data/onions_glossary_index.json'),
    path.join(process.cwd(), 'data/onions_glossary_index.json'),
  ]
  const filePath = candidates.find(p => fs.existsSync(p))
  if (!filePath) {
    throw new Error('Onions glossary index not found. Run scripts/build_onions_index.py')
  }

  const raw = JSON.parse(fs.readFileSync(filePath, 'utf8'))
  const { _meta, ...entries } = raw
  glossaryIndex = { meta: _meta || {}, entries }
  return glossaryIndex
}

function normalizeToken(token) {
  let t = token
    .toLowerCase()
    .replace(/^['']|['']$/g, '')
    .replace(/['']s$/, '')
    .replace(/['']d$/, '')
    .replace(/['']ll$/, '')
    .replace(/['']ve$/, '')
    .replace(/['']re$/, '')
    .replace(/[^a-z'-]/g, '')

  if (LEMMA_OVERRIDES[t]) return LEMMA_OVERRIDES[t]

  if (t.endsWith('eth') && t.length > 4) return t.slice(0, -3) + 'e'
  if (t.endsWith('est') && t.length > 4) return t.slice(0, -3)
  if (t.endsWith('ed') && t.length > 3) return t.slice(0, -2)
  if (t.endsWith('ing') && t.length > 4) return t.slice(0, -3)

  return t
}

function extractLookupCandidates(text, { maxWords = 8 } = {}) {
  const tokens = text
    .split(/\s+/)
    .map(normalizeToken)
    .filter(t => t.length > 2 && !STOPWORDS.has(t))

  const unique = [...new Set(tokens)]
  unique.sort((a, b) => b.length - a.length)
  return unique.slice(0, maxWords)
}

function lookupHeadword(headword) {
  const { entries } = loadGlossaryIndex()
  if (entries[headword]) return entries[headword]

  const hyphenated = headword.replace(/\s+/g, '-')
  if (entries[hyphenated]) return entries[hyphenated]

  return null
}

function lookupForText(text, options = {}) {
  const candidates = extractLookupCandidates(text, options)
  const hits = []
  const misses = []

  for (const word of candidates) {
    const entry = lookupHeadword(word)
    if (entry) hits.push({ query: word, entry })
    else misses.push(word)
  }

  const meta = loadGlossaryIndex().meta
  return {
    source: {
      author: meta.author || 'C. T. Onions',
      title: meta.title || 'A Shakespeare Glossary',
      edition: '1911 (rev. 1919)',
      publisher: meta.publisher || 'Clarendon Press, Oxford',
      citation:
        'Onions, C. T. A Shakespeare Glossary. Oxford: Clarendon Press, 1911 (rev. ed. 1919).',
    },
    hits,
    misses,
    hitCount: hits.length,
  }
}

function formatOnionsBlock(lookupResult) {
  const citation = lookupResult.source.citation

  if (!lookupResult.hits.length) {
    return [
      'LEXICAL SOURCE (Onions, A Shakespeare Glossary, 1911/1919):',
      'No matching headwords in the Onions index for this passage.',
      'Do not invent Shakespeare-specific senses. State when a gloss is uncertain.',
      `Cite as: ${citation}`,
    ].join('\n')
  }

  const blocks = lookupResult.hits.map(({ entry }) => {
    const lines = [`▸ ${entry.headword}`]
    if (entry.forms) lines.push(`  (${entry.forms})`)
    lines.push(`  ${entry.text}`)
    return lines.join('\n')
  })

  return [
    'LEXICAL SOURCE (Onions, A Shakespeare Glossary, 1911/1919) — USE VERBATIM.',
    'Shakespeare-specific lexical commentary by C. T. Onions (OED co-editor).',
    'For Key Words & Glosses and Language and Rhetoric: prefer these entries over model memory.',
    'If a word is absent below, write: "not in Onions glossary" rather than inventing a sense.',
    `Cite as: ${citation}`,
    '',
    ...blocks,
  ].join('\n')
}

/** Compact payload for frontend display */
function formatOnionsForUI(lookupResult) {
  return {
    citation: lookupResult.source.citation,
    hits: lookupResult.hits.map(({ query, entry }) => ({
      query,
      headword: entry.headword,
      text: entry.text,
    })),
    misses: lookupResult.misses,
  }
}

module.exports = {
  loadGlossaryIndex,
  extractLookupCandidates,
  lookupForText,
  formatOnionsBlock,
  formatOnionsForUI,
}
