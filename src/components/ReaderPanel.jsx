import React, { useEffect, useRef } from 'react'
import { BookOpen } from 'lucide-react'

const ReaderPanel = ({ selectedPlay, currentScene, setSelectedText }) => {
  const contentRef = useRef(null)

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
    // This would normally load from a file, but for now we'll show sample content
    if (sceneName === 'ACT 1, SCENE 1') {
      return [
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
      ]
    }
    
    return [
      { character: 'Sample Character', dialogue: 'This is sample content for other scenes.' }
    ]
  }

  if (!selectedPlay) {
    return (
      <div className="flex-1">
        <div className="card p-12 text-center">
          <div className="w-20 h-20 mx-auto mb-6 text-gray-500">
            <BookOpen className="w-full h-full" />
          </div>
          <h3 className="text-2xl font-semibold text-gray-300 mb-3">
            Welcome to Shakespeare Digital Variorum
          </h3>
          <p className="text-gray-400 max-w-md mx-auto">
            Select Macbeth from the library to begin exploring the play with scholarly commentary and AI analysis.
          </p>
        </div>
      </div>
    )
  }

  if (!currentScene) {
    return (
      <div className="flex-1">
        <div className="card p-12 text-center">
          <h3 className="text-2xl font-semibold text-gray-300 mb-3">
            Select a Scene
          </h3>
          <p className="text-gray-400">
            Choose a scene from the navigation to begin reading.
          </p>
        </div>
      </div>
    )
  }

  const sceneContent = getSceneContent(currentScene)

  return (
    <div className="flex-1">
      <div className="card p-8" ref={contentRef}>
        {/* Scene Header */}
        <div className="mb-8 pb-6 border-b border-gray-700">
          <h1 className="text-3xl font-bold gradient-text mb-2">
            {currentScene}
          </h1>
          <p className="text-gray-400">
            {selectedPlay} • {currentScene}
          </p>
        </div>

        {/* Play Content */}
        <div className="space-y-6 font-serif text-lg leading-relaxed">
          {sceneContent.map((line, index) => (
            <div 
              key={index}
              className="p-4 rounded-lg bg-gray-800/50 border border-gray-700 hover:bg-gray-800 hover:border-gray-600 transition-all duration-200"
            >
              <div className="font-sans font-semibold text-primary-400 uppercase tracking-wide text-sm mb-2">
                {line.character}
              </div>
              <div className="text-gray-100 leading-relaxed">
                {line.dialogue.split('\n').map((text, i) => (
                  <div key={i} className="mb-2 last:mb-0">
                    {text}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default ReaderPanel
