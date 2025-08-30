import React, { useEffect, useRef, useState } from 'react'
import { BookOpen, Search, Copy, Share2, Play, Pause, Volume2, Settings } from 'lucide-react'

const ReaderPanel = ({ selectedPlay, currentScene, setSelectedText }) => {
  const contentRef = useRef(null)
  const [selectedLine, setSelectedLine] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [fontSize, setFontSize] = useState('lg')

  // Handle text selection
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection()
      const selectedText = selection.toString().trim()
      
      if (selectedText && selectedText.length > 0) {
        setSelectedText(selectedText)
        highlightSelectedText()
      } else {
        clearHighlighting()
      }
    }

    const handleClickOutside = (event) => {
      if (!contentRef.current?.contains(event.target)) {
        clearHighlighting()
      }
    }

    document.addEventListener('mouseup', handleSelection)
    document.addEventListener('click', handleClickOutside)

    return () => {
      document.removeEventListener('mouseup', handleSelection)
      document.removeEventListener('click', handleClickOutside)
    }
  }, [setSelectedText])

  const highlightSelectedText = () => {
    clearHighlighting()
    
    const selection = window.getSelection()
    if (selection.rangeCount > 0) {
      const range = selection.getRangeAt(0)
      const span = document.createElement('span')
      span.className = 'highlight'
      range.surroundContents(span)
    }
  }

  const clearHighlighting = () => {
    const highlights = document.querySelectorAll('.highlight')
    highlights.forEach(highlight => {
      const parent = highlight.parentNode
      parent.replaceChild(document.createTextNode(highlight.textContent), highlight)
      parent.normalize()
    })
  }

  const getSceneContent = (sceneName) => {
    const macbethText = {
      'ACT 1, SCENE 1': [
        { character: 'First Witch', dialogue: 'When shall we three meet again\nIn thunder, lightning, or in rain?' },
        { character: 'Second Witch', dialogue: 'When the hurlyburly\'s done,\nWhen the battle\'s lost and won.' },
        { character: 'Third Witch', dialogue: 'That will be ere the set of sun.' },
        { character: 'First Witch', dialogue: 'Where the place?' },
        { character: 'Second Witch', dialogue: 'Upon the heath.' },
        { character: 'Third Witch', dialogue: 'There to meet with Macbeth.' },
        { character: 'First Witch', dialogue: 'I come, Graymalkin!' },
        { character: 'Second Witch', dialogue: 'Paddock calls.' },
        { character: 'Third Witch', dialogue: 'Anon.' },
        { character: 'ALL', dialogue: 'Fair is foul, and foul is fair:\nHover through the fog and filthy air.' }
      ],
      'ACT 1, SCENE 2': [
        { character: 'DUNCAN', dialogue: 'What bloody man is that? He can report,\nAs seemeth by his plight, of the revolt\nThe newest state.' },
        { character: 'MALCOLM', dialogue: 'This is the sergeant\nWho like a good and hardy soldier fought\n\'Gainst my captivity. Hail, brave friend!\nSay to the king the knowledge of the broil\nAs thou didst leave it.' },
        { character: 'Sergeant', dialogue: 'Doubtful it stood;\nAs two spent swimmers, that do cling together\nAnd choke their art. The merciless Macdonwald—\nWorthy to be a rebel, for to that\nThe multiplying villanies of nature\nDo swarm upon him—from the western isles\nOf kerns and gallowglasses is supplied;\nAnd fortune, on his damned quarrel smiling,\nShow\'d like a rebel\'s whore: but all\'s too weak:\nFor brave Macbeth—well he deserves that name—\nDisdaining fortune, with his brandish\'d steel,\nWhich smoked with bloody execution,\nLike valour\'s minion carved out his passage\nTill he faced the slave;\nWhich ne\'er shook hands, nor bade farewell to him,\nTill he unseam\'d him from the nave to the chaps,\nAnd fix\'d his head upon our battlements.' }
      ]
    }

    return macbethText[sceneName] || [
      { character: 'Narrator', dialogue: `Content for ${sceneName} is being prepared. This scene will be available soon with full text and scholarly notes.` }
    ]
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
  }

  const shareText = (text) => {
    if (navigator.share) {
      navigator.share({
        title: `${currentScene} - ${selectedPlay}`,
        text: text
      })
    } else {
      copyToClipboard(text)
    }
  }

  const togglePlay = () => {
    setIsPlaying(!isPlaying)
  }

  if (!selectedPlay) {
    return (
      <div className="flex-1">
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-8">
          <div className="max-w-2xl text-center">
            <div className="w-32 h-32 mx-auto mb-8 bg-gradient-to-br from-primary-600 to-primary-800 rounded-full flex items-center justify-center shadow-2xl">
              <BookOpen className="w-16 h-16 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent mb-6">
              Shakespeare Digital Variorum
            </h1>
            <p className="text-xl text-gray-300 mb-8 leading-relaxed">
              Experience Shakespeare's works with scholarly commentary, AI analysis, and interactive research tools.
            </p>
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
              <p className="text-gray-400">
                Select Macbeth from the library to begin your scholarly exploration.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!currentScene) {
    return (
      <div className="flex-1">
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-8">
          <div className="max-w-md text-center">
            <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-primary-600 to-primary-800 rounded-full flex items-center justify-center shadow-xl">
              <Play className="w-12 h-12 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-gray-100 mb-4">
              Select a Scene
            </h2>
            <p className="text-gray-400">
              Choose a scene from the navigation to begin reading with scholarly commentary.
            </p>
          </div>
        </div>
      </div>
    )
  }

  const sceneContent = getSceneContent(currentScene)

  return (
    <div className="flex-1 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 min-h-screen">
      {/* Header with Controls */}
      <div className="sticky top-0 z-50 bg-gray-900/95 backdrop-blur-md border-b border-gray-700/50">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
                {currentScene}
              </h1>
              <p className="text-gray-400 mt-1">
                {selectedPlay} • Shakespeare Digital Variorum
              </p>
            </div>
            
            {/* Playback Controls */}
            <div className="flex items-center gap-4">
              <button
                onClick={togglePlay}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-lg hover:from-primary-700 hover:to-primary-800 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                {isPlaying ? 'Pause' : 'Play'}
              </button>
              
              <div className="flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-gray-400" />
                <div className="w-20 h-2 bg-gray-700 rounded-full">
                  <div className="w-3/4 h-full bg-primary-500 rounded-full"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Settings Bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Font:</span>
                <select 
                  value={fontSize} 
                  onChange={(e) => setFontSize(e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-200"
                >
                  <option value="sm">Small</option>
                  <option value="md">Medium</option>
                  <option value="lg">Large</option>
                  <option value="xl">Extra Large</option>
                  <option value="2xl">2XL</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Settings className="w-4 h-4" />
              <span>Reading Mode</span>
            </div>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="p-8" ref={contentRef}>
        <div className="max-w-4xl mx-auto">
          {/* Scene Content - Subtitle Style */}
          <div className="space-y-8 text-lg leading-relaxed">
            {sceneContent.map((line, index) => (
              <div 
                key={index}
                className={`group relative p-6 rounded-2xl transition-all duration-300 cursor-pointer ${
                  selectedLine === line 
                    ? 'bg-gradient-to-r from-primary-900/50 to-primary-800/50 border-2 border-primary-500/50 shadow-2xl' 
                    : 'bg-gray-800/30 border border-gray-700/30 hover:bg-gray-800/50 hover:border-gray-600/50 hover:shadow-xl'
                }`}
                onClick={() => {
                  setSelectedLine(line)
                  setSelectedText(line.dialogue)
                }}
              >
                {/* Character Name - Subtitle Style */}
                <div className="mb-3">
                  <div className="inline-block px-3 py-1 bg-gradient-to-r from-primary-600 to-primary-700 text-white text-sm font-semibold rounded-full shadow-lg">
                    {line.character}
                  </div>
                </div>

                {/* Dialogue Text - Subtitle Style */}
                <div className="text-gray-100 leading-relaxed select-text">
                  {line.dialogue.split('\n').map((text, i) => (
                    <div key={i} className="mb-2 last:mb-0">
                      {text}
                    </div>
                  ))}
                </div>

                {/* Action Buttons - Appear on Hover */}
                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      copyToClipboard(line.dialogue)
                    }}
                    className="p-2 bg-gray-700/80 hover:bg-gray-600/80 rounded-lg transition-colors duration-200"
                    title="Copy text"
                  >
                    <Copy className="w-4 h-4 text-gray-300" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      shareText(line.dialogue)
                    }}
                    className="p-2 bg-gray-700/80 hover:bg-gray-600/80 rounded-lg transition-colors duration-200"
                    title="Share text"
                  >
                    <Share2 className="w-4 h-4 text-gray-300" />
                  </button>
                </div>

                {/* Line Number */}
                <div className="absolute bottom-2 right-2 text-xs text-gray-500 font-mono">
                  {index + 1}
                </div>
              </div>
            ))}
          </div>

          {/* Instructions */}
          <div className="mt-12 p-6 bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-700/30 rounded-2xl backdrop-blur-sm">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <Search className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-100 mb-2">
                  How to Use This Digital Variorum
                </h3>
                <ul className="text-gray-300 space-y-1 text-sm">
                  <li>• <strong>Click on any line</strong> to select it for analysis</li>
                  <li>• <strong>Highlight specific text</strong> for detailed scholarly commentary</li>
                  <li>• <strong>Use the analysis panel</strong> to explore different levels of interpretation</li>
                  <li>• <strong>Access research links</strong> for further scholarly exploration</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ReaderPanel
