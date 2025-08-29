// Notes Integration System for Shakespeare Digital Variorum
// This file handles the integration of pre-existing notes from macbeth_notes.json

class NotesIntegration {
    constructor() {
        this.notesData = null;
        this.currentPlay = '';
        this.currentScene = '';
        this.isLoaded = false;
    }

    // Load the notes data from macbeth_notes.json
    async loadNotes() {
        try {
            const response = await fetch('/Public/Data/macbeth_notes.json');
            if (!response.ok) {
                console.warn('Could not load macbeth_notes.json');
                return false;
            }
            this.notesData = await response.json();
            this.isLoaded = true;
            console.log('Notes data loaded successfully');
            return true;
        } catch (error) {
            console.error('Error loading notes:', error);
            return false;
        }
    }

    // Set the current play and scene context
    setContext(playName, sceneName) {
        this.currentPlay = playName;
        this.currentScene = sceneName;
    }

    // Find notes for a specific line of text
    findNotesForLine(text, sceneName = null) {
        if (!this.isLoaded || !this.notesData) {
            return null;
        }

        const targetScene = sceneName || this.currentScene;
        if (!targetScene || !this.notesData[targetScene]) {
            return null;
        }

        const sceneNotes = this.notesData[targetScene];
        
        // Search through all line entries in the scene
        for (const lineNumber in sceneNotes) {
            const lineData = sceneNotes[lineNumber];
            if (lineData && lineData.play) {
                // Check if the highlighted text matches or is contained in the play line
                const playLine = lineData.play.toLowerCase().trim();
                const searchText = text.toLowerCase().trim();
                
                // Multiple matching strategies
                if (this.matchesText(playLine, searchText)) {
                    return {
                        lineNumber: lineNumber,
                        playLine: lineData.play,
                        notes: lineData.notes || [],
                        scene: targetScene
                    };
                }
            }
        }
        
        return null;
    }

    // Check if the highlighted text matches the play line
    matchesText(playLine, searchText) {
        // Exact match
        if (playLine === searchText) {
            return true;
        }
        
        // Contains match (search text is part of play line)
        if (playLine.includes(searchText) && searchText.length > 3) {
            return true;
        }
        
        // Play line is part of search text
        if (searchText.includes(playLine) && playLine.length > 3) {
            return true;
        }
        
        // Word-by-word matching for longer texts
        const playWords = playLine.split(/\s+/).filter(word => word.length > 2);
        const searchWords = searchText.split(/\s+/).filter(word => word.length > 2);
        
        if (playWords.length > 0 && searchWords.length > 0) {
            const matchingWords = playWords.filter(word => 
                searchWords.some(searchWord => 
                    word.includes(searchWord) || searchWord.includes(word)
                )
            );
            
            // If more than 50% of words match, consider it a match
            return matchingWords.length >= Math.min(playWords.length, searchWords.length) * 0.5;
        }
        
        return false;
    }

    // Format notes for display
    formatNotes(notesData) {
        if (!notesData || !notesData.notes || notesData.notes.length === 0) {
            return null;
        }

        let formattedNotes = '';
        
        // Add header
        formattedNotes += `<div class="notes-header">
            <h3>📚 Scholarly Notes</h3>
            <p class="notes-meta">Line ${notesData.lineNumber} from ${notesData.scene}</p>
        </div>`;
        
        // Add the original play line
        formattedNotes += `<div class="original-line">
            <strong>Original Text:</strong> "${notesData.playLine}"
        </div>`;
        
        // Add notes
        formattedNotes += `<div class="notes-content">`;
        notesData.notes.forEach((note, index) => {
            formattedNotes += `<div class="note-entry">
                <div class="note-text">${this.formatNoteText(note)}</div>
            </div>`;
        });
        formattedNotes += `</div>`;
        
        return formattedNotes;
    }

    // Format individual note text
    formatNoteText(note) {
        // Clean up the note text
        let formatted = note
            .replace(/\*\*/g, '<strong>') // Bold text
            .replace(/\*/g, '<em>') // Italic text
            .replace(/\n/g, '<br>') // Line breaks
            .replace(/\[([^\]]+)\]/g, '<em>$1</em>') // Stage directions in italics
            .replace(/--/g, '—') // Em dashes
            .replace(/\.\.\./g, '…'); // Ellipsis
        
        return formatted;
    }

    // Check if notes exist for the current play
    hasNotesForPlay(playName) {
        if (!this.isLoaded || !this.notesData) {
            return false;
        }
        
        // Currently only Macbeth has notes
        return playName.toLowerCase().includes('macbeth');
    }

    // Get all available scenes with notes
    getScenesWithNotes() {
        if (!this.isLoaded || !this.notesData) {
            return [];
        }
        
        return Object.keys(this.notesData);
    }
}

// Global instance
window.notesIntegration = new NotesIntegration();

// Initialize notes when the page loads
document.addEventListener('DOMContentLoaded', async function() {
    await window.notesIntegration.loadNotes();
});
