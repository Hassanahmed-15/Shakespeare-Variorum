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
  const [macbethData, setMacbethData] = useState(null)
  const [notesData, setNotesData] = useState(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [currentPlay, setCurrentPlay] = useState('Macbeth')
  const [currentScene, setCurrentScene] = useState('ACT 1, SCENE 1')

  // Load both macbeth data and notes data
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load the complete Macbeth database
        const macbethResponse = await fetch('/Data/macbeth_complete.json')
        if (macbethResponse.ok) {
          const macbethJson = await macbethResponse.json()
          setMacbethData(macbethJson)
          console.log('Macbeth data loaded successfully')
        } else {
          console.warn('Could not load macbeth_complete.json:', macbethResponse.status, macbethResponse.statusText)
        }

        // Load the scholarly notes
        const notesResponse = await fetch('/Data/macbeth_notes.json')
        if (notesResponse.ok) {
          const notesJson = await notesResponse.json()
          setNotesData(notesJson)
          console.log('Notes data loaded successfully')
        } else {
          console.warn('Could not load macbeth_notes.json:', notesResponse.status, notesResponse.statusText)
        }

        setIsLoaded(true)
      } catch (error) {
        console.error('Error loading data:', error)
        // Set loaded to true even if there's an error so the app doesn't get stuck
        setIsLoaded(true)
      }
    }

    loadData()
  }, [])

  // Get scene content from macbeth database
  const getSceneContent = (sceneName) => {
    if (!macbethData || !macbethData.scenes || !macbethData.scenes[sceneName]) {
      return []
    }
    return macbethData.scenes[sceneName].lines || []
  }

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
    if (!notesData) return null

    return {
      lineNumber: notesData.lineNumber,
      playLine: notesData.playLine,
      notes: notesData.notes.map(note => {
        // Format the scholarly note with proper HTML
        return note
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>')
          .replace(/\n/g, '<br>')
      }),
      scene: notesData.scene
    }
  }

  // Get all acts and scenes
  const getActsAndScenes = () => {
    if (!macbethData || !macbethData.acts) {
      return {}
    }
    return macbethData.acts
  }

  // Get scene metadata
  const getSceneMetadata = (sceneName) => {
    if (!macbethData || !macbethData.scenes || !macbethData.scenes[sceneName]) {
      return null
    }
    return macbethData.scenes[sceneName]
  }

  const value = {
    isLoaded,
    currentPlay,
    setCurrentPlay,
    currentScene,
    setCurrentScene,
    findNotesForLine,
    formatNotes,
    getSceneContent,
    getActsAndScenes,
    getSceneMetadata,
    macbethData,
    notesData
  }

  return (
    <NotesContext.Provider value={value}>
      {children}
    </NotesContext.Provider>
  )
}
