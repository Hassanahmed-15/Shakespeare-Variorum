import React from 'react'
import { BookOpen, Settings } from 'lucide-react'

const Header = ({ selectedText, analysisMode }) => {
  const handleAnalyze = () => {
    if (!selectedText) {
      alert('Please highlight some text first, then click "Analyze Text".')
      return
    }
    // This will be handled by the AnalysisPanel component
  }

  return (
    <header className="sticky top-0 z-50 glass border-b border-gray-700/50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-lg">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">
                Shakespeare Digital Variorum
              </h1>
              <p className="text-sm text-gray-400">
                Scholarly commentary meets modern technology
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button className="btn btn-secondary">
              <Settings className="w-4 h-4" />
              Settings
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleAnalyze}
              disabled={!selectedText}
            >
              <BookOpen className="w-4 h-4" />
              Analyze Text
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
