import React from 'react'
import { Library, Navigation } from 'lucide-react'
import { useNotes } from '../context/NotesContext'

const Sidebar = ({ selectedPlay, setSelectedPlay, currentScene, setCurrentScene }) => {
  const { setCurrentPlay, setCurrentScene: setNotesScene } = useNotes()

  const handlePlayChange = (playName) => {
    setSelectedPlay(playName)
    setCurrentPlay(playName)
    
    if (playName === 'Macbeth') {
      // Load first scene
      const firstScene = 'ACT 1, SCENE 1'
      setCurrentScene(firstScene)
      setNotesScene(firstScene)
    } else {
      setCurrentScene('')
      setNotesScene('')
    }
  }

  const handleSceneClick = (sceneName) => {
    setCurrentScene(sceneName)
    setNotesScene(sceneName)
  }

  const macbethStructure = {
    'ACT 1': ['SCENE 1', 'SCENE 2', 'SCENE 3', 'SCENE 4', 'SCENE 5', 'SCENE 6', 'SCENE 7'],
    'ACT 2': ['SCENE 1', 'SCENE 2', 'SCENE 3', 'SCENE 4'],
    'ACT 3': ['SCENE 1', 'SCENE 2', 'SCENE 3', 'SCENE 4', 'SCENE 5', 'SCENE 6'],
    'ACT 4': ['SCENE 1', 'SCENE 2', 'SCENE 3'],
    'ACT 5': ['SCENE 1', 'SCENE 2', 'SCENE 3', 'SCENE 4', 'SCENE 5', 'SCENE 6', 'SCENE 7', 'SCENE 8']
  }

  return (
    <aside className="w-80 flex-shrink-0">
      <div className="card p-6 sticky top-24">
        {/* Library Section */}
        <div className="mb-8">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
            <Library className="w-4 h-4" />
            Library
          </h2>
          
          <div className="space-y-3">
            <select 
              className="input"
              value={selectedPlay}
              onChange={(e) => handlePlayChange(e.target.value)}
            >
              <option value="">Choose a Play</option>
              <option value="Macbeth">Macbeth</option>
            </select>
          </div>
        </div>

        {/* Navigation Section */}
        {selectedPlay && (
          <div>
            <h2 className="flex items-center gap-2 text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
              <Navigation className="w-4 h-4" />
              Navigation
            </h2>
            
            <nav className="space-y-1">
              {Object.entries(macbethStructure).map(([act, scenes]) => (
                <div key={act} className="space-y-1">
                  <div className="px-3 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors cursor-pointer">
                    {act}
                  </div>
                  {scenes.map((scene) => {
                    const sceneKey = `${act}, ${scene}`
                    const isActive = currentScene === sceneKey
                    
                    return (
                      <button
                        key={sceneKey}
                        onClick={() => handleSceneClick(sceneKey)}
                        className={`w-full text-left px-6 py-2 text-sm rounded-lg transition-all duration-200 ${
                          isActive
                            ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg'
                            : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                        }`}
                      >
                        {scene}
                      </button>
                    )
                  })}
                </div>
              ))}
            </nav>
          </div>
        )}
      </div>
    </aside>
  )
}

export default Sidebar
