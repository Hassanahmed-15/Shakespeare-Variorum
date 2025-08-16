const fs = require('fs');
const path = require('path');

// Conversion script for Geneva Bible text file
// Converts from "Genesis 1:1" format to "[1:1]" format for bibleSearch.js parser

function convertGenevaBibleFormat(inputText) {
    console.log('Starting Geneva Bible format conversion...');
    
    // Split into lines
    const lines = inputText.split('\n');
    const convertedLines = [];
    
    let currentBook = null;
    let inBookSection = false;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Skip empty lines
        if (!line) {
            continue;
        }
        
        // Skip header lines
        if (line === 'Geneva Bible' || line === 'This Bible is in the Public Domain.') {
            console.log(`Skipping header line: "${line}"`);
            continue;
        }
        
        // Check if this is a verse line (contains "Chapter:Verse" pattern)
        const verseMatch = line.match(/^([A-Za-z\s]+)\s+(\d+):(\d+)\s+(.+)$/);
        
        if (verseMatch) {
            const bookName = verseMatch[1].trim();
            const chapter = verseMatch[2];
            const verse = verseMatch[3];
            const verseText = verseMatch[4].trim();
            
            // If we have a new book, add the book header
            if (bookName !== currentBook) {
                if (currentBook) {
                    // Add a blank line between books
                    convertedLines.push('');
                }
                convertedLines.push(bookName);
                currentBook = bookName;
                inBookSection = true;
                console.log(`Processing book: ${bookName}`);
            }
            
            // Convert to the expected format: [chapter:verse] text
            const convertedVerse = `[${chapter}:${verse}] ${verseText}`;
            convertedLines.push(convertedVerse);
            
        } else {
            // This might be a book name or other content
            // Check if it looks like a book name (no numbers, no colons)
            if (!line.includes(':') && !line.match(/\d/) && line.length < 50) {
                // This could be a book name or section header
                if (line !== currentBook) {
                    if (currentBook) {
                        convertedLines.push('');
                    }
                    convertedLines.push(line);
                    currentBook = line;
                    console.log(`Found book/section: ${line}`);
                }
            } else {
                // This might be continuation text or other content
                // Add it as-is if we're in a book section
                if (inBookSection) {
                    convertedLines.push(line);
                }
            }
        }
    }
    
    console.log(`Conversion complete. Processed ${convertedLines.length} lines.`);
    return convertedLines.join('\n');
}

// Main conversion function
async function convertGenevaBibleFile() {
    try {
        const inputPath = path.join(__dirname, 'Public', 'Data', 'geneva_bible.txt');
        const outputPath = path.join(__dirname, 'Public', 'Data', 'geneva_bible_converted.txt');
        
        console.log(`Reading Geneva Bible file from: ${inputPath}`);
        
        // Check if input file exists
        if (!fs.existsSync(inputPath)) {
            console.error(`Input file not found: ${inputPath}`);
            return; 
        }
        
        // Read the original file
        const inputText = fs.readFileSync(inputPath, 'utf8');
        console.log(`Read ${inputText.length} characters from input file`);
        
        // Convert the format
        const convertedText = convertGenevaBibleFormat(inputText);
        
        // Write the converted file
        fs.writeFileSync(outputPath, convertedText, 'utf8');
        console.log(`Converted file written to: ${outputPath}`);
        
        // Show a sample of the converted output
        const sampleLines = convertedText.split('\n').slice(0, 20);
        console.log('\n=== SAMPLE OF CONVERTED OUTPUT ===');
        sampleLines.forEach(line => console.log(line));
        console.log('=== END SAMPLE ===\n');
        
        console.log('✅ Geneva Bible conversion completed successfully!');
        console.log(`📁 Original file: ${inputPath}`);
        console.log(`📁 Converted file: ${outputPath}`);
        console.log('\nTo use the converted file:');
        console.log('1. Rename geneva_bible_converted.txt to geneva_bible.txt');
        console.log('2. Or update the file path in bibleSearch.js');
        
    } catch (error) {
        console.error('❌ Error during conversion:', error);
    }
}

// Run the conversion if this script is executed directly
if (require.main === module) {
    convertGenevaBibleFile();
}

module.exports = { convertGenevaBibleFormat };
