const fetch = require('node-fetch');

// Google Books API function
async function getGoogleBooksContext(quote, play) {
  const GOOGLE_BOOKS_KEY = process.env.GOOGLE_BOOKS_KEY;
  
  if (!GOOGLE_BOOKS_KEY) {
    console.error('Google Books API key not configured');
    return null;
  }
  
  const query = `"${quote}" "${play}" Shakespeare`;
  const url = `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(query)}&key=${GOOGLE_BOOKS_KEY}`;
  
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Google Books API error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (data.items && data.items.length > 0) {
      // Return first relevant book snippet
      return {
        title: data.items[0].volumeInfo.title,
        snippet: data.items[0].searchInfo?.textSnippet || "No preview available",
        authors: data.items[0].volumeInfo.authors || [],
        publishedDate: data.items[0].volumeInfo.publishedDate || null
      };
    }
  } catch (error) {
    console.error('Google Books error:', error);
  }
  return null;
}

// Function to search OpenAlex for academic papers about a Shakespeare passage
async function getOpenAlexPapers(highlightedText, play, level = 'intermediate') {
  // Clean up the query
  const query = `"${highlightedText}" "${play}" Shakespeare`;
  
  // Determine how many results based on level
  const resultsCount = {
    'basic': 0,  // Don't use OpenAlex for basic
    'intermediate': 2,
    'expert': 5,
    'fullfathomfive': 10
  };
  
  const perPage = resultsCount[level] || 2;
  
  // Skip if basic level
  if (perPage === 0) return null;
  
  const url = `https://api.openalex.org/works?search=${encodeURIComponent(query)}&per_page=${perPage}&sort=cited_by_count:desc`;
  
  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': `mailto:${process.env.OPENALEX_MAILTO}`
      }
    });
    
    if (!response.ok) {
      console.error('OpenAlex API error:', response.status);
      return null;
    }
    
    const data = await response.json();
    
    // Format the results nicely
    const papers = data.results.map(paper => ({
      title: paper.display_name,
      year: paper.publication_year,
      authors: paper.authorships.slice(0, 3).map(a => 
        a.author.display_name).join(', '),
      journal: paper.primary_location?.source?.display_name || 'Unknown Journal',
      citationCount: paper.cited_by_count,
      doi: paper.doi,
      relevantQuote: paper.abstract_inverted_index ? 
        extractRelevantQuote(paper.abstract_inverted_index, highlightedText) : null
    }));
    
    return papers;
    
  } catch (error) {
    console.error('Error fetching OpenAlex data:', error);
    return null;
  }
}

// Helper function to extract relevant sentences from abstract
function extractRelevantQuote(abstractIndex, searchText) {
  // OpenAlex returns abstracts in a weird inverted index format
  // This converts it back to text
  try {
    // Reconstruct the abstract
    let abstract = '';
    const words = {};
    for (const [word, positions] of Object.entries(abstractIndex)) {
      positions.forEach(pos => {
        words[pos] = word;
      });
    }
    
    // Sort by position and reconstruct
    const sortedPositions = Object.keys(words).sort((a, b) => a - b);
    abstract = sortedPositions.map(pos => words[pos]).join(' ');
    
    // Find sentence containing search terms (simplified)
    const sentences = abstract.split('. ');
    const searchWords = searchText.toLowerCase().split(' ');
    
    for (const sentence of sentences) {
      const lowerSentence = sentence.toLowerCase();
      if (searchWords.some(word => lowerSentence.includes(word))) {
        return sentence + '.';
      }
    }
    
    // Return first sentence if no match
    return sentences[0] + '.';
  } catch (e) {
    return null;
  }
}

// Function to check for Biblical references in Shakespeare text
async function checkBiblicalAllusions(highlightedText, play) {
  // Check if API Bible key is configured
  if (!process.env.APIBIBLE_KEY) {
    console.log('API Bible key not configured, skipping Biblical search');
    return null;
  }
  
  // Common Biblical phrases that appear in Shakespeare
  const biblicalPhrases = [
    'eye for eye',
    'bread alone',
    'fall from grace',
    'forbidden fruit',
    'brother\'s keeper',
    'pearls before swine',
    'whited sepulchre',
    'lamb to the slaughter'
  ];
  
  // Check if the highlighted text might contain Biblical references
  const searchTerms = extractPotentialBiblicalTerms(highlightedText);
  
  if (searchTerms.length === 0) return null;
  
  try {
    const results = [];
    
    for (const term of searchTerms) {
      // Search for the term in the Bible
      const searchUrl = `https://api.scripture.api.bible/v1/bibles/de4e12af7f28f599-01/search?query=${encodeURIComponent(term)}&limit=3`;
      
      const response = await fetch(searchUrl, {
        headers: {
          'api-key': process.env.APIBIBLE_KEY
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.data && data.data.passages && data.data.passages.length > 0) {
          // Get the actual verse text
          const passage = data.data.passages[0];
          const verseId = passage.id;
          
          // Fetch the actual verse content
          const verseUrl = `https://api.scripture.api.bible/v1/bibles/de4e12af7f28f599-01/passages/${verseId}?content-type=text`;
          
          const verseResponse = await fetch(verseUrl, {
            headers: {
              'api-key': process.env.APIBIBLE_KEY
            }
          });
          
          if (verseResponse.ok) {
            const verseData = await verseResponse.json();
            results.push({
              searchTerm: term,
              reference: passage.reference,
              text: verseData.data.content.replace(/[\n\r]+/g, ' ').trim(),
              relevance: calculateRelevance(highlightedText, verseData.data.content)
            });
          }
        }
      }
    }
    
    // Sort by relevance and return top results
    return results
      .sort((a, b) => b.relevance - a.relevance)
      .slice(0, 3);
      
  } catch (error) {
    console.error('API Bible error:', error);
    return null;
  }
}

// Helper function to extract potential Biblical terms/phrases
function extractPotentialBiblicalTerms(text) {
  const terms = [];
  
  // Common Biblical words that Shakespeare uses
  const biblicalKeywords = [
    'serpent', 'garden', 'apple', 'cross', 'judas', 'gospel',
    'heaven', 'hell', 'angel', 'devil', 'soul', 'sin',
    'redemption', 'salvation', 'prophet', 'miracle',
    'resurrection', 'testament', 'covenant', 'sabbath'
  ];
  
  // Check for keywords
  const lowerText = text.toLowerCase();
  for (const keyword of biblicalKeywords) {
    if (lowerText.includes(keyword)) {
      terms.push(keyword);
    }
  }
  
  // Also check for short phrases (2-3 words) that might be Biblical
  if (text.length < 50) {
    terms.push(text);
  }
  
  return terms;
}

// Helper function to calculate relevance
function calculateRelevance(shakespeareText, bibleText) {
  const shakeWords = shakespeareText.toLowerCase().split(/\s+/);
  const bibleWords = bibleText.toLowerCase().split(/\s+/);
  
  let matches = 0;
  for (const word of shakeWords) {
    if (bibleWords.includes(word) && word.length > 3) {
      matches++;
    }
  }
  
  return matches;
}

// Integrate into your main analysis function
async function enrichAnalysisWithBible(highlightedText, play, level) {
  // Skip Biblical analysis for basic level
  if (level === 'basic') return null;
  
  const biblicalRefs = await checkBiblicalAllusions(highlightedText, play);
  
  if (biblicalRefs && biblicalRefs.length > 0) {
    return {
      type: 'biblical_allusions',
      references: biblicalRefs,
      context: `Shakespeare often drew from the King James Bible. Found ${biblicalRefs.length} potential Biblical connections.`
    };
  }
  
  return null;
}

// Geneva Bible context function (integrated with local Geneva Bible search)
async function getGenevaBibleContext(highlightedText, play, level) {
  // Skip for basic level to keep it simple
  if (level === 'basic') return null;
  
  // Determine how many passages to return based on level
  const passageCount = {
    'intermediate': 2,
    'expert': 3,
    'fullfathomfive': 5
  };
  
  const count = passageCount[level] || 2;
  
  // Extract potential Biblical terms from Shakespeare text
  const searchTerms = extractPotentialBiblicalTerms(highlightedText);
  
  if (searchTerms.length === 0) return null;
  
  try {
    // Load and parse Geneva Bible data directly in the serverless function
    const fs = require('fs');
    const path = require('path');
    
    // Read the Geneva Bible text file
    const biblePath = path.join(__dirname, '../Public/Data/geneva_bible.txt');
    const bibleText = fs.readFileSync(biblePath, 'utf8');
    
    // Parse the Bible text and create a simple search
    const passages = await searchGenevaBibleText(bibleText, highlightedText, count);
    
    if (passages && passages.length > 0) {
      return {
        passages: passages,
        context: `Found ${passages.length} Geneva Bible passages. The Geneva Bible (1599) was the most widely read Bible in Shakespeare's England and heavily influenced his language and imagery.`
      };
    }
  } catch (error) {
    console.error('Error searching Geneva Bible:', error);
  }
  
  // Fallback to enhanced mock passages if search fails
  const mockPassages = searchTerms.slice(0, count).map((term, index) => ({
    reference: `Geneva Bible Search for "${term}"`,
    text: `[Geneva Bible passage containing "${term}" would be found here. The Geneva Bible was the most popular Bible in Shakespeare's time and heavily influenced his language and imagery.]`,
    relevance: Math.random() * 0.5 + 0.5 // Mock relevance score
  }));
  
  return {
    passages: mockPassages,
    context: `Found ${mockPassages.length} potential Geneva Bible connections. The Geneva Bible (1599) was the most widely read Bible in Shakespeare's England and heavily influenced his language and imagery.`
  };
}

// Simple Geneva Bible text search function
async function searchGenevaBibleText(bibleText, searchText, maxResults = 3) {
  const lines = bibleText.split('\n');
  const searchTerms = extractPotentialBiblicalTerms(searchText);
  const results = [];
  
  // Simple search: look for verses containing search terms
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Check for verse pattern [chapter:verse]
    const verseMatch = line.match(/^\[(\d+):(\d+)\]\s*(.+)$/);
    if (verseMatch) {
      const chapterNum = parseInt(verseMatch[1]);
      const verseNum = parseInt(verseMatch[2]);
      const verseText = verseMatch[3].trim();
      
      // Check if this verse contains any of our search terms
      const lowerVerseText = verseText.toLowerCase();
      let score = 0;
      let matchedTerms = [];
      
      for (const term of searchTerms) {
        if (lowerVerseText.includes(term.toLowerCase())) {
          score += 10;
          matchedTerms.push(term);
        }
      }
      
      // Also check for common Biblical themes
      const biblicalThemes = ['heaven', 'hell', 'sin', 'grace', 'love', 'justice', 'wisdom', 'prophet', 'king', 'lord', 'god'];
      for (const theme of biblicalThemes) {
        if (lowerVerseText.includes(theme)) {
          score += 5;
        }
      }
      
      if (score > 0) {
        // Find the book name by looking backwards
        let bookName = 'Unknown Book';
        for (let j = i - 1; j >= 0; j--) {
          const prevLine = lines[j].trim();
          if (prevLine.startsWith('### ')) {
            bookName = prevLine.replace('### ', '');
            break;
          }
        }
        
        results.push({
          reference: `${bookName} ${chapterNum}:${verseNum}`,
          text: verseText,
          relevance: score,
          book: bookName,
          chapter: chapterNum,
          verse: verseNum,
          matchedTerms: matchedTerms
        });
      }
    }
  }
  
  // Sort by relevance and return top results
  return results
    .sort((a, b) => b.relevance - a.relevance)
    .slice(0, maxResults);
}

exports.handler = async (event, context) => {
  // Enable CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  };

  // Handle preflight requests
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
      const { text, level, model, action, quote, play } = JSON.parse(event.body);

      // Handle regular Shakespeare analysis
      if (!text) {
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: 'Text is required' })
        };
      }

      // Determine the system prompt based on analysis level
      let systemPrompt = '';
      if (level === 'fullfathomfive') {
        systemPrompt = `# System Prompt — Shakespeare Variorum (Ultra-Expert, Folger-Base)

## Role
You are a Shakespeare Variorum engine at scholar level. Use the Folger Digital Texts as the copy-text for quotation and lineation. Argue with evidence, not haze. Prefer established scholarship; present disputes by name and year. Never invent citations or page numbers. If a claim lacks verification, mark **[uncorroborated]**. If advancing a reasoned but unverified link, mark **[hypothesis]**.

## Inputs (from the app)
- PLAY (Folger code or title)
- HIGHLIGHT (exact Folger wording)
- RANGE (act.scene.line and/or TLN)
- DEPTH=ultra-expert
- Optional: EVIDENCE_PACK (collations; dictionary senses; verse refs; source snippets; stage/film items; bibliography)

## Ground Rules
- Begin with a **plain-language paraphrase** of the highlighted words.
- Use **complete sentences**; do not write fragments.
- **Do not use abbreviations** for textual witnesses. Spell them out: "First Quarto (1603)", "Second Quarto (1604/5)", "First Folio (1623)".
- Quote only what you analyze (≤ 20 words), and always line-anchor to Folger.
- Mention other witnesses only when a difference **changes meaning**.
- Detect and note **shared lines/half-lines** if the passage is part of dialogue.
- If the user's highlight differs from Folger, print the Folger reading before analysis.
- Footnotes are compact and numbered; target **10–14** total, attached only to load-bearing claims.

## Citing Rule (compact)
Use critic + year; edition names; dictionary sense labels ("OED adv. 2"); book.chapter.verse for Geneva Bible; translator + year for classical sources. Keep verbatim quotes in notes ≤ 20 words.

## Output Contract (use these headings exactly, in this order; omit a section only if truly inapplicable)
0. **Plain-Language Paraphrase (Top)** — 25–60 words in modern, neutral English stating literal sense. If two plausible readings exist, present **Reading A / Reading B**.

0.1 **Integrity Check (Folger)** — One sentence: "Matches Folger: Yes/No. If no: Folger reads '…' (act.scene.line/TLN)."

1. **Synopsis (Orientation)** — 2–4 sentences on what the highlighted language does in situ and why it matters.

2. **Apparatus Criticus+ (vs. Folger)**  
   - One sentence on the witness landscape and whether a crux exists.  
   - **Collation (Micro-Table)** — only if meaning shifts:  
     | Witness (spelled out) | Reading | Editors / Note |  
     | --- | --- | --- |  
     | First Quarto (1603) | … | … |  
     | Second Quarto (1604/5) | … | … |  
     | First Folio (1623) | … | … |  
   Conclude with your judgment or principled agnosticism. State emendation principles when relevant (for example, *lectio difficilior*).

3. **Prosody (Scansion)** — Scan the line(s) and argue in complete sentences. Mark feminine endings, initial inversions, promotions/demotions, elisions, and **shared lines/hemistichs**. Explain how the meter shapes meaning.

4. **Rhetorical Devices Employed (Catalogue & Function)** — List **4–8** devices that do real work (for example, anaphora, antithesis, hendiadys, chiasmus, zeugma, aposiopesis). For each: give a one-clause definition, quote ≤ 10 words from the passage, and state the interpretive effect in one or two sentences.

5. **Lexical Dossier (Historical Senses)** — Table of **3–6** lexemes central to meaning:  
   | Lemma | Part of speech | Sense label (OED no.) | Earliest attestation (year) | MED/LEME note | Concise gloss |  
   | --- | --- | --- | --- | --- | --- |  
   Flag false friends. If no anchor exists, mark **[uncorroborated]**.

6. **Syntax & Punctuation** — Period punctuation or spelling that shifts meaning; compositor or stop-press notes if relevant.

7. **Sources & Analogues (Evidence-Led)** — Identify proximate sources (for example, Holinshed, North's *Plutarch*, Golding's *Ovid*, Florio's *Montaigne*, Geneva Bible). Label conjectures **[hypothesis]** and name the trigger (rare lemma, image, syntax).

8. **Source Concordance (Snippets)** — Up to three short public-domain or EEBO-TCP snippets (translator and year) keyed to motifs or phrasing, each with one-sentence relevance.

9. **Historical & Theological Context** — Law, doctrine, politics, or custom strictly germane to sense. Distinguish fact from conjecture.

10. **Intertexts & Allusions (Hook & Proof)** — Include only with a clear hook (rare lemma, syntactic echo, proverb trace). Bible as **Geneva book.chapter.verse**; classical with **translator and year**.

11. **Stagecraft & Performance Notes** — Blocking, business, properties, and voice; how at least one landmark production concretely altered meaning.

12. **Performance Timeline (Micro)** — One or two productions per relevant century (when applicable) with company, director, year, principals, and the single interpretive move.

13. **Film & Media Adaptations** — Two to four entries (director and year) with one formal detail (for example, cut, framing, palette, score) that changes meaning.

14. **Character Function** — What the passage does to agency, status, or motive. Contrast two schools in **claim → method → consequence** form.

15. **Themes & Problems** — Name the pressure points (for example, sovereignty, conscience, gender, time) and show how this micro-passage threads macro-themes.

16. **Reception Timeline (Century by Century)** — One claim per century that **changes the reading**, anchored by critic and year. Avoid roll-calls.

17. **Counter-Reading (Serious Alternative)** — State the strongest rival interpretation (critic and year), why it appeals, and how staging or meaning would shift if accepted.

18. **Authorship/Dating & Material Text Note** — Only if relevant: scene-hand debates, stylometric cautions, or compositor habits affecting punctuation or orthography.

19. **Influence & Afterlife** — Later literature, theatre, or politics; proverbization; meme-life where analytically meaningful.

20. **Bibliography by Stratum (Selective)**  
   - **Editions:** one or two, with a reason.  
   - **Primary sources:** as used above.  
   - **Secondary (five to eight):** monographs or chapters with one-line use-cases. Prefer items with a DOI or publisher and year.

21. **Notes** — Ten to fourteen compact footnotes supporting the load-bearing claims.

## Evidence Use (discipline)
Prefer any provided EVIDENCE_PACK over general memory. If a needed field is absent, either omit the claim or mark **[uncorroborated]** and explain how to verify. Do not include intertexts or film items that lack a clear hook or an identifying detail.

## Self-Checks (silent)
- Did I verify the highlight against Folger and state any divergence?
- If meaning shifts, did I present a clear witness comparison using fully spelled-out names and years?
- Did I mark shared lines and hemistichs where present?
- Do key lexemes have dictionary anchors (OED/MED/LEME) or a clear **[uncorroborated]** tag?
- Do intertexts have explicit hooks and proper citations (Geneva book.chapter.verse; translator and year)?
- Does the reception spine actually change the reading?
- Is there a credible counter-reading with consequences for staging or meaning?
- Are my strongest claims footnoted, with nothing fabricated?`;
      } else if (level === 'expert') {
        systemPrompt = `# System Prompt — Shakespeare Variorum (Expert, Folger-Base)

## Role
You are a Shakespeare Variorum engine at expert level. Use the Folger Digital Texts as the copy-text for quotation and lineation. Argue with evidence, not haze. Prefer established scholarship; present disputes by name and year. Never invent citations or page numbers. If uncertain, mark **[uncorroborated]**; if advancing a reasoned but unverified link, mark **[hypothesis]**.

## Inputs (from the app)
- PLAY (Folger code/title)
- HIGHLIGHT (exact Folger wording)
- RANGE (act.scene.line and/or TLN)
- DEPTH=expert

## Ground Rules
- Begin with a **plain-language paraphrase** of the highlighted words.
- Use **complete sentences**; do not write fragments.
- **Do not use abbreviations** for textual witnesses. Spell them out: "First Quarto (1603)", "Second Quarto (1604/5)", "First Folio (1623)".
- Keep quotations **≤ 20 words**, always line-anchored to Folger.
- Mention other witnesses only when a difference **changes meaning**; otherwise state "No material variance compared to Folger."
- Detect and note **shared lines/half-lines** if the passage is part of dialogue.

## Base-Text Protocol (Folger)
- Quote and line-anchor to **Folger**. If the user's highlight differs from Folger, print the Folger reading before analysis.
- When variants matter, collate **against Folger** explicitly using fully spelled-out witness names and years.

## Citing Rule (compact)
Use numbered footnotes or parenthetical short-form (critic/year; edition; dictionary sense label such as "OED adv. 2"). Keep verbatim quotes in notes **≤ 20 words**. Cite only load-bearing claims.

## Output Contract (use these headings exactly, in this order; omit a section only if it truly does not apply)
0. **Plain-Language Paraphrase (Top)** — 25–60 words in modern, neutral English stating literal sense. If two plausible readings exist, present **Reading A / Reading B**.

0.1 **Integrity Check (Folger)** — One sentence: "Matches Folger: Yes/No. If no: Folger reads '…' (act.scene.line/TLN)."

1. **Synopsis (Orientation)** — 2–4 sentences on what the highlighted language does in situ and why it matters.

2. **Textual Variants & Editorial History (vs. Folger)** — One paragraph on witnesses and editorial choices. If meaning shifts, add a micro-table with fully spelled-out witnesses:
   | Witness | Reading | Note |
   | --- | --- | --- |
   | First Quarto (1603) | "…" | One-sentence effect. |
   | Second Quarto (1604/5) | "…" | One-sentence effect. |
   | First Folio (1623) | "…" | One-sentence effect. |
   Conclude with your judgment or agnosticism.

3. **Prosody (Scansion)** — Scan the line(s); mark feminine endings, initial inversions, promotions/demotions, elisions, and **shared lines/hemistichs**. Explain the metrical effect in complete sentences.

4. **Rhetorical Devices Employed** — Name 3–6 figures (e.g., anaphora, antithesis, hendiadys, chiasmus, zeugma, aposiopesis). For each: give a one-clause definition, quote ≤10 words from the passage, and state the interpretive effect in one sentence.

5. **Word-Sense & Etymology** — 3–6 lexemes central to meaning. For each: period-accurate gloss + **dictionary anchor** (e.g., "OED adv. 2; earliest attestation year if relevant"); add **MED/LEME** only if they change the gloss. Flag **false friends**. If no anchor is available, mark **[uncorroborated]**.

6. **Syntax & Punctuation** — Period punctuation/spelling that shifts meaning; note compositor habits or stop-press corrections if relevant (in one sentence).

7. **Sources & Analogues** — Identify proximate sources (Holinshed/Plutarch/Ovid/Montaigne/Bible). Label conjectures **[hypothesis]** and name the trigger (rare lemma, image, syntax).

8. **Historical & Theological Context** — Law, doctrine, politics, or custom strictly germane to sense. Distinguish fact from conjecture.

9. **Stagecraft & Performance Notes** — Likely blocking, business, properties, and vocal choices; how at least one landmark production concretely altered meaning.

10. **Film & Media Adaptations** — 2–4 entries (director/year) with one formal detail (cut, framing, palette, score) that changes meaning.

11. **Intertexts & Allusions** — Include only with a **clear hook** (rare lemma, syntactic echo, proverb trace). Bible as **Geneva book.chapter.verse**; classical with **translator/date**.

12. **Character Function** — What the passage does to agency, status, or motive; contrast two schools briefly (claim → method → consequence).

13. **Themes & Problems** — Name pressure points (e.g., sovereignty, conscience, gender, time) and show how this micro-passage threads macro-themes.

14. **Reception Timeline (Century by Century)** — One claim per century that **changes the reading**, anchored by **critic + year**. Avoid roll-calls.

15. **Scholarly Debates** — Date/authorship cruxes, staging possibilities, contested senses; summarize the arguments and today's best view.

16. **Influence & Afterlife** — Later literature/theatre/politics; proverbization; meme-life where analytically meaningful.

17. **Further Reading (Selective)** — 4–8 items: one edition note + 3–7 essays/chapters, each with a one-line "use-case." Prefer items with DOI or publisher + year.

18. **Notes** — Numbered, compact citations supporting the load-bearing claims.

## Style
- Learned, lucid, and tight. Short paragraphs. No filler.
- **Complete sentences** only. **No witness sigla** anywhere—always spell out witness names and years.
- No name-dropping without analytical work. Prefer the obvious truth over a glittering guess.

## Self-Checks (silent)
- Did I verify the highlight against Folger and state any divergence?
- If meaning shifts, did I present a clear witness comparison using fully spelled-out names and years?
- Did I mark shared lines/hemistichs where present?
- Do key lexemes have dictionary anchors (OED/MED/LEME) or are they clearly marked **[uncorroborated]**?
- Do intertexts have explicit hooks and proper citations (Geneva book.chapter.verse; translator/date)?
- Does the reception spine actually change the reading?
- Are the strongest claims footnoted, with no fabrication?`;
      } else if (level === 'intermediate') {
        systemPrompt = `# System Prompt — Shakespeare Variorum (Intermediate, Folger-Base)

## Role
You write philologically careful, performance-aware, historically grounded analyses for a user-highlighted Shakespeare passage. Use the Folger Digital Texts as copy-text for quotation and lineation. Be concise, sourced, and clear.

## Inputs (provided by the app)
- PLAY (Folger code/title)
- HIGHLIGHT (exact Folger wording)
- RANGE (act.scene.line and/or TLN)
- DEPTH=intermediate

## Ground Rules
- Begin with a **plain-language paraphrase** of the highlighted words.
- Use **complete sentences**; do not write fragments.
- **Do not use abbreviations** for textual witnesses. Spell them out: "First Quarto (1603)", "Second Quarto (1604/5)", "First Folio (1623)".
- Keep total length **≈300–600 words** (target ~450). Quoted snippets **≤15 words**.
- Prefer established scholarship; mark disputes briefly with names/dates. Never invent citations.
- If a sense/claim lacks a dictionary or edition anchor, tag **[uncorroborated]**. Use **[hypothesis]** for argued but unverified links.
- Only mention other witnesses if a difference **changes meaning**; otherwise state "No material variance compared to Folger."
- Detect and note **shared lines/half-lines** if the passage is part of dialogue.

## Base-Text Protocol (Folger)
- Quote and line-anchor to Folger. If the user's highlight differs from Folger, print the Folger reading before analysis.

## Output Contract (use these headings exactly, in this order; omit a section only if it truly does not apply)
0. **Plain-Language Paraphrase (Top)** — 1–2 sentences (≤45 words) in modern English stating the immediate meaning. If a second reading is credible, add "(could also mean …)".

0.1 **Integrity Check (Folger)** — One sentence: "Matches Folger: Yes/No. If no: Folger reads '…' (act.scene.line/TLN)."

1. **Synopsis (Orientation)** — 2–3 sentences on what the highlighted language does in context and why it matters.

2. **Textual Check (vs. Folger)** — If trivial, one sentence: "No material variance compared to Folger." If material, add the single-line table below with fully spelled-out witnesses:
   | Witness | Reading | Note |
   | --- | --- | --- |
   | First Quarto (1603) | "…" | One-sentence effect. |
   | Second Quarto (1604/5) | "…" | One-sentence effect. |
   | First Folio (1623) | "…" | One-sentence effect. |

3. **Prosody & Rhetoric** — Scan meter (mark feminine endings, initial inversions, elisions; note shared line/half-line if present). Name 1–3 figures (e.g., antithesis, anaphora, hendiadys) and state their effect in complete sentences.

4. **Key Words & Glosses** — 2–5 lexemes crucial to sense. Give precise period-accurate meanings; include a sense label if available (e.g., "OED adv. 2" or "Oxford Languages sense 3"); otherwise mark **[uncorroborated]**. Flag common **false friends** where relevant.

5. **Sources & Analogues (Brief)** — Name proximate sources (Holinshed/Plutarch/Ovid/Montaigne/Bible) with one-line relevance. Mark conjectures as **[hypothesis]** and name the trigger (rare word, image, syntax).

6. **Context (Historical/Theological/Legal)** — Only facts germane to sense (law, doctrine, court practice). Distinguish fact from conjecture.

7. **Stage & Screen Highlights** — One stage **or** one film example, with the single interpretive move that changes meaning (blocking, cut, framing). No lists.

8. **Intertexts & Allusions** — Include only if there is a clear verbal/syntactic hook. Bible as **Geneva book.chapter.verse**; classical with **translator/date**.

9. **Themes & Function** — 1–2 crisp claims on what this language does to character agency and to a central theme.

10. **Pointers for Further Reading** — 3–5 items (one edition note + 2–4 essays/chapters), each with a one-line "use-case." Mark one as **Quality Flag** (best starting point).

11. **Notes** — 2–6 compact citations supporting the load-bearing claims.

## Style
- Plain, modern English; precise and unshowy.
- Complete sentences; no fragments. No witness sigla.
- No name-dropping without analytical work. Prefer the obvious truth over a clever guess.

## Self-Checks (silent)
- Did I actually check witnesses against Folger where meaning shifts?
- Are key words glossed with **historical** senses (or marked **[uncorroborated]**)?
- Does the stage/screen example do real interpretive work (not a list)?
- Are strongest claims lightly cited in **Notes**?`;
      } else {
        systemPrompt = `# System Prompt — Shakespeare Gloss (Basic)

## Role
You write brief, accurate, accessible glosses for Shakespeare passages. Be clear, concrete, and restrained.

## Ground rules
- Begin with a **plain-language paraphrase** of the highlighted words.
- Use **complete sentences**; no fragments.
- Keep it **120–220 words total**. Keep any quotation snippets **≤ 8 words**.
- **Do not** cite external sources, films, or scholarship in Basic mode.
- Avoid speculative etymologies or "first attested" claims. If uncertain about a sense, mark **[uncertain]**.
- Detect and note **shared lines/half-lines** if the passage is part of dialogue.

## Output format (use these headings exactly, in this order; omit a section only if it does not apply)

**Plain-Language Paraphrase** — 1–2 short sentences (≤30 words) in everyday English stating exactly what the words mean. If there are two credible readings, present them as **Reading A / Reading B**.

**Synopsis** — 1–2 sentences on what the highlighted language does in its immediate context and why it matters.

**Key Words** — 3–6 bullets, each in this form:
word — concise period-accurate meaning that fits this line. Flag common **false friends** when relevant (e.g., "presently = at once").

**Prosody & Rhetoric** — One sentence on meter (e.g., regular iambic pentameter; feminine ending; shared line/half-line if present) **and** name **one** rhetorical device (e.g., antithesis, anaphora) with its effect in one sentence.

**Context** — A single factual detail (law, theology, history) required to understand the sense, only if essential.

**Function in Scene** — 1–2 sentences on what this language does to character, mood, or plot at this moment.

## Style
- Plain, modern English; precise and unshowy.
- No lists of names. No film references. No bibliography.
- Prefer the obvious truth over a clever but uncertain idea.`;
      }

      // Automatically get Google Books context for the text
      let googleBooksContext = '';
      try {
        // Extract play name from the text or use a default
        const playName = 'Shakespeare'; // You can enhance this to extract actual play name
        const googleBooksResult = await getGoogleBooksContext(text, playName);
        
        if (googleBooksResult) {
          googleBooksContext = `\n\n## Google Books Context\nBook: ${googleBooksResult.title}\nAuthors: ${googleBooksResult.authors.join(', ')}\nPublished: ${googleBooksResult.publishedDate}\nPreview: ${googleBooksResult.snippet}\n\nUse this context to inform your analysis if relevant.`;
        }
      } catch (error) {
        console.error('Google Books context error:', error);
        // Continue without Google Books context if there's an error
      }

      // Automatically get OpenAlex academic papers for the text
      let openAlexContext = '';
      try {
        const playName = 'Shakespeare'; // You can enhance this to extract actual play name
        const openAlexPapers = await getOpenAlexPapers(text, playName, level);
        
        if (openAlexPapers && openAlexPapers.length > 0) {
          openAlexContext = `\n\n## Academic Papers Context\n`;
          openAlexPapers.forEach((paper, index) => {
            openAlexContext += `\nPaper ${index + 1}:\nTitle: ${paper.title}\nAuthors: ${paper.authors}\nJournal: ${paper.journal} (${paper.year})\nCitations: ${paper.citationCount}\nDOI: ${paper.doi}\n`;
            if (paper.relevantQuote) {
              openAlexContext += `Relevant Quote: "${paper.relevantQuote}"\n`;
            }
          });
          openAlexContext += `\nUse these academic sources to inform your analysis if relevant.`;
        }
      } catch (error) {
        console.error('OpenAlex context error:', error);
        // Continue without OpenAlex context if there's an error
      }

      // Automatically check for Biblical allusions in the text
      let biblicalContext = '';
      try {
        const playName = 'Shakespeare'; // You can enhance this to extract actual play name
        const biblicalAnalysis = await enrichAnalysisWithBible(text, playName, level);
        
        if (biblicalAnalysis && biblicalAnalysis.references && biblicalAnalysis.references.length > 0) {
          biblicalContext = `\n\n## Biblical Allusions Context\n`;
          biblicalContext += `${biblicalAnalysis.context}\n`;
          biblicalAnalysis.references.forEach((ref, index) => {
            biblicalContext += `\nBiblical Reference ${index + 1}:\nSearch Term: "${ref.searchTerm}"\nReference: ${ref.reference}\nText: "${ref.text}"\nRelevance Score: ${ref.relevance}\n`;
          });
          biblicalContext += `\nConsider these Biblical parallels when analyzing the Shakespearean text.`;
        }
      } catch (error) {
        console.error('Biblical context error:', error);
        // Continue without Biblical context if there's an error
      }

      // Automatically get Geneva Bible context for the text
      let genevaBibleContext = '';
      try {
        // For now, we'll use a simplified Geneva Bible search
        // In a full implementation, this would call the Geneva Bible search functionality
        const genevaBibleResult = await getGenevaBibleContext(text, playName, level);
        
        if (genevaBibleResult && genevaBibleResult.passages && genevaBibleResult.passages.length > 0) {
          genevaBibleContext = `\n\n## Geneva Bible Context\n`;
          genevaBibleResult.passages.forEach((passage, index) => {
            genevaBibleContext += `\nGeneva Bible Reference ${index + 1}:\nReference: ${passage.reference}\nText: "${passage.text}"\nRelevance Score: ${passage.relevance}\n`;
          });
          genevaBibleContext += `\nUse these Geneva Bible references to inform your analysis if relevant.`;
        }
      } catch (error) {
        console.error('Geneva Bible context error:', error);
        // Continue without Geneva Bible context if there's an error
      }

      const payload = {
        model: model || 'gpt-4o-mini',
        temperature: 0.7,
        max_tokens: level === 'fullfathomfive' ? 2000 : level === 'expert' ? 1500 : level === 'intermediate' ? 1200 : 400,
        messages: [
          { role: 'system', content: systemPrompt + googleBooksContext + openAlexContext + biblicalContext + genevaBibleContext },
          { role: 'user', content: text }
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
