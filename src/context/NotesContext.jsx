import React, { createContext, useContext, useState, useEffect } from 'react'

const NotesContext = createContext()

export const useNotes = () => {
  const context = useContext(NotesContext)
  if (!context) {
    throw new Error('useNotes must be used within a NotesProvider')
  }
  return context
}

export const NotesProvider = ({ children }) => {
  const [notesData, setNotesData] = useState(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [currentPlay, setCurrentPlay] = useState('')
  const [currentScene, setCurrentScene] = useState('')

  // Load notes data
  useEffect(() => {
    const loadNotes = async () => {
      try {
        const response = await fetch('/Public/Data/macbeth_notes.json')
        if (!response.ok) {
          console.warn('Could not load macbeth_notes.json')
          return
        }
        const data = await response.json()
        setNotesData(data)
        setIsLoaded(true)
        console.log('Notes data loaded successfully')
      } catch (error) {
        console.error('Error loading notes:', error)
      }
    }

    loadNotes()
  }, [])

  // Find notes for a specific line of text
  const findNotesForLine = (text, sceneName = null) => {
    if (!isLoaded || !notesData) {
      return null
    }

    const targetScene = sceneName || currentScene
    if (!targetScene || !notesData[targetScene]) {
      return null
    }

    const sceneNotes = notesData[targetScene]
    
    // Search through all line entries in the scene
    for (const lineNumber in sceneNotes) {
      const lineData = sceneNotes[lineNumber]
      if (lineData && lineData.play) {
        // Check if the highlighted text matches or is contained in the play line
        const playLine = lineData.play.toLowerCase().trim()
        const searchText = text.toLowerCase().trim()
        
        // Multiple matching strategies
        if (matchesText(playLine, searchText)) {
          return {
            lineNumber: lineNumber,
            playLine: lineData.play,
            notes: lineData.notes || [],
            scene: targetScene
          }
        }
      }
    }
    
    return null
  }

  // Check if the highlighted text matches the play line
  const matchesText = (playLine, searchText) => {
    // Exact match
    if (playLine === searchText) {
      return true
    }
    
    // Contains match (search text is part of play line)
    if (playLine.includes(searchText) && searchText.length > 3) {
      return true
    }
    
    // Play line is part of search text
    if (searchText.includes(playLine) && playLine.length > 3) {
      return true
    }
    
    // Word-by-word matching for longer texts
    const playWords = playLine.split(/\s+/).filter(word => word.length > 2)
    const searchWords = searchText.split(/\s+/).filter(word => word.length > 2)
    
    if (playWords.length > 0 && searchWords.length > 0) {
      const matchingWords = playWords.filter(word => 
        searchWords.some(searchWord => 
          word.includes(searchWord) || searchWord.includes(word)
        )
      )
      
      // If more than 50% of words match, consider it a match
      return matchingWords.length >= Math.min(playWords.length, searchWords.length) * 0.5
    }
    
    return false
  }

  // Format notes for display
  const formatNotes = (notesData) => {
    if (!notesData || !notesData.notes || notesData.notes.length === 0) {
      return null
    }

    return {
      lineNumber: notesData.lineNumber,
      playLine: notesData.playLine,
      scene: notesData.scene,
      notes: notesData.notes.map(note => formatNoteText(note))
    }
  }

  // Format individual note text
  const formatNoteText = (note) => {
    // Clean up the note text
    return note
      .replace(/\*\*/g, '<strong>') // Bold text
      .replace(/\*/g, '<em>') // Italic text
      .replace(/\n/g, '<br>') // Line breaks
      .replace(/\[([^\]]+)\]/g, '<em>$1</em>') // Stage directions in italics
      .replace(/--/g, '—') // Em dashes
      .replace(/\.\.\./g, '…') // Ellipsis
  }

  // Check if notes exist for the current play
  const hasNotesForPlay = (playName) => {
    if (!isLoaded || !notesData) {
      return false
    }
    
    // Currently only Macbeth has notes
    return playName.toLowerCase().includes('macbeth')
  }

  // Get all available scenes with notes
  const getScenesWithNotes = () => {
    if (!isLoaded || !notesData) {
      return []
    }
    
    return Object.keys(notesData)
  }

  const value = {
    notesData,
    isLoaded,
    currentPlay,
    setCurrentPlay,
    currentScene,
    setCurrentScene,
    findNotesForLine,
    formatNotes,
    hasNotesForPlay,
    getScenesWithNotes
  }

  return (
    <NotesContext.Provider value={value}>
      {children}
    </NotesContext.Provider>
  )
}
