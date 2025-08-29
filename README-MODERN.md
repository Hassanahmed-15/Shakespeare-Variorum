# Shakespeare Digital Variorum - Modern Version

## 🎭 Overview

This is a modern, redesigned version of the Shakespeare Digital Variorum with enhanced features and a sleek, contemporary interface. The system now integrates pre-existing scholarly notes from `macbeth_notes.json` with AI-powered analysis.

## ✨ New Features

### 1. **Modern UI Design**
- Clean, contemporary interface with improved typography
- Responsive design that works on all devices
- Smooth animations and transitions
- Professional color scheme and spacing

### 2. **Play Selection System**
- Currently supports **Macbeth** (as requested)
- Easy-to-use dropdown selector
- Structured navigation by acts and scenes
- Clear visual hierarchy

### 3. **Notes Integration**
- **Priority System**: When you highlight text, the system first checks `macbeth_notes.json` for existing scholarly notes
- **Fallback to AI**: If no notes exist, it generates AI analysis using the existing system
- **Seamless Experience**: Notes appear immediately without any delay
- **Rich Formatting**: Notes are beautifully formatted with proper typography

### 4. **Enhanced Analysis**
- Three analysis modes: Basic, Expert, Full Fathom Five
- Improved text highlighting system
- Better error handling and loading states
- Keyboard shortcuts (Ctrl/Cmd + Enter to analyze)

## 🚀 Getting Started

### Prerequisites
- Node.js and npm installed
- Netlify CLI (for deployment)
- OpenAI API key

### Setup

1. **Environment Variables**
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Run Locally**
   ```bash
   netlify dev
   ```

4. **Access the Application**
   Open `http://localhost:8888` in your browser

## 📁 File Structure

```
Shakespeare-Variorum/
├── index-modern.html          # New modern interface
├── styles/
│   └── modern-ui.css         # Modern styling
├── Public/Data/
│   ├── notes-integration.js  # Notes integration system
│   └── macbeth_notes.json    # Scholarly notes database
├── functions/
│   └── shakespeare.js        # AI analysis backend
├── .env                      # Environment variables
└── README-MODERN.md         # This file
```

## 🎯 How to Use

### 1. **Select a Play**
- Choose "Macbeth" from the dropdown in the sidebar
- The navigation will populate with acts and scenes

### 2. **Navigate the Play**
- Click on any act or scene in the sidebar
- The play text will load in the main reader panel

### 3. **Analyze Text**
- **Highlight any text** in the play
- **Notes Integration**: If scholarly notes exist, they appear immediately
- **AI Analysis**: If no notes exist, click "Analyze Text" for AI-generated analysis

### 4. **Choose Analysis Level**
- **Basic**: Simple explanations for students
- **Expert**: Detailed scholarly analysis
- **Full Fathom Five**: Comprehensive variorum-style commentary

## 🔧 Technical Implementation

### Notes Integration System (`notes-integration.js`)

The notes integration system:
- Loads `macbeth_notes.json` on page load
- Matches highlighted text against the database using multiple strategies
- Formats notes with proper typography and structure
- Provides seamless fallback to AI analysis

### Text Matching Algorithm

The system uses several matching strategies:
1. **Exact Match**: Perfect text match
2. **Contains Match**: Highlighted text is part of a play line
3. **Word-by-Word Matching**: For longer selections, matches individual words
4. **Fuzzy Matching**: Handles slight variations in text

### Modern UI (`modern-ui.css`)

The new CSS provides:
- CSS custom properties for consistent theming
- Modern color palette and typography
- Responsive grid layout
- Smooth animations and transitions
- Professional shadows and borders
- Accessibility features

## 🎨 Design Features

### Color Palette
- **Primary**: Blue (#2563eb) for main actions
- **Secondary**: Gray tones for text and borders
- **Accent**: Orange (#f59e0b) for highlights
- **Success/Error**: Green/Red for feedback

### Typography
- **Sans-serif**: Inter for UI elements
- **Serif**: Source Serif 4 for play text
- **Monospace**: JetBrains Mono for code

### Layout
- **Three-column grid**: Sidebar, Reader, Analysis
- **Sticky positioning**: Sidebar and analysis panel stay in view
- **Responsive**: Adapts to different screen sizes

## 🔄 Notes vs AI Priority System

### How It Works
1. User highlights text
2. System checks `macbeth_notes.json` first
3. If notes found → Display immediately
4. If no notes → Show AI analysis option
5. User clicks "Analyze Text" for AI analysis

### Benefits
- **Instant Access**: Pre-existing notes load immediately
- **Scholarly Authority**: Notes come from established scholarship
- **Cost Effective**: Reduces API calls for documented passages
- **Comprehensive**: AI fills gaps where notes don't exist

## 🚀 Deployment

### Netlify Deployment
1. Connect your repository to Netlify
2. Set environment variables in Netlify dashboard:
   - `OPENAI_API_KEY`
3. Deploy automatically on push to main branch

### Environment Variables
Make sure to set these in your Netlify environment:
- `OPENAI_API_KEY`: Your OpenAI API key

## 🔮 Future Enhancements

### Planned Features
- Add more plays to the library
- Expand notes database for other plays
- Enhanced search functionality
- User annotations and bookmarks
- Export analysis to PDF
- Collaborative features

### Technical Improvements
- Caching system for better performance
- Progressive Web App features
- Offline support for notes
- Advanced text matching algorithms

## 🐛 Troubleshooting

### Common Issues

1. **Notes not loading**
   - Check that `macbeth_notes.json` is accessible
   - Verify the file path in `notes-integration.js`

2. **AI analysis not working**
   - Verify your OpenAI API key is set
   - Check Netlify function logs for errors

3. **Styling issues**
   - Ensure `modern-ui.css` is properly linked
   - Check browser console for CSS errors

### Debug Mode
Enable debug logging by adding this to the browser console:
```javascript
localStorage.setItem('debug', 'true');
```

## 📚 API Reference

### Notes Integration API

```javascript
// Initialize notes system
await window.notesIntegration.loadNotes();

// Find notes for text
const notes = window.notesIntegration.findNotesForLine(selectedText);

// Format notes for display
const formatted = window.notesIntegration.formatNotes(notesData);
```

### AI Analysis API

```javascript
// Generate AI analysis
const response = await fetch('/.netlify/functions/shakespeare', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: selectedText,
    level: 'basic|expert|fullfathomfive',
    playName: 'Macbeth',
    sceneName: 'ACT 1, SCENE 1'
  })
});
```

## 🤝 Contributing

To contribute to this project:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Shakespeare scholars whose work is referenced in the notes
- OpenAI for providing the AI analysis capabilities
- The Shakespeare community for ongoing support and feedback

---

**Created by Jack David Carson, Massachusetts Institute of Technology • 2025**
