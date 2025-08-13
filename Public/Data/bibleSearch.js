// Geneva Bible Search Functionality
// Loads and parses geneva_bible.txt file for Shakespeare analysis

class BibleSearch {
    constructor() {
        this.bibleData = null;
        this.searchIndex = null;
        this.isLoaded = false;
        this.archaicWords = new Set([
            'thee', 'thou', 'thy', 'thine', 'hath', 'hast', 'doth', 'dost', 'shalt', 'wilt',
            'art', 'beest', 'wast', 'wert', 'hath', 'hast', 'hadst', 'hath', 'hast',
            'doth', 'dost', 'didst', 'shalt', 'wilt', 'wouldst', 'couldst', 'shouldst',
            'mayst', 'mightst', 'canst', 'must', 'ought', 'methinks', 'forsooth',
            'verily', 'alas', 'lo', 'behold', 'nay', 'yea', 'ay', 'prithee', 'anon'
        ]);
    }

    // Load and parse the Geneva Bible text file
    async loadBibleData() {
        try {
            const response = await fetch('/Public/Data/geneva_bible.txt');
            if (!response.ok) {
                throw new Error(`Failed to load Geneva Bible data: ${response.status}`);
            }
            
            const text = await response.text();
            this.bibleData = this.parseBibleText(text);
            this.createSearchIndex();
            this.isLoaded = true;
            console.log('Geneva Bible data loaded successfully');
            return true;
        } catch (error) {
            console.error('Error loading Geneva Bible data:', error);
            return false;
        }
    }

    // Parse the Geneva Bible text file format
    parseBibleText(text) {
        const books = [];
        const lines = text.split('\n');
        let currentBook = null;
        let currentChapter = null;
        let currentVerses = [];

        for (let line of lines) {
            line = line.trim();
            if (!line) continue;

            // Check for verse reference pattern [chapter:verse]
            const verseMatch = line.match(/^\[(\d+):(\d+)\]\s*(.+)$/);
            if (verseMatch) {
                const chapterNum = parseInt(verseMatch[1]);
                const verseNum = parseInt(verseMatch[2]);
                const verseText = verseMatch[3].trim();

                // If we have a new chapter, save the previous one
                if (currentChapter && chapterNum !== currentChapter.number) {
                    if (currentVerses.length > 0) {
                        currentChapter.verses = currentVerses;
                        currentBook.chapters.push(currentChapter);
                        currentVerses = [];
                    }
                    currentChapter = {
                        number: chapterNum,
                        verses: []
                    };
                }

                // If we don't have a chapter yet, create one
                if (!currentChapter) {
                    currentChapter = {
                        number: chapterNum,
                        verses: []
                    };
                }

                // Add verse to current chapter
                currentVerses.push({
                    number: verseNum,
                    text: verseText
                });

                continue;
            }

            // Check for book name (usually appears before verses)
            // Look for common book patterns
            const bookPatterns = [
                /^Genesis/i, /^Exodus/i, /^Leviticus/i, /^Numbers/i, /^Deuteronomy/i,
                /^Joshua/i, /^Judges/i, /^Ruth/i, /^Samuel/i, /^Kings/i, /^Chronicles/i,
                /^Ezra/i, /^Nehemiah/i, /^Esther/i, /^Job/i, /^Psalms/i, /^Proverbs/i,
                /^Ecclesiastes/i, /^Song of Solomon/i, /^Isaiah/i, /^Jeremiah/i,
                /^Lamentations/i, /^Ezekiel/i, /^Daniel/i, /^Hosea/i, /^Joel/i,
                /^Amos/i, /^Obadiah/i, /^Jonah/i, /^Micah/i, /^Nahum/i, /^Habakkuk/i,
                /^Zephaniah/i, /^Haggai/i, /^Zechariah/i, /^Malachi/i,
                /^Matthew/i, /^Mark/i, /^Luke/i, /^John/i, /^Acts/i,
                /^Romans/i, /^Corinthians/i, /^Galatians/i, /^Ephesians/i,
                /^Philippians/i, /^Colossians/i, /^Thessalonians/i, /^Timothy/i,
                /^Titus/i, /^Philemon/i, /^Hebrews/i, /^James/i, /^Peter/i,
                /^John/i, /^Jude/i, /^Revelation/i
            ];

            for (let pattern of bookPatterns) {
                if (pattern.test(line)) {
                    // Save previous book if exists
                    if (currentBook && currentChapter) {
                        if (currentVerses.length > 0) {
                            currentChapter.verses = currentVerses;
                            currentBook.chapters.push(currentChapter);
                        }
                        books.push(currentBook);
                    }

                    // Start new book
                    currentBook = {
                        name: line.trim(),
                        chapters: []
                    };
                    currentChapter = null;
                    currentVerses = [];
                    break;
                }
            }
        }

        // Save the last book
        if (currentBook && currentChapter) {
            if (currentVerses.length > 0) {
                currentChapter.verses = currentVerses;
                currentBook.chapters.push(currentChapter);
            }
            books.push(currentBook);
        }

        console.log(`Parsed ${books.length} books from Geneva Bible`);
        return books;
    }

    // Create a searchable index of all verses
    createSearchIndex() {
        if (!this.bibleData) {
            console.error('No Bible data available to index');
            return;
        }

        this.searchIndex = [];
        
        this.bibleData.forEach(book => {
            book.chapters.forEach(chapter => {
                chapter.verses.forEach(verse => {
                    this.searchIndex.push({
                        book: book.name,
                        chapter: chapter.number,
                        verse: verse.number,
                        text: verse.text,
                        reference: `${book.name} ${chapter.number}:${verse.number}`,
                        keywords: this.extractKeywords(verse.text),
                        archaicKeywords: this.extractArchaicKeywords(verse.text)
                    });
                });
            });
        });

        console.log(`Created search index with ${this.searchIndex.length} verses`);
    }

    // Extract keywords from verse text
    extractKeywords(text) {
        if (!text) return [];
        
        // Convert to lowercase and remove punctuation
        const cleanText = text.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
        
        // Split into words and filter out common words
        const words = cleanText.split(' ');
        const commonWords = new Set([
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'a', 'an', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their', 'mine', 'yours', 'ours', 'theirs'
        ]);
        
        return words.filter(word => 
            word.length > 2 && !commonWords.has(word) && !this.archaicWords.has(word)
        );
    }

    // Extract archaic keywords for better matching with Shakespeare
    extractArchaicKeywords(text) {
        if (!text) return [];
        
        const cleanText = text.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
        
        const words = cleanText.split(' ');
        return words.filter(word => this.archaicWords.has(word));
    }

    // Search for Biblical passages that match Shakespeare text
    searchBiblePassages(shakespeareText, playName, maxResults = 3) {
        if (!this.isLoaded || !this.searchIndex) {
            console.error('Bible data not loaded');
            return [];
        }

        if (!shakespeareText || shakespeareText.trim().length === 0) {
            return [];
        }

        // Extract keywords from Shakespeare text
        const shakespeareKeywords = this.extractKeywords(shakespeareText);
        const shakespeareArchaic = this.extractArchaicKeywords(shakespeareText);
        
        // Score each verse based on keyword matches
        const scoredVerses = this.searchIndex.map(verse => {
            const score = this.calculateRelevanceScore(shakespeareKeywords, shakespeareArchaic, verse);
            return { ...verse, score };
        });

        // Sort by relevance score and return top results
        return scoredVerses
            .filter(verse => verse.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, maxResults)
            .map(verse => ({
                reference: verse.reference,
                text: verse.text,
                relevance: verse.score,
                book: verse.book,
                chapter: verse.chapter,
                verse: verse.verse
            }));
    }

    // Calculate relevance score between Shakespeare text and Bible verse
    calculateRelevanceScore(shakespeareKeywords, shakespeareArchaic, verse) {
        let score = 0;
        
        // Check for exact phrase matches
        const shakespeareLower = shakespeareKeywords.join(' ').toLowerCase();
        const verseLower = verse.text.toLowerCase();
        
        // Exact phrase match gets high score
        if (verseLower.includes(shakespeareLower) || shakespeareLower.includes(verseLower)) {
            score += 100;
        }
        
        // Check for keyword matches
        shakespeareKeywords.forEach(keyword => {
            if (verse.keywords.includes(keyword)) {
                score += 10;
            }
            
            // Check for partial matches
            verse.keywords.forEach(verseKeyword => {
                if (verseKeyword.includes(keyword) || keyword.includes(verseKeyword)) {
                    score += 5;
                }
            });
        });

        // Check for archaic word matches (important for Shakespeare)
        shakespeareArchaic.forEach(archaicWord => {
            if (verse.archaicKeywords.includes(archaicWord)) {
                score += 15; // Higher score for archaic matches
            }
        });

        // Check for thematic matches
        const biblicalThemes = this.getBiblicalThemes(shakespeareKeywords);
        const verseThemes = this.getBiblicalThemes(verse.keywords);
        
        biblicalThemes.forEach(theme => {
            if (verseThemes.includes(theme)) {
                score += 15;
            }
        });

        return score;
    }

    // Identify Biblical themes in text
    getBiblicalThemes(keywords) {
        const themes = [];
        
        const themeKeywords = {
            'creation': ['create', 'beginning', 'earth', 'heaven', 'light', 'dark'],
            'salvation': ['save', 'redeem', 'grace', 'mercy', 'forgive', 'sin'],
            'wisdom': ['wise', 'wisdom', 'knowledge', 'understanding', 'prudent'],
            'love': ['love', 'charity', 'kindness', 'compassion', 'mercy'],
            'justice': ['judge', 'justice', 'righteous', 'wicked', 'evil', 'good'],
            'prophecy': ['prophet', 'prophecy', 'vision', 'dream', 'foretell'],
            'kingdom': ['king', 'kingdom', 'throne', 'rule', 'reign', 'power'],
            'covenant': ['covenant', 'promise', 'oath', 'swear', 'vow'],
            'temple': ['temple', 'altar', 'sacrifice', 'priest', 'worship'],
            'exile': ['exile', 'captive', 'prison', 'bondage', 'free', 'deliver']
        };

        keywords.forEach(keyword => {
            Object.entries(themeKeywords).forEach(([theme, themeWords]) => {
                if (themeWords.some(themeWord => 
                    keyword.includes(themeWord) || themeWord.includes(keyword)
                )) {
                    themes.push(theme);
                }
            });
        });

        return [...new Set(themes)]; // Remove duplicates
    }

    // Get Bible context for analysis levels
    getBibleContext(shakespeareText, playName, level = 'intermediate') {
        // Don't include Biblical references for basic level
        if (level === 'basic') {
            return null;
        }

        // Determine number of results based on level
        const resultsCount = {
            'intermediate': 2,
            'expert': 3,
            'full-fathom-five': 5
        };

        const maxResults = resultsCount[level] || 2;
        const passages = this.searchBiblePassages(shakespeareText, playName, maxResults);

        if (passages.length === 0) {
            return null;
        }

        return {
            passages,
            totalFound: passages.length,
            searchText: shakespeareText,
            playName: playName
        };
    }

    // Format Bible context for inclusion in AI prompt
    formatBibleContextForPrompt(bibleContext) {
        if (!bibleContext || !bibleContext.passages || bibleContext.passages.length === 0) {
            return '';
        }

        let context = '\n\n## Geneva Bible Context\n';
        context += `Found ${bibleContext.passages.length} potentially relevant Biblical passages:\n\n`;

        bibleContext.passages.forEach((passage, index) => {
            context += `${index + 1}. ${passage.reference}\n`;
            context += `   Text: "${passage.text}"\n`;
            context += `   Relevance Score: ${passage.relevance}\n\n`;
        });

        context += 'Use these Biblical references to inform your analysis if they provide relevant context for understanding the Shakespeare passage.';

        return context;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BibleSearch };
}
