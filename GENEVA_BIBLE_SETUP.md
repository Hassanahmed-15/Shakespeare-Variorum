# Geneva Bible Setup Guide

## Overview
This guide explains how to set up the Geneva Bible search functionality for your Shakespeare analysis tool. The system is designed to automatically search the 1599 Geneva Bible for relevant passages when analyzing Shakespeare text.

## Current Status
- ✅ Geneva Bible search functionality is implemented
- ✅ Search index and relevance scoring system is ready
- ✅ Integration with AI analysis is complete
- ✅ **Geneva Bible text file**: `geneva_bible.txt` is in place
- ✅ **Parser**: Handles [chapter:verse] format
- ✅ **Archaic language support**: Matches Shakespeare's language (thee, thou, hath, etc.)

## System Status

### ✅ **COMPLETE AND READY TO USE!**

The Geneva Bible search system is now fully implemented and ready to use with your `geneva_bible.txt` file. The system will:

1. **Automatically load** the Geneva Bible text when the page starts
2. **Parse the [chapter:verse] format** from your text file
3. **Create a searchable index** of all verses
4. **Match Shakespeare's archaic language** (thee, thou, hath, etc.)
5. **Integrate with AI analysis** for all levels except 'basic'

### How It Works Now

1. **Text File Loading**: The system loads your `geneva_bible.txt` file automatically
2. **Smart Parsing**: Recognizes [chapter:verse] format and book names
3. **Archaic Language Matching**: Special handling for Shakespeare's language
4. **Relevance Scoring**: Finds the most relevant Biblical passages
5. **AI Integration**: Includes Geneva Bible context in analysis prompts

## How the System Works

### Analysis Levels
- **Basic**: No Geneva Bible references (keeps analysis simple)
- **Intermediate**: 2 Geneva Bible passages
- **Expert**: 3 Geneva Bible passages  
- **Full Fathom Five**: 5 Geneva Bible passages

### Search Process
1. User selects Shakespeare text and chooses analysis level
2. System extracts keywords from Shakespeare text
3. Geneva Bible search finds relevant passages using:
   - Exact phrase matches (highest score)
   - Keyword matches
   - Thematic matches (creation, salvation, wisdom, etc.)
4. Top-scoring passages are included in AI prompt
5. AI analysis incorporates Geneva Bible context

### Relevance Scoring
The system calculates relevance scores based on:
- **Exact phrase matches**: +100 points
- **Keyword matches**: +10 points each
- **Partial keyword matches**: +5 points each
- **Thematic matches**: +15 points each

## Files Involved

### Core Files
- `Public/Data/geneva-bible.json` - Geneva Bible text data
- `Public/Data/geneva-bible-search.js` - Search functionality
- `functions/shakespeare.js` - Backend integration
- `index.html` - Frontend integration

### Integration Points
1. **Frontend**: Automatically loads Geneva Bible data when page loads
2. **Backend**: Calls Geneva Bible search during AI analysis
3. **AI Prompt**: Includes Geneva Bible context for relevant analysis

## Testing the System

### Without Geneva Bible Data
The system will work but won't find any passages. You'll see:
- Console message: "Failed to initialize Geneva Bible search"
- Analysis will proceed without Geneva Bible context

### With Geneva Bible Data
Once you add the Geneva Bible data:
- Console message: "Geneva Bible search initialized successfully"
- Analysis will include Geneva Bible passages when relevant

## Example Usage

When a user selects Shakespeare text like:
> "The quality of mercy is not strained"

The system might find Geneva Bible passages like:
- **James 2:13**: "For he shall have judgment without mercy, that hath showed no mercy"
- **Proverbs 11:17**: "The merciful man doeth good to his own soul"

These would be included in the AI analysis to provide Biblical context.

## Troubleshooting

### Common Issues
1. **"Failed to load Geneva Bible data"**
   - Check that `geneva-bible.json` exists in `Public/Data/`
   - Verify JSON format is correct

2. **No Geneva Bible passages found**
   - Ensure Geneva Bible data is populated
   - Check that search terms are relevant

3. **Performance issues**
   - Geneva Bible data can be large (30,000+ verses)
   - Consider implementing pagination or limiting search scope

## Next Steps

1. **Get Geneva Bible text** from one of the sources listed above
2. **Convert to JSON format** using the structure provided
3. **Replace sample data** in `geneva-bible.json`
4. **Test the system** with Shakespeare passages
5. **Fine-tune search parameters** if needed

## Support

If you need help with:
- Finding Geneva Bible text sources
- Converting text to JSON format
- Troubleshooting search functionality
- Optimizing performance

Please refer to the code comments in the files or create an issue in your project repository.
