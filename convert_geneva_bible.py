#!/usr/bin/env python3
"""
Conversion script for Geneva Bible text file
Converts from "Genesis 1:1" format to "[1:1]" format for bibleSearch.js parser
"""

import os
import re

def convert_geneva_bible_format(input_text):
    """Convert Geneva Bible text from current format to parser-compatible format."""
    print('Starting Geneva Bible format conversion...')
    
    # Split into lines
    lines = input_text.split('\n')
    converted_lines = []
    
    current_book = None
    in_book_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip header lines
        if line in ['Geneva Bible', 'This Bible is in the Public Domain.']:
            print(f'Skipping header line: "{line}"')
            continue
        
        # Check if this is a verse line (contains "Chapter:Verse" pattern)
        verse_match = re.match(r'^([A-Za-z\s]+)\s+(\d+):(\d+)\s+(.+)$', line)
        
        if verse_match:
            book_name = verse_match.group(1).strip()
            chapter = verse_match.group(2)
            verse = verse_match.group(3)
            verse_text = verse_match.group(4).strip()
            
            # If we have a new book, add the book header
            if book_name != current_book:
                if current_book:
                    # Add a blank line between books
                    converted_lines.append('')
                converted_lines.append(book_name)
                current_book = book_name
                in_book_section = True
                print(f'Processing book: {book_name}')
            
            # Convert to the expected format: [chapter:verse] text
            converted_verse = f'[{chapter}:{verse}] {verse_text}'
            converted_lines.append(converted_verse)
            
        else:
            # This might be a book name or other content
            # Check if it looks like a book name (no numbers, no colons)
            if ':' not in line and not re.search(r'\d', line) and len(line) < 50:
                # This could be a book name or section header
                if line != current_book:
                    if current_book:
                        converted_lines.append('')
                    converted_lines.append(line)
                    current_book = line
                    print(f'Found book/section: {line}')
            else:
                # This might be continuation text or other content
                # Add it as-is if we're in a book section
                if in_book_section:
                    converted_lines.append(line)
    
    print(f'Conversion complete. Processed {len(converted_lines)} lines.')
    return '\n'.join(converted_lines)

def convert_geneva_bible_file():
    """Main conversion function."""
    try:
        input_path = os.path.join('Public', 'Data', 'geneva_bible.txt')
        output_path = os.path.join('Public', 'Data', 'geneva_bible_converted.txt')
        
        print(f'Reading Geneva Bible file from: {input_path}')
        
        # Check if input file exists
        if not os.path.exists(input_path):
            print(f'❌ Input file not found: {input_path}')
            return
        
        # Read the original file
        with open(input_path, 'r', encoding='utf-8') as f:
            input_text = f.read()
        
        print(f'Read {len(input_text)} characters from input file')
        
        # Convert the format
        converted_text = convert_geneva_bible_format(input_text)
        
        # Write the converted file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted_text)
        
        print(f'Converted file written to: {output_path}')
        
        # Show a sample of the converted output
        sample_lines = converted_text.split('\n')[:20]
        print('\n=== SAMPLE OF CONVERTED OUTPUT ===')
        for line in sample_lines:
            print(line)
        print('=== END SAMPLE ===\n')
        
        print('✅ Geneva Bible conversion completed successfully!')
        print(f'📁 Original file: {input_path}')
        print(f'📁 Converted file: {output_path}')
        print('\nTo use the converted file:')
        print('1. Rename geneva_bible_converted.txt to geneva_bible.txt')
        print('2. Or update the file path in bibleSearch.js')
        
    except Exception as error:
        print(f'❌ Error during conversion: {error}')

if __name__ == '__main__':
    convert_geneva_bible_file()
