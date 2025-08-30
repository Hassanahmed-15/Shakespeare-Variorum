import React, { useEffect, useRef, useState } from 'react'
import { BookOpen, Search, Copy, Share2 } from 'lucide-react'

const ReaderPanel = ({ selectedPlay, currentScene, setSelectedText }) => {
  const contentRef = useRef(null)
  const [selectedLine, setSelectedLine] = useState(null)
  const [showLineNumbers, setShowLineNumbers] = useState(true)

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
        { character: 'Sergeant', dialogue: 'Doubtful it stood;\nAs two spent swimmers, that do cling together\nAnd choke their art. The merciless Macdonwald—\nWorthy to be a rebel, for to that\nThe multiplying villanies of nature\nDo swarm upon him—from the western isles\nOf kerns and gallowglasses is supplied;\nAnd fortune, on his damned quarrel smiling,\nShow\'d like a rebel\'s whore: but all\'s too weak:\nFor brave Macbeth—well he deserves that name—\nDisdaining fortune, with his brandish\'d steel,\nWhich smoked with bloody execution,\nLike valour\'s minion carved out his passage\nTill he faced the slave;\nWhich ne\'er shook hands, nor bade farewell to him,\nTill he unseam\'d him from the nave to the chaps,\nAnd fix\'d his head upon our battlements.' },
        { character: 'DUNCAN', dialogue: 'O valiant cousin! worthy gentleman!' },
        { character: 'Sergeant', dialogue: 'As whence the sun \'gins his reflection\nShipwrecking storms and direful thunders break,\nSo from that spring whence comfort seem\'d to come\nDiscomfort swells. Mark, king of Scotland, mark:\nNo sooner justice had with valour arm\'d\nCompell\'d these skipping kerns to trust their heels,\nBut the Norweyan lord surveying vantage,\nWith furbish\'d arms and new supplies of men\nBegan a fresh assault.' },
        { character: 'DUNCAN', dialogue: 'Dismay\'d not this\nOur captains, Macbeth and Banquo?' },
        { character: 'Sergeant', dialogue: 'Yes;\nAs sparrows eagles, or the hare the lion.\nIf I say sooth, I must report they were\nAs cannons overcharged with double cracks, so they\nDoubly redoubled strokes upon the foe:\nExcept they meant to bathe in reeking wounds,\nOr memorise another Golgotha,\nI cannot tell.\nBut I am faint, my gashes cry for help.' },
        { character: 'DUNCAN', dialogue: 'So well thy words become thee as thy wounds;\nThey smack of honour both. Go get him surgeons.' }
      ],
      'ACT 1, SCENE 3': [
        { character: 'First Witch', dialogue: 'Where hast thou been, sister?' },
        { character: 'Second Witch', dialogue: 'Killing swine.' },
        { character: 'Third Witch', dialogue: 'Sister, where thou?' },
        { character: 'First Witch', dialogue: 'A sailor\'s wife had chestnuts in her lap,\nAnd munch\'d, and munch\'d, and munch\'d:—\'Give me,\' quoth I:\n\'Aroint thee, witch!\' the rump-fed ronyon cries.\nHer husband\'s to Aleppo gone, master o\' the Tiger:\nBut in a sieve I\'ll thither sail,\nAnd, like a rat without a tail,\nI\'ll do, I\'ll do, and I\'ll do.' },
        { character: 'Second Witch', dialogue: 'I\'ll give thee a wind.' },
        { character: 'First Witch', dialogue: 'Thou\'rt kind.' },
        { character: 'Third Witch', dialogue: 'And I another.' },
        { character: 'First Witch', dialogue: 'I myself have all the other,\nAnd the very ports they blow,\nAll the quarters that they know\nI\' the shipman\'s card.\nI will drain him dry as hay:\nSleep shall neither night nor day\nHang upon his pent-house lid;\nHe shall live a man forbid:\nWeary se\'nnights nine times nine\nShall he dwindle, peak and pine:\nThough his bark cannot be lost,\nYet it shall be tempest-tost.\nLook what I have.' },
        { character: 'Second Witch', dialogue: 'Show me, show me.' },
        { character: 'First Witch', dialogue: 'Here I have a pilot\'s thumb,\nWreck\'d as homeward he did come.' },
        { character: 'Third Witch', dialogue: 'A drum, a drum!\nMacbeth doth come.' },
        { character: 'ALL', dialogue: 'The weird sisters, hand in hand,\nPosters of the sea and land,\nThus do go about, about:\nThrice to thine and thrice to mine\nAnd thrice again, to make up nine.\nPeace! the charm\'s wound up.' }
      ],
      'ACT 1, SCENE 4': [
        { character: 'DUNCAN', dialogue: 'Is execution done on Cawdor? Are not\nThose in commission yet return\'d?' },
        { character: 'MALCOLM', dialogue: 'My liege,\nThey are not yet come back. But I have spoke\nWith one that saw him die: who did report\nThat very frankly he confess\'d his treasons,\nImplored your highness\' pardon and set forth\nA deep repentance: nothing in his life\nBecame him like the leaving it; he died\nAs one that had been studied in his death\nTo throw away the dearest thing he owed,\nAs \'twere a careless trifle.' },
        { character: 'DUNCAN', dialogue: 'There\'s no art\nTo find the mind\'s construction in the face:\nHe was a gentleman on whom I built\nAn absolute trust.\n\nEnter MACBETH, BANQUO, ROSS, and ANGUS\n\nO worthiest cousin!\nThe sin of my ingratitude even now\nWas heavy on me: thou art so far before\nThat swiftest wing of recompense is slow\nTo overtake thee. Would thou hadst less deserved,\nThat the proportion both of thanks and payment\nMight have been mine! only I have left to say,\nMore is thy due than more than all can pay.' },
        { character: 'MACBETH', dialogue: 'The service and the loyalty I owe,\nIn doing it, pays itself. Your highness\' part\nIs to receive our duties; and our duties\nAre to your throne and state children and servants,\nWhich do but what they should, by doing every thing\nSafe toward your love and honour.' },
        { character: 'DUNCAN', dialogue: 'Welcome hither:\nI have begun to plant thee, and will labour\nTo make thee full of growing. Noble Banquo,\nThat hast no less deserved, nor must be known\nNo less to have done so, let me enfold thee\nAnd hold thee to my heart.' },
        { character: 'BANQUO', dialogue: 'There if I grow,\nThe harvest is your own.' },
        { character: 'DUNCAN', dialogue: 'My plenteous joys,\nWanton in fulness, seek to hide themselves\nIn drops of sorrow. Sons, kinsmen, thanes,\nAnd you whose places are the nearest, know\nWe will establish our estate upon\nOur eldest, Malcolm, whom we name hereafter\nThe Prince of Cumberland; which honour must\nNot unaccompanied invest him only,\nBut signs of nobleness, like stars, shall shine\nOn all deservers. From hence to Inverness,\nAnd bind us further to you.' },
        { character: 'MACBETH', dialogue: 'The rest is labour, which is not used for you:\nI\'ll be myself the harbinger and make joyful\nThe hearing of my wife with your approach;\nSo humbly take my leave.' },
        { character: 'DUNCAN', dialogue: 'My worthy Cawdor!' },
        { character: 'MACBETH', dialogue: '[Aside] The Prince of Cumberland! that is a step\nOn which I must fall down, or else o\'erleap,\nFor in my way it lies. Stars, hide your fires;\nLet not light see my black and deep desires:\nThe eye wink at the hand; yet let that be,\nWhich the eye fears, when it is done, to see.' },
        { character: 'DUNCAN', dialogue: 'True, worthy Banquo; he is full so valiant,\nAnd in his commendations I am fed;\nIt is a banquet to me. Let\'s after him,\nWhose care is gone before to bid us welcome:\nIt is a peerless kinsman.' }
      ],
      'ACT 1, SCENE 5': [
        { character: 'LADY MACBETH', dialogue: 'They met me in the day of success: and I have\nlearned by the perfectest report, they have more in\nthem than mortal knowledge. When I burned in desire\nto question them further, they made themselves air,\ninto which they vanished. Whiles I stood rapt in\nthe wonder of it, came missives from the king, who\nall-hailed me \'Thane of Cawdor;\' by which title,\nbefore, these weird sisters saluted me, and referred\nme to the coming on of time, with \'Hail, king that\nshalt be!\' This have I thought good to deliver\nthee, my dearest partner of greatness, that thou\nmightst not lose the dues of rejoicing, by being\nignorant of what greatness is promised thee. Lay it\nto thy heart, and farewell.\n\nGlamis thou art, and Cawdor; and shalt be\nWhat thou art promised: yet do I fear thy nature;\nIt is too full o\' the milk of human kindness\nTo catch the nearest way: thou wouldst be great;\nArt not without ambition, but without\nThe illness should attend it: what thou wouldst highly,\nThat thou wouldst holily; wouldst not play false,\nAnd yet wouldst wrongly win: thou\'ldst have, great\nGlamis, that which cries \'Thus thou must do, if thou\nhave it;\' and that which rather thou dost fear to do\nThan wishest should be undone. Hie thee hither,\nThat I may pour my spirits in thine ear;\nAnd chastise with the valour of my tongue\nAll that impedes thee from the golden round,\nWhich fate and metaphysical aid doth seem\nTo have thee crown\'d withal.' }
      ]
    }

    return macbethText[sceneName] || [
      { character: 'Narrator', dialogue: `Content for ${sceneName} is being prepared. This scene will be available soon with full text and scholarly notes.` }
    ]
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    // You could add a toast notification here
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
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold gradient-text">
              {currentScene}
            </h1>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowLineNumbers(!showLineNumbers)}
                className="btn btn-ghost text-sm"
                title="Toggle line numbers"
              >
                <Search className="w-4 h-4" />
              </button>
            </div>
          </div>
          <p className="text-gray-400">
            {selectedPlay} • {currentScene}
          </p>
        </div>

        {/* Play Content */}
        <div className="space-y-4 font-serif text-lg leading-relaxed">
          {sceneContent.map((line, index) => (
            <div 
              key={index}
              className="group p-4 rounded-lg bg-gray-800/50 border border-gray-700 hover:bg-gray-800 hover:border-gray-600 transition-all duration-200 cursor-pointer"
              onClick={() => {
                setSelectedLine(line)
                setSelectedText(line.dialogue)
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="font-sans font-semibold text-primary-400 uppercase tracking-wide text-sm mb-2">
                    {line.character}
                  </div>
                  <div className="text-gray-100 leading-relaxed select-text">
                    {line.dialogue.split('\n').map((text, i) => (
                      <div key={i} className="mb-2 last:mb-0">
                        {text}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      copyToClipboard(line.dialogue)
                    }}
                    className="btn btn-ghost text-xs p-1"
                    title="Copy text"
                  >
                    <Copy className="w-3 h-3" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      shareText(line.dialogue)
                    }}
                    className="btn btn-ghost text-xs p-1"
                    title="Share text"
                  >
                    <Share2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Instructions */}
        <div className="mt-8 p-4 bg-blue-900/20 border border-blue-700/50 rounded-lg">
          <p className="text-blue-300 text-sm">
            💡 <strong>Tip:</strong> Click on any line to select it for analysis, or highlight specific text to analyze.
          </p>
        </div>
      </div>
    </div>
  )
}

export default ReaderPanel
