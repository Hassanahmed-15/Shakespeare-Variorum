import React, { useState } from 'react'
import { useNotes } from '../context/NotesContext'
import { 
  BookOpen, 
  Copy, 
  Share2,
  ChevronDown,
  ChevronUp,
  Type,
  AlignLeft,
  ArrowLeft
} from 'lucide-react'

const ReaderPanel = ({ selectedText, setSelectedText, onBackToLibrary }) => {
  const { 
    isLoaded, 
    currentScene, 
    setCurrentScene, 
    getSceneContent, 
    getActsAndScenes,
    getSceneMetadata 
  } = useNotes()
  
  const [selectedLine, setSelectedLine] = useState(null)
  const [showLineNumbers, setShowLineNumbers] = useState(true)
  const [fontSize, setFontSize] = useState('text-lg')
  const [lineSpacing, setLineSpacing] = useState('leading-relaxed')
  const [expandedActs, setExpandedActs] = useState({ 'ACT 1': true })
  const [forceUpdate, setForceUpdate] = useState(0)

  // Force re-render when scene changes
  React.useEffect(() => {
    console.log('Scene changed to:', currentScene)
    setForceUpdate(prev => prev + 1)
  }, [currentScene])

  const actsAndScenes = getActsAndScenes()
  
  // Force re-calculation of scene content when currentScene changes
  const sceneContent = React.useMemo(() => {
    console.log('Calculating scene content for:', currentScene)
    return getSceneContent(currentScene)
  }, [currentScene, getSceneContent])
  
  const sceneMetadata = React.useMemo(() => {
    return getSceneMetadata(currentScene)
  }, [currentScene, getSceneMetadata])

  // Copy text to clipboard
  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  // Share text
  const shareText = async (text) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Shakespeare Quote',
          text: text,
          url: window.location.href
        })
      } catch (err) {
        console.error('Error sharing:', err)
      }
    } else {
      copyToClipboard(text)
    }
  }

  // Handle line selection
  const handleLineClick = (line) => {
    setSelectedLine(line)
    setSelectedText(line.text)
  }

  // Toggle act expansion
  const toggleAct = (actName) => {
    setExpandedActs(prev => ({
      ...prev,
      [actName]: !prev[actName]
    }))
  }

  // Handle scene selection
  const handleSceneSelect = (sceneName) => {
    console.log('=== SCENE SELECTION ===')
    console.log('Selecting scene:', sceneName)
    console.log('Previous scene:', currentScene)
    console.log('Available acts and scenes:', actsAndScenes)
    
    // Clear selections first
    setSelectedLine(null)
    setSelectedText('')
    
    // Update scene
    setCurrentScene(sceneName)
    
    // Force immediate re-render
    setForceUpdate(prev => prev + 1)
    
    console.log('Scene selection completed. New scene:', sceneName)
  }

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading Shakespeare Database...</p>
        </div>
      </div>
    )
  }

  // Debug info
  console.log('ReaderPanel debug:', {
    isLoaded,
    currentScene,
    sceneContent: sceneContent.length,
    actsAndScenes: Object.keys(actsAndScenes),
    sceneContentSample: sceneContent.slice(0, 2),
    forceUpdate
  })

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800/50">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToLibrary}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors"
            title="Back to Library"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <BookOpen className="w-6 h-6 text-blue-400" />
          <div>
            <h2 className="text-lg font-semibold text-white">Macbeth</h2>
            {currentScene && (
              <p className="text-sm text-gray-400">{currentScene}</p>
            )}
          </div>
        </div>
        
        {/* Settings */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowLineNumbers(!showLineNumbers)}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              showLineNumbers
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {showLineNumbers ? 'Hide' : 'Show'} Numbers
          </button>
        </div>
      </div>

      {/* Scene Selector */}
      <div className="flex-shrink-0 border-b border-gray-700">
        <div className="p-4">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Select Scene</h3>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {Object.entries(actsAndScenes).map(([actName, actData]) => (
              <div key={actName} className="border border-gray-700 rounded-lg">
                <button
                  onClick={() => toggleAct(actName)}
                  className="w-full p-3 text-left flex items-center justify-between bg-gray-800 hover:bg-gray-700 transition-colors rounded-lg"
                >
                  <span className="font-medium text-white">{actName}</span>
                  {expandedActs[actName] ? (
                    <ChevronUp className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  )}
                </button>
                
                {expandedActs[actName] && (
                  <div className="p-2 space-y-1">
                    {actData.scenes.map((sceneName) => (
                      <button
                        key={sceneName}
                        onClick={() => handleSceneSelect(sceneName)}
                        className={`w-full p-2 text-left rounded text-sm transition-colors ${
                          currentScene === sceneName
                            ? 'bg-blue-600 text-white'
                            : 'text-gray-300 hover:bg-gray-700'
                        }`}
                      >
                        {sceneName.replace(/^ACT \d+, /, '')}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Scene Content */}
      <div className="flex-1 overflow-y-auto p-6" key={`${currentScene}-${forceUpdate}`}>
        {currentScene && sceneContent.length > 0 ? (
          <div className="space-y-6">
            {/* Scene Header */}
            {sceneMetadata && (
              <div className="text-center pb-6 border-b border-gray-700">
                <h2 className="text-2xl font-bold text-white mb-2">{currentScene}</h2>
                {sceneMetadata.characters && sceneMetadata.characters.length > 0 && (
                  <p className="text-sm text-gray-500 mt-2">
                    Characters: {sceneMetadata.characters.join(', ')}
                  </p>
                )}
              </div>
            )}

            {/* Lines */}
            <div className="space-y-4">
              {sceneContent.map((line, index) => (
                <div
                  key={line.id}
                  className={`group relative p-4 rounded-lg border transition-all duration-300 cursor-pointer ${
                    selectedLine?.id === line.id
                      ? 'border-blue-500 bg-blue-500/10 shadow-lg'
                      : 'border-gray-700 hover:border-gray-600 bg-gray-800/50 hover:bg-gray-800'
                  }`}
                  onClick={() => handleLineClick(line)}
                >
                  {/* Line Number */}
                  {showLineNumbers && (
                    <div className="absolute top-2 left-2 text-xs text-gray-500 font-mono">
                      {line.line_number}
                    </div>
                  )}

                  {/* Character Name */}
                  <div className="text-sm font-semibold text-blue-400 mb-2">
                    {line.character}
                  </div>

                  {/* Line Text */}
                  <div className={`${fontSize} ${lineSpacing} text-white leading-relaxed`}>
                    {line.text.split('\n').map((part, i) => (
                      <div key={i} className="mb-2">
                        {part}
                      </div>
                    ))}
                  </div>

                  {/* Action Buttons (visible on hover) */}
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        copyToClipboard(line.text)
                      }}
                      className="p-1 rounded bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-white transition-colors"
                      title="Copy"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        shareText(line.text)
                      }}
                      className="p-1 rounded bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-white transition-colors"
                      title="Share"
                    >
                      <Share2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-400 py-12">
            <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No content available for this scene</p>
            <p className="text-sm mt-2">Please select a different scene</p>
            <div className="mt-4 p-4 bg-gray-800/50 rounded-lg">
              <p className="text-xs text-gray-500">Debug Info:</p>
              <p className="text-xs text-gray-500">Current Scene: {currentScene}</p>
              <p className="text-xs text-gray-500">Available Scenes: {Object.keys(actsAndScenes).join(', ')}</p>
            </div>
          </div>
        )}
      </div>

      {/* Settings Panel */}
      <div className="flex-shrink-0 border-t border-gray-700 p-4 bg-gray-800/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Font Size */}
            <div className="flex items-center gap-2">
              <Type className="w-4 h-4 text-gray-400" />
              <select
                value={fontSize}
                onChange={(e) => setFontSize(e.target.value)}
                className="px-2 py-1 rounded bg-gray-700 text-white text-sm border border-gray-600"
              >
                <option value="text-sm">Small</option>
                <option value="text-base">Medium</option>
                <option value="text-lg">Large</option>
                <option value="text-xl">Extra Large</option>
              </select>
            </div>

            {/* Line Spacing */}
            <div className="flex items-center gap-2">
              <AlignLeft className="w-4 h-4 text-gray-400" />
              <select
                value={lineSpacing}
                onChange={(e) => setLineSpacing(e.target.value)}
                className="px-2 py-1 rounded bg-gray-700 text-white text-sm border border-gray-600"
              >
                <option value="leading-tight">Tight</option>
                <option value="leading-normal">Normal</option>
                <option value="leading-relaxed">Relaxed</option>
                <option value="leading-loose">Loose</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ReaderPanel
