const { loadJsonIndex, normalizeText, extractPhrases } = require('./lexical-utils')

let indexCache = null
const CITATION = 'The Geneva Bible (1599). Public-domain text via eBible.org (enggnv).'

function loadIndex() {
  if (!indexCache) {
    const { meta, entries } = loadJsonIndex('geneva_bible_index.json')
    const verses = entries.verses || []
    indexCache = {
      meta,
      verses: verses.map(v => ({
        ...v,
        normalized: normalizeText(v.text),
      })),
    }
  }
  return indexCache
}

function lookupForText(text, { maxHits = 5 } = {}) {
  const { verses } = loadIndex()
  const phrases = extractPhrases(text, { minWords: 3, maxWords: 5, maxPhrases: 10 })
  const hits = []
  const seen = new Set()

  for (const phrase of phrases) {
    if (phrase.length < 8) continue
    for (const verse of verses) {
      if (!verse.normalized.includes(phrase)) continue
      const key = verse.ref
      if (seen.has(key)) continue
      seen.add(key)
      hits.push({
        matchedPhrase: phrase,
        ref: verse.ref,
        text: verse.text,
        score: phrase.length,
      })
      if (hits.length >= maxHits) break
    }
    if (hits.length >= maxHits) break
  }

  hits.sort((a, b) => b.score - a.score)

  return {
    source: { citation: CITATION, title: 'Geneva Bible', edition: '1599' },
    hits,
    hitCount: hits.length,
  }
}

function formatGenevaBlock(lookupResult) {
  if (!lookupResult.hits.length) {
    return [
      'BIBLICAL SOURCE (Geneva Bible, 1599):',
      'No strong phrase-level parallels found in the Geneva Bible index for this passage.',
      'Do not invent biblical quotations. Note possible allusions only with caution.',
      `Cite as: ${CITATION}`,
    ].join('\n')
  }

  const blocks = lookupResult.hits.map(hit => {
    return [
      `▸ ${hit.ref} (matched: "${hit.matchedPhrase}")`,
      `  ${hit.text}`,
    ].join('\n')
  })

  return [
    'BIBLICAL SOURCE (Geneva Bible, 1599) — POSSIBLE PARALLELS ONLY.',
    'Present these as candidate echoes, not confirmed quotations, unless the match is exact.',
    'For the Sources section: cite Geneva wording verbatim when a parallel is relevant.',
    `Cite as: ${CITATION}`,
    '',
    ...blocks,
  ].join('\n')
}

function formatForUI(lookupResult) {
  return {
    citation: CITATION,
    hits: lookupResult.hits.map(hit => ({
      ref: hit.ref,
      matchedPhrase: hit.matchedPhrase,
      text: hit.text,
    })),
  }
}

module.exports = { lookupForText, formatGenevaBlock, formatForUI }
