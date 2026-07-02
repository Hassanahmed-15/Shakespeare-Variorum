const fs = require('fs')
const path = require('path')

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
  'nor', 'let', 'come', 'go', 'see', 'say', 'make', 'take', 'who', 'whom',
])

const LEMMA_OVERRIDES = {
  doth: 'do',
  dost: 'do',
  hath: 'have',
  hast: 'have',
  wherefore: 'wherefore',
  incarnardine: 'incarnadine',
  fadom: 'fathom',
  fadoiii: 'fathom',
  thou: 'thou',
  thee: 'thee',
  ye: 'ye',
}

function loadJsonIndex(filename) {
  const candidates = [
    path.join(__dirname, '../../data', filename),
    path.join(__dirname, '../data', filename),
    path.join(process.cwd(), 'data', filename),
  ]
  const filePath = candidates.find(p => fs.existsSync(p))
  if (!filePath) {
    throw new Error(`Index not found: ${filename}`)
  }
  const raw = JSON.parse(fs.readFileSync(filePath, 'utf8'))
  const { _meta, ...entries } = raw
  return { meta: _meta || {}, entries, filePath }
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

function normalizeText(text) {
  return text
    .toLowerCase()
    .replace(/[æ]/g, 'ae')
    .replace(/[œ]/g, 'oe')
    .replace(/['']/g, "'")
    .replace(/[^a-z0-9'\s-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
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

function extractPhrases(text, { minWords = 3, maxWords = 5, maxPhrases = 12 } = {}) {
  const words = normalizeText(text).split(/\s+/).filter(w => w.length > 2 && !STOPWORDS.has(w))
  const phrases = new Set()

  for (let size = maxWords; size >= minWords; size--) {
    for (let i = 0; i <= words.length - size; i++) {
      phrases.add(words.slice(i, i + size).join(' '))
      if (phrases.size >= maxPhrases) break
    }
    if (phrases.size >= maxPhrases) break
  }

  return [...phrases].sort((a, b) => b.length - a.length).slice(0, maxPhrases)
}

module.exports = {
  STOPWORDS,
  loadJsonIndex,
  normalizeToken,
  normalizeText,
  extractLookupCandidates,
  extractPhrases,
}
