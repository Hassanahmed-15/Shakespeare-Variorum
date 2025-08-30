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

  // Load notes data from macbeth_notes.json
  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetch('/Data/macbeth_notes.json')
        if (response.ok) {
          const data = await response.json()
          setNotesData(data)
          console.log('Macbeth notes loaded successfully')
        } else {
          console.warn('Could not load macbeth_notes.json:', response.status, response.statusText)
        }
        setIsLoaded(true)
      } catch (error) {
        console.error('Error loading data:', error)
        setIsLoaded(true)
      }
    }

    loadData()
  }, [])

  // Get all available scenes
  const getScenes = () => {
    if (!notesData) return []
    return Object.keys(notesData).sort()
  }

  // Get scene content from notes data
  const getSceneContent = (sceneName) => {
    console.log('getSceneContent called with:', sceneName)
    console.log('notesData available:', !!notesData)
    
    if (!notesData) {
      console.log('No notesData available')
      return []
    }
    
    if (!notesData[sceneName]) {
      console.log('Scene not found in notesData:', sceneName)
      console.log('Available scenes:', Object.keys(notesData).slice(0, 10))
      return []
    }
    
    const sceneData = notesData[sceneName]
    console.log('Scene data found:', Object.keys(sceneData).length, 'lines')
    
    const lines = []
    
    // Convert the scene data to a structured format
    Object.keys(sceneData).forEach(lineNumber => {
      const lineData = sceneData[lineNumber]
      if (lineData && lineData.play) {
        // Extract character name and text from the play line
        const playText = lineData.play
        const colonIndex = playText.indexOf(':')
        
        let character = 'Unknown'
        let text = playText
        
        if (colonIndex !== -1) {
          character = playText.substring(0, colonIndex).trim()
          text = playText.substring(colonIndex + 1).trim()
        }
        
        lines.push({
          id: `${sceneName}-${lineNumber}`,
          lineNumber: parseInt(lineNumber),
          character: character,
          text: text,
          notes: lineData.notes || []
        })
      }
    })
    
    const sortedLines = lines.sort((a, b) => a.lineNumber - b.lineNumber)
    console.log('Returning', sortedLines.length, 'lines for scene:', sceneName)
    return sortedLines
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

    const sceneData = notesData[targetScene]
    
    // Search through all line entries in the scene
    for (const lineNumber in sceneData) {
      const lineData = sceneData[lineNumber]
      if (lineData && lineData.play) {
        // Check if the highlighted text matches or is contained in the play line
        const playLine = lineData.play.toLowerCase().trim()
        const searchText = text.toLowerCase().trim()
        
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

  // Get acts and scenes organized by act
  const getActsAndScenes = () => {
    if (!notesData) return {}
    
    const acts = {}
    
    Object.keys(notesData).forEach(sceneName => {
      const actMatch = sceneName.match(/ACT (\d+)/)
      if (actMatch) {
        const actNumber = actMatch[1]
        const actKey = `ACT ${actNumber}`
        
        if (!acts[actKey]) {
          acts[actKey] = { scenes: [] }
        }
        acts[actKey].scenes.push(sceneName)
      }
    })
    
    // Sort scenes within each act
    Object.keys(acts).forEach(actKey => {
      acts[actKey].scenes.sort()
    })
    
    return acts
  }

  // Get scene metadata
  const getSceneMetadata = (sceneName) => {
    if (!notesData || !notesData[sceneName]) {
      return null
    }
    
    // Extract location and characters from the first few lines
    const sceneData = notesData[sceneName]
    const firstLine = Object.values(sceneData)[0]
    
    return {
      location: sceneName,
      characters: extractCharacters(sceneData)
    }
  }

  // Extract character names from scene data
  const extractCharacters = (sceneData) => {
    const characters = new Set()
    
    Object.values(sceneData).forEach(lineData => {
      if (lineData && lineData.play) {
        const playText = lineData.play
        const colonIndex = playText.indexOf(':')
        
        if (colonIndex !== -1) {
          const character = playText.substring(0, colonIndex).trim()
          if (character && character !== 'ALL') {
            characters.add(character)
          }
        }
      }
    })
    
    return Array.from(characters).sort()
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
    getScenes,
    notesData
  }

  return (
    <NotesContext.Provider value={value}>
      {children}
    </NotesContext.Provider>
  )
}
