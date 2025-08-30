import React, { useState, useEffect } from 'react'
import { useNotes } from '../context/NotesContext'
import { 
  Sparkles, 
  Search, 
  BookMarked, 
  Zap, 
  MessageSquare, 
  Send, 
  Loader2,
  BookOpen,
  ExternalLink,
  Youtube,
  FileText,
  Globe,
  Database
} from 'lucide-react'

const AnalysisPanel = ({ selectedText, setSelectedText }) => {
  const { 
    isLoaded, 
    currentScene, 
    findNotesForLine, 
    formatNotes,
    currentPlay 
  } = useNotes()
  
  const [analysisMode, setAnalysisMode] = useState('basic')
  const [analysisContent, setAnalysisContent] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [followUpQuestion, setFollowUpQuestion] = useState('')
  const [followUpResponse, setFollowUpResponse] = useState('')
  const [isFollowUpLoading, setIsFollowUpLoading] = useState(false)
  const [commentary, setCommentary] = useState(null)

  // Check for commentary when text is selected
  useEffect(() => {
    if (selectedText && selectedText.trim()) {
      const foundNotes = findNotesForLine(selectedText, currentScene)
      if (foundNotes) {
        const formattedNotes = formatNotes(foundNotes)
        setCommentary(formattedNotes)
        console.log('Found commentary:', formattedNotes)
      } else {
        setCommentary(null)
        console.log('No commentary found for:', selectedText)
      }
    } else {
      setCommentary(null)
    }
  }, [selectedText, currentScene, findNotesForLine, formatNotes])

  // Get mode icon and description
  const getModeIcon = (mode) => {
    switch (mode) {
      case 'basic':
        return <BookOpen className="w-5 h-5" />
      case 'expert':
        return <Search className="w-5 h-5" />
      case 'fullfathomfive':
        return <BookMarked className="w-5 h-5" />
      default:
        return <Sparkles className="w-5 h-5" />
    }
  }

  const getModeDescription = (mode) => {
    switch (mode) {
      case 'basic':
        return 'Essential analysis with plain language paraphrase and key glosses'
      case 'expert':
        return 'Comprehensive scholarly analysis with textual variants and critical reception'
      case 'fullfathomfive':
        return 'Complete scholarly commentary with database integration and research links'
      default:
        return 'Select an analysis mode to begin'
    }
  }

  // Analyze text function
  const analyzeText = async () => {
    if (!selectedText || !selectedText.trim()) {
      alert('Please select some text to analyze')
      return
    }

    setIsAnalyzing(true)
    setAnalysisContent(null)

    try {
      console.log('Sending analysis request:', {
        text: selectedText,
        mode: analysisMode,
        scene: currentScene,
        play: currentPlay || 'Macbeth'
      })

      const response = await fetch('/.netlify/functions/shakespeare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: selectedText,
          mode: analysisMode,
          scene: currentScene,
          play: currentPlay || 'Macbeth'
        }),
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', response.headers)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Response error text:', errorText)
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`)
      }

      const data = await response.json()
      console.log('Analysis response:', data)
      
      // Handle the response format
      if (data.analysis) {
        setAnalysisContent(data.analysis)
      } else if (data.error) {
        setAnalysisContent({ error: data.error })
      } else {
        setAnalysisContent({ error: 'Invalid response format' })
      }
      
      console.log('Analysis completed:', data)
    } catch (error) {
      console.error('Error analyzing text:', error)
      setAnalysisContent({
        error: 'Failed to analyze text. Please try again.',
        details: error.message
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Handle follow-up question
  const handleFollowUp = async () => {
    if (!followUpQuestion.trim() || !analysisContent) return

    setIsFollowUpLoading(true)
    try {
      const response = await fetch('/.netlify/functions/shakespeare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: selectedText,
          mode: analysisMode,
          followUp: followUpQuestion,
          previousAnalysis: analysisContent,
          scene: currentScene,
          play: currentPlay || 'Macbeth'
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setFollowUpResponse(data.analysis || data.error || 'No response received')
      setFollowUpQuestion('')
    } catch (error) {
      console.error('Error with follow-up:', error)
      setFollowUpResponse('Sorry, I encountered an error. Please try again.')
    } finally {
      setIsFollowUpLoading(false)
    }
  }

  // Handle research link clicks
  const handleResearchLink = (type) => {
    if (!selectedText) return

    let url = ''
    const encodedText = encodeURIComponent(`"${selectedText}"`)
    const encodedScene = encodeURIComponent(currentScene || 'Macbeth')
    const encodedPlay = encodeURIComponent(currentPlay || 'Macbeth')

    switch (type) {
      case 'youtube':
        url = `https://www.youtube.com/results?search_query=${encodedText} Shakespeare ${encodedPlay} ${encodedScene}`
        break
      case 'jstor-exact':
        url = `https://www.jstor.org/action/doBasicSearch?Query=${encodedText} Shakespeare`
        break
      case 'jstor-passage':
        url = `https://www.jstor.org/action/doBasicSearch?Query=${encodedScene} ${encodedPlay} Shakespeare`
        break
      case 'scholar':
        url = `https://scholar.google.com/scholar?q=${encodedText} Shakespeare ${encodedPlay}`
        break
      case 'internet-shakespeare':
        url = `https://internetshakespeare.uvic.ca/search/?q=${encodedText}`
        break
      default:
        return
    }

    window.open(url, '_blank')
  }

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-gray-700 bg-gray-800/50">
        <div className="flex items-center gap-3 mb-3">
          {getModeIcon(analysisMode)}
          <div>
            <h2 className="text-lg font-semibold text-white">
              {analysisMode === 'basic' && 'Basic Analysis'}
              {analysisMode === 'expert' && 'Expert Analysis'}
              {analysisMode === 'fullfathomfive' && 'Full Fathom Five'}
            </h2>
            <p className="text-sm text-gray-400">{getModeDescription(analysisMode)}</p>
          </div>
        </div>

        {/* Mode Selector */}
        <div className="flex gap-2">
          {['basic', 'expert', 'fullfathomfive'].map((mode) => (
            <button
              key={mode}
              onClick={() => setAnalysisMode(mode)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                analysisMode === mode
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
              }`}
            >
              {getModeIcon(mode)}
              {mode === 'basic' && 'Basic'}
              {mode === 'expert' && 'Expert'}
              {mode === 'fullfathomfive' && 'FFF'}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {!selectedText ? (
          <div className="text-center text-gray-400 py-12">
            <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Click on a line to analyze it</p>
            <p className="text-sm mt-2">Select from Basic, Expert, or Full Fathom Five modes</p>
          </div>
        ) : (
          <>
            {/* Selected Text Display */}
            <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                Selected Text
              </h3>
              <p className="text-white italic">"{selectedText}"</p>
            </div>

            {/* Commentary Section (Full Fathom Five) */}
            {analysisMode === 'fullfathomfive' && commentary && (
              <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-700/30 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-blue-300 mb-3 flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  Scholarly Commentary
                </h3>
                <div className="space-y-3">
                  <div className="text-xs text-gray-400">
                    Line {commentary.lineNumber} • {commentary.scene}
                  </div>
                  <div className="text-sm text-gray-300 italic mb-3">
                    "{commentary.playLine}"
                  </div>
                  {commentary.notes.map((note, index) => (
                    <div 
                      key={index}
                      className="text-sm text-gray-200 leading-relaxed"
                      dangerouslySetInnerHTML={{ __html: note }}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Analysis Content */}
            {analysisContent && !analysisContent.error ? (
              <div className="space-y-4">
                {Object.entries(analysisContent).map(([section, content]) => (
                  <div key={section} className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-gray-300 mb-2 capitalize">
                      {section.replace(/([A-Z])/g, ' $1').trim()}
                    </h3>
                    <div 
                      className="text-sm text-gray-200 leading-relaxed prose prose-invert max-w-none"
                      dangerouslySetInnerHTML={{ __html: content }}
                    />
                  </div>
                ))}
              </div>
            ) : analysisContent?.error ? (
              <div className="bg-red-900/20 border border-red-700/30 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-red-300 mb-2">Analysis Error</h3>
                <p className="text-sm text-red-200">{analysisContent.error}</p>
                {analysisContent.details && (
                  <p className="text-xs text-red-300 mt-2">{analysisContent.details}</p>
                )}
              </div>
            ) : null}

            {/* Test and Analyze Buttons */}
            <div className="space-y-2">
              {/* Test Function Button */}
              <button
                onClick={async () => {
                  try {
                    console.log('Testing Netlify function...')
                    const response = await fetch('/.netlify/functions/test')
                    const data = await response.json()
                    console.log('Test response:', data)
                    alert(`Function test: ${data.message}`)
                  } catch (error) {
                    console.error('Test error:', error)
                    alert(`Test failed: ${error.message}`)
                  }
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-all duration-200"
              >
                Test Function
              </button>

              {/* Analyze Button */}
              {!analysisContent && !isAnalyzing && (
                <button
                  onClick={analyzeText}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  <Zap className="w-4 h-4" />
                  Analyze Text
                </button>
              )}
            </div>

            {/* Loading State */}
            {isAnalyzing && (
              <div className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg">
                <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                <span className="text-gray-300">Analyzing text...</span>
              </div>
            )}

            {/* Research Links */}
            {analysisContent && selectedText && (
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                  <ExternalLink className="w-4 h-4" />
                  Research & Media Links
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleResearchLink('youtube')}
                    className="flex items-center gap-2 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
                  >
                    <Youtube className="w-4 h-4" />
                    YouTube
                  </button>
                  <button
                    onClick={() => handleResearchLink('jstor-exact')}
                    className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                  >
                    <FileText className="w-4 h-4" />
                    JSTOR (Exact)
                  </button>
                  <button
                    onClick={() => handleResearchLink('jstor-passage')}
                    className="flex items-center gap-2 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
                  >
                    <FileText className="w-4 h-4" />
                    JSTOR (Passage)
                  </button>
                  <button
                    onClick={() => handleResearchLink('scholar')}
                    className="flex items-center gap-2 px-3 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded text-sm transition-colors"
                  >
                    <Globe className="w-4 h-4" />
                    Google Scholar
                  </button>
                  <button
                    onClick={() => handleResearchLink('internet-shakespeare')}
                    className="flex items-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm transition-colors col-span-2"
                  >
                    <BookOpen className="w-4 h-4" />
                    Internet Shakespeare Editions
                  </button>
                </div>
              </div>
            )}

            {/* Follow-up Question */}
            {analysisContent && !analysisContent.error && (
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Ask a Follow-up Question
                </h3>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={followUpQuestion}
                    onChange={(e) => setFollowUpQuestion(e.target.value)}
                    placeholder="Ask a question about this analysis..."
                    className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                    onKeyPress={(e) => e.key === 'Enter' && handleFollowUp()}
                  />
                  <button
                    onClick={handleFollowUp}
                    disabled={!followUpQuestion.trim() || isFollowUpLoading}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded transition-colors"
                  >
                    {isFollowUpLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </button>
                </div>
                {followUpResponse && (
                  <div className="mt-3 p-3 bg-blue-900/20 border border-blue-700/30 rounded">
                    <div 
                      className="text-sm text-gray-200 leading-relaxed"
                      dangerouslySetInnerHTML={{ __html: followUpResponse }}
                    />
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default AnalysisPanel
