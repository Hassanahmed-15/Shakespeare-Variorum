import React, { useState, useEffect } from 'react'
import { Brain, BookOpen, MessageSquare, Loader2, Play, Sparkles } from 'lucide-react'
import { useNotes } from '../context/NotesContext'

const AnalysisPanel = ({ selectedText, analysisMode, setAnalysisMode, currentPlay, currentScene }) => {
  const [analysisContent, setAnalysisContent] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [followUpQuestion, setFollowUpQuestion] = useState('')
  const { findNotesForLine, formatNotes } = useNotes()

  // Check for notes when selected text changes
  useEffect(() => {
    if (selectedText && currentPlay && currentScene) {
      const notesData = findNotesForLine(selectedText, currentScene)
      
      if (notesData) {
        const formattedNotes = formatNotes(notesData)
        setAnalysisContent({ type: 'notes', data: formattedNotes })
      } else {
        setAnalysisContent(null)
      }
    } else {
      setAnalysisContent(null)
    }
  }, [selectedText, currentPlay, currentScene, findNotesForLine, formatNotes])

  const handleAnalyze = async () => {
    if (!selectedText) {
      alert('Please highlight some text first.')
      return
    }

    // Check if we have notes first
    const notesData = findNotesForLine(selectedText, currentScene)
    
    if (notesData && analysisMode === 'fullfathomfive') {
      // Show commentary for Full Fathom Five mode
      const formattedNotes = formatNotes(notesData)
      setAnalysisContent({ type: 'commentary', data: formattedNotes })
    } else if (notesData && (analysisMode === 'basic' || analysisMode === 'expert')) {
      // Show analysis for Basic/Expert modes (not commentary)
      await generateAIAnalysis()
    } else if (!notesData && analysisMode === 'fullfathomfive') {
      // No commentary available, show analysis with message
      await generateAIAnalysis('No commentary for this line.')
    } else {
      // Generate AI analysis for Basic/Expert modes
      await generateAIAnalysis()
    }
  }

  const generateAIAnalysis = async (noCommentaryMessage = null) => {
    setIsLoading(true)
    
    try {
      const response = await fetch('/.netlify/functions/shakespeare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: selectedText,
          level: analysisMode,
          playName: currentPlay,
          sceneName: currentScene
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.choices && data.choices[0] && data.choices[0].message) {
        const content = data.choices[0].message.content
        setAnalysisContent({ 
          type: 'analysis', 
          data: content,
          noCommentaryMessage 
        })
      } else {
        throw new Error('Invalid response format')
      }
      
    } catch (error) {
      console.error('Error generating analysis:', error)
      setAnalysisContent({ 
        type: 'error', 
        data: `Error generating analysis: ${error.message}` 
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleFollowUp = async () => {
    if (!followUpQuestion.trim()) {
      alert('Please enter a question.')
      return
    }
    
    // Implementation for follow-up questions
    console.log('Follow-up question:', followUpQuestion)
    setFollowUpQuestion('')
  }

  const getModeTitle = () => {
    switch(analysisMode) {
      case 'basic': return 'Basic Analysis'
      case 'expert': return 'Expert Analysis'
      case 'fullfathomfive': return 'Full Fathom Five Analysis'
      default: return 'Analysis'
    }
  }

  const getModeDescription = () => {
    switch(analysisMode) {
      case 'basic': return 'Clear, accessible analysis for undergraduates'
      case 'expert': return 'Comprehensive scholarly analysis with citations'
      case 'fullfathomfive': return 'Deepest analysis with commentary and sources'
      default: return 'Analysis'
    }
  }

  const formatAnalysisContent = (content) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<h4 class="text-lg font-semibold text-primary-400 mb-2">$1</h4>')
      .replace(/\n\n/g, '</p><p class="mb-3">')
      .replace(/\n/g, '<br>')
  }

  return (
    <div className="w-96 flex-shrink-0">
      <div className="card p-6 sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto">
        {/* Header */}
        <div className="mb-6 pb-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-gray-100 mb-2">
            {getModeTitle()}
          </h2>
          <p className="text-sm text-gray-400 mb-3">
            {getModeDescription()}
          </p>
          {selectedText && (
            <div className="bg-gray-800/50 p-3 rounded-lg border-l-4 border-primary-500">
              <p className="text-sm text-gray-300">
                "{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}"
              </p>
            </div>
          )}
        </div>

        {/* Mode Selector */}
        <div className="mb-6">
          <div className="flex bg-gray-800 rounded-lg p-1 gap-1">
            {['basic', 'expert', 'fullfathomfive'].map((mode) => (
              <button
                key={mode}
                onClick={() => setAnalysisMode(mode)}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
                  analysisMode === mode
                    ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                {mode === 'basic' && 'Basic'}
                {mode === 'expert' && 'Expert'}
                {mode === 'fullfathomfive' && 'Full Fathom Five'}
              </button>
            ))}
          </div>
        </div>

        {/* Analyze Button */}
        {selectedText && !isLoading && !analysisContent && (
          <div className="mb-6">
            <button
              onClick={handleAnalyze}
              className="w-full btn btn-primary flex items-center justify-center gap-2 py-3"
            >
              <Sparkles className="w-4 h-4" />
              Analyze Text
            </button>
          </div>
        )}

        {/* Content Area */}
        <div className="space-y-6">
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto mb-3" />
                <p className="text-gray-400">Generating {analysisMode} analysis...</p>
              </div>
            </div>
          )}

          {!isLoading && analysisContent && (
            <div className="animate-fade-in">
              {analysisContent.type === 'notes' && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-lg font-semibold text-gray-100 mb-3">
                    <BookOpen className="w-5 h-5 text-primary-400" />
                    📚 Scholarly Notes
                  </div>
                  <div className="text-sm text-gray-400 mb-3">
                    Line {analysisContent.data.lineNumber} from {analysisContent.data.scene}
                  </div>
                  <div className="bg-gray-800/50 p-4 rounded-lg border-l-4 border-primary-500 mb-4">
                    <strong className="text-gray-200">Original Text:</strong> "{analysisContent.data.playLine}"
                  </div>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {analysisContent.data.notes.map((note, index) => (
                      <div key={index} className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                        <div 
                          className="text-sm text-gray-200 leading-relaxed"
                          dangerouslySetInnerHTML={{ __html: note }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {analysisContent.type === 'commentary' && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-lg font-semibold text-gray-100 mb-3">
                    <BookOpen className="w-5 h-5 text-primary-400" />
                    📚 Scholarly Commentary
                  </div>
                  <div className="text-sm text-gray-400 mb-3">
                    Line {analysisContent.data.lineNumber} from {analysisContent.data.scene}
                  </div>
                  <div className="bg-gray-800/50 p-4 rounded-lg border-l-4 border-primary-500 mb-4">
                    <strong className="text-gray-200">Original Text:</strong> "{analysisContent.data.playLine}"
                  </div>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {analysisContent.data.notes.map((note, index) => (
                      <div key={index} className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                        <div 
                          className="text-sm text-gray-200 leading-relaxed"
                          dangerouslySetInnerHTML={{ __html: note }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {analysisContent.type === 'analysis' && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-lg font-semibold text-gray-100 mb-3">
                    <Brain className="w-5 h-5 text-primary-400" />
                    AI Analysis
                  </div>
                  {analysisContent.noCommentaryMessage && (
                    <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-3 mb-4">
                      <p className="text-yellow-300 text-sm">{analysisContent.noCommentaryMessage}</p>
                    </div>
                  )}
                  <div 
                    className="prose prose-invert max-w-none text-sm leading-relaxed"
                    dangerouslySetInnerHTML={{ 
                      __html: `<p class="mb-3">${formatAnalysisContent(analysisContent.data)}</p>` 
                    }}
                  />
                </div>
              )}

              {analysisContent.type === 'error' && (
                <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-4">
                  <p className="text-red-300 text-sm">{analysisContent.data}</p>
                  <button 
                    className="btn btn-primary mt-3"
                    onClick={handleAnalyze}
                  >
                    Try Again
                  </button>
                </div>
              )}
            </div>
          )}

          {!isLoading && !analysisContent && selectedText && (
            <div className="text-center py-8">
              <Brain className="w-12 h-12 text-gray-500 mx-auto mb-3" />
              <p className="text-gray-400">Click "Analyze Text" to generate analysis</p>
            </div>
          )}

          {!selectedText && (
            <div className="text-center py-8">
              <BookOpen className="w-12 h-12 text-gray-500 mx-auto mb-3" />
              <p className="text-gray-400">Highlight text or click on a line to analyze</p>
            </div>
          )}
        </div>

        {/* Media and Research Links */}
        {analysisContent && selectedText && (
          <div className="mt-6 pt-6 border-t border-gray-700">
            <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              Research & Media Links
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <button 
                className="btn btn-secondary text-xs py-2"
                onClick={() => {
                  const searchQuery = encodeURIComponent(`"${selectedText}" Shakespeare ${currentPlay} ${currentScene}`);
                  window.open(`https://www.youtube.com/results?search_query=${searchQuery}`, '_blank');
                }}
              >
                Search YouTube
              </button>
              <button 
                className="btn btn-secondary text-xs py-2"
                onClick={() => {
                  const searchQuery = encodeURIComponent(`"${selectedText}" Shakespeare`);
                  window.open(`https://www.jstor.org/action/doBasicSearch?Query=${searchQuery}`, '_blank');
                }}
              >
                Search JSTOR (Exact)
              </button>
              <button 
                className="btn btn-secondary text-xs py-2"
                onClick={() => {
                  const searchQuery = encodeURIComponent(`${selectedText} Shakespeare ${currentPlay} ${currentScene}`);
                  window.open(`https://www.jstor.org/action/doBasicSearch?Query=${searchQuery}`, '_blank');
                }}
              >
                Search JSTOR (Passage)
              </button>
              <button 
                className="btn btn-secondary text-xs py-2"
                onClick={() => {
                  const searchQuery = encodeURIComponent(`"${selectedText}" Shakespeare ${currentPlay}`);
                  window.open(`https://scholar.google.com/scholar?q=${searchQuery}`, '_blank');
                }}
              >
                Google Scholar
              </button>
              <button 
                className="btn btn-secondary text-xs py-2 col-span-2"
                onClick={() => {
                  const searchQuery = encodeURIComponent(`${selectedText} ${currentPlay}`);
                  window.open(`https://internetshakespeare.uvic.ca/Library/SLT/plays/${currentPlay?.toLowerCase()}/`, '_blank');
                }}
              >
                Internet Shakespeare Editions
              </button>
            </div>
          </div>
        )}

        {/* Follow-up Section */}
        {analysisContent && analysisContent.type === 'analysis' && (
          <div className="mt-6 pt-6 border-t border-gray-700">
            <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Ask a follow-up question
            </h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={followUpQuestion}
                onChange={(e) => setFollowUpQuestion(e.target.value)}
                placeholder="Ask a follow-up question..."
                className="input flex-1"
                onKeyPress={(e) => e.key === 'Enter' && handleFollowUp()}
              />
              <button 
                className="btn btn-primary"
                onClick={handleFollowUp}
              >
                Ask
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AnalysisPanel
