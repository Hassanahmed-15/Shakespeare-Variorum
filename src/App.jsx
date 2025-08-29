import React, { useState, useEffect } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ReaderPanel from './components/ReaderPanel'
import AnalysisPanel from './components/AnalysisPanel'
import Footer from './components/Footer'
import { NotesProvider } from './context/NotesContext'

function App() {
  const [selectedPlay, setSelectedPlay] = useState('')
  const [currentScene, setCurrentScene] = useState('')
  const [selectedText, setSelectedText] = useState('')
  const [analysisMode, setAnalysisMode] = useState('basic')

  return (
    <NotesProvider>
      <div className="min-h-screen bg-gray-900 flex flex-col">
        <Header 
          selectedText={selectedText}
          analysisMode={analysisMode}
        />
        
        <main className="flex-1 flex gap-6 p-6 max-w-7xl mx-auto w-full">
          <Sidebar 
            selectedPlay={selectedPlay}
            setSelectedPlay={setSelectedPlay}
            currentScene={currentScene}
            setCurrentScene={setCurrentScene}
          />
          
          <ReaderPanel 
            selectedPlay={selectedPlay}
            currentScene={currentScene}
            setSelectedText={setSelectedText}
          />
          
          <AnalysisPanel 
            selectedText={selectedText}
            analysisMode={analysisMode}
            setAnalysisMode={setAnalysisMode}
            currentPlay={selectedPlay}
            currentScene={currentScene}
          />
        </main>
        
        <Footer />
      </div>
    </NotesProvider>
  )
}

export default App
