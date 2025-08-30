import React from 'react'
import { BookOpen, Sparkles, ArrowRight } from 'lucide-react'

const LibraryPanel = ({ onSelectPlay }) => {
  const plays = [
    {
      id: 'macbeth',
      title: 'Macbeth',
      subtitle: 'The Scottish Play',
      description: 'A tragedy of ambition, power, and supernatural forces',
      year: '1606',
      acts: 5,
      scenes: 28,
      icon: '👑',
      color: 'from-purple-600 to-red-600'
    }
    // Add more plays here as they become available
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-8">
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center shadow-2xl">
            <BookOpen className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent mb-4">
            Shakespeare Digital Variorum
          </h1>
          <p className="text-xl text-gray-300 mb-2">
            Scholarly Edition with AI Analysis
          </p>
          <p className="text-gray-400">
            Select a play to begin your scholarly exploration
          </p>
        </div>

        {/* Plays Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {plays.map((play) => (
            <div
              key={play.id}
              className="group cursor-pointer"
              onClick={() => onSelectPlay(play.id)}
            >
              <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6 hover:bg-gray-800/70 hover:border-gray-600/50 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1">
                {/* Play Icon */}
                <div className="text-4xl mb-4">{play.icon}</div>
                
                {/* Play Info */}
                <div className="mb-4">
                  <h3 className="text-xl font-bold text-white mb-1">
                    {play.title}
                  </h3>
                  <p className="text-gray-400 text-sm mb-2">
                    {play.subtitle} • {play.year}
                  </p>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {play.description}
                  </p>
                </div>

                {/* Stats */}
                <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
                  <span>{play.acts} Acts</span>
                  <span>{play.scenes} Scenes</span>
                </div>

                {/* Action Button */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-blue-400 text-sm font-medium">
                    <Sparkles className="w-4 h-4" />
                    Full Fathom Five Available
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-400 transition-colors" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Coming Soon */}
        <div className="mt-12 text-center">
          <div className="bg-gray-800/30 border border-gray-700/30 rounded-xl p-6 max-w-2xl mx-auto">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">
              More Plays Coming Soon
            </h3>
            <p className="text-gray-400 text-sm">
              Hamlet, King Lear, Romeo and Juliet, and other masterpieces will be added with full scholarly commentary.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LibraryPanel
