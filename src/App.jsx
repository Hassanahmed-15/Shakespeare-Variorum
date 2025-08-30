import React, { useState } from 'react'
import { NotesProvider } from './context/NotesContext'
import LibraryPanel from './components/LibraryPanel'
import ReaderPanel from './components/ReaderPanel'
import AnalysisPanel from './components/AnalysisPanel'
import { BookOpen, Sparkles } from 'lucide-react'

function App() {
  const [selectedPlay, setSelectedPlay] = useState('')
  const [selectedText, setSelectedText] = useState('')

  const handleSelectPlay = (playId) => {
    setSelectedPlay(playId)
    setSelectedText('')
  }

  const handleBackToLibrary = () => {
    setSelectedPlay('')
    setSelectedText('')
  }

  return (
    <NotesProvider>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        {/* Header */}
        <header className="bg-gray-800/50 border-b border-gray-700 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">Shakespeare Digital Variorum</h1>
                  <p className="text-sm text-gray-400">
                    {selectedPlay ? `${selectedPlay.charAt(0).toUpperCase() + selectedPlay.slice(1)} • Scholarly Edition` : 'Select a Play'}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-400">Database Connected</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        {!selectedPlay ? (
          <LibraryPanel onSelectPlay={handleSelectPlay} />
        ) : (
          <main className="flex h-[calc(100vh-4rem)]">
            {/* Reader Panel - Takes up most of the space */}
            <div className="flex-1 border-r border-gray-700">
              <ReaderPanel 
                selectedText={selectedText}
                setSelectedText={setSelectedText}
                onBackToLibrary={handleBackToLibrary}
              />
            </div>
            
            {/* Analysis Panel - Fixed width sidebar */}
            <div className="w-96 flex-shrink-0">
              <AnalysisPanel 
                selectedText={selectedText}
                setSelectedText={setSelectedText}
              />
            </div>
          </main>
        )}

        {/* Footer */}
        <footer className="bg-gray-800/50 border-t border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between text-sm text-gray-400">
              <div className="flex items-center gap-4">
                <span>© 2024 Shakespeare Digital Variorum</span>
                <span>•</span>
                <span>Powered by AI Analysis</span>
              </div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                <span>Full Fathom Five Mode Available</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </NotesProvider>
  )
}

export default App
