// Shakespeare Digital Variorum - Modern App
// Enhanced functionality with bug fixes and improved UX

class ShakespeareApp {
    constructor() {
        this.selectedText = '';
        this.currentPlay = '';
        this.currentScene = '';
        this.currentAnalysisMode = 'basic';
        this.analysisInProgress = false;
        this.notesIntegration = null;
        this.macbethData = null;
        
        this.init();
    }

    async init() {
        console.log('🎭 Shakespeare Digital Variorum - Modern Edition');
        
        // Initialize notes integration
        this.notesIntegration = new NotesIntegration();
        await this.notesIntegration.loadNotes();
        
        // Load Macbeth data for navigation
        await this.loadMacbethData();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Set up keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        console.log('✅ App initialized successfully');
    }

    async loadMacbethData() {
        try {
            const response = await fetch('/Public/Data/macbeth_notes.json');
            if (response.ok) {
                this.macbethData = await response.json();
                console.log('📚 Macbeth data loaded successfully');
            }
        } catch (error) {
            console.error('❌ Error loading Macbeth data:', error);
        }
    }

    setupEventListeners() {
        // Text selection handling
        document.addEventListener('mouseup', this.handleTextSelection.bind(this));
        
        // Click outside to clear highlighting
        document.addEventListener('click', this.handleClickOutside.bind(this));
        
        // Add animation classes
        this.addAnimationClasses();
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Ctrl/Cmd + Enter to analyze
            if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                event.preventDefault();
                this.explainHighlighted();
            }
            
            // Escape to close modals
            if (event.key === 'Escape') {
                this.closeSettings();
            }
        });
    }

    addAnimationClasses() {
        // Add fade-in animations to main elements
        const elements = document.querySelectorAll('.sidebar, .reader-panel, .analysis-panel');
        elements.forEach((el, index) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                el.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    handleTextSelection() {
        const selection = window.getSelection();
        const newSelectedText = selection.toString().trim();
        
        if (newSelectedText && newSelectedText.length > 0) {
            this.selectedText = newSelectedText;
            this.highlightSelectedText();
            this.checkForNotes();
        } else {
            this.clearHighlighting();
        }
    }

    handleClickOutside(event) {
        if (!event.target.closest('.reader-panel') && !event.target.closest('.analysis-panel')) {
            this.clearHighlighting();
        }
    }

    highlightSelectedText() {
        this.clearHighlighting();
        
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            const span = document.createElement('span');
            span.className = 'highlight';
            range.surroundContents(span);
        }
    }

    clearHighlighting() {
        const highlights = document.querySelectorAll('.highlight');
        highlights.forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
            parent.normalize();
        });
    }

    async checkForNotes() {
        if (!this.notesIntegration || !this.notesIntegration.isLoaded) {
            return false;
        }

        // Set context for notes integration
        this.notesIntegration.setContext(this.currentPlay, this.currentScene);
        
        // Find notes for the selected text
        const notesData = this.notesIntegration.findNotesForLine(this.selectedText);
        
        if (notesData) {
            // Display notes
            this.displayNotes(notesData);
            return true;
        } else {
            // No notes found, hide notes container
            document.getElementById('notesContainer').style.display = 'none';
            return false;
        }
    }

    displayNotes(notesData) {
        const notesContainer = document.getElementById('notesContainer');
        const formattedNotes = this.notesIntegration.formatNotes(notesData);
        
        if (formattedNotes) {
            notesContainer.innerHTML = formattedNotes;
            notesContainer.style.display = 'block';
            notesContainer.classList.add('fade-in');
            
            // Hide AI analysis when showing notes
            document.getElementById('aiAnalysisContainer').style.display = 'none';
            document.getElementById('followUpSection').style.display = 'none';
        }
    }

    loadSelectedPlay() {
        const selector = document.getElementById('playSelector');
        const selectedValue = selector.value;
        
        if (selectedValue === 'macbeth') {
            this.currentPlay = 'Macbeth';
            this.loadMacbeth();
        } else {
            this.showEmptyState();
        }
    }

    showEmptyState() {
        document.getElementById('readerContent').innerHTML = `
            <div class="empty-state fade-in">
                <div class="empty-state-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                    </svg>
                </div>
                <h3>Select a Play</h3>
                <p>Choose a play from the library to begin reading.</p>
            </div>
        `;
    }

    loadMacbeth() {
        // Update navigation
        this.updateNavigation();
        
        // Load first scene
        this.loadScene('ACT 1, SCENE 1');
    }

    updateNavigation() {
        const navList = document.getElementById('navigationList');
        
        // Macbeth acts and scenes
        const macbethStructure = {
            'ACT 1': ['SCENE 1', 'SCENE 2', 'SCENE 3', 'SCENE 4', 'SCENE 5', 'SCENE 6', 'SCENE 7'],
            'ACT 2': ['SCENE 1', 'SCENE 2', 'SCENE 3', 'SCENE 4'],
            'ACT 3': ['SCENE 1', 'SCENE 2', 'SCENE 3', 'SCENE 4', 'SCENE 5', 'SCENE 6'],
            'ACT 4': ['SCENE 1', 'SCENE 2', 'SCENE 3'],
            'ACT 5': ['SCENE 1', 'SCENE 2', 'SCENE 3', 'SCENE 4', 'SCENE 5', 'SCENE 6', 'SCENE 7', 'SCENE 8']
        };
        
        let navHTML = '';
        
        Object.keys(macbethStructure).forEach(act => {
            navHTML += `<li class="nav-item">
                <a href="#" class="nav-link" onclick="app.loadAct('${act}')">${act}</a>
            </li>`;
            
            macbethStructure[act].forEach(scene => {
                const sceneKey = `${act}, ${scene}`;
                navHTML += `<li class="nav-item nav-subitem">
                    <a href="#" class="nav-link" onclick="app.loadScene('${sceneKey}')">${scene}</a>
                </li>`;
            });
        });
        
        navList.innerHTML = navHTML;
    }

    loadScene(sceneName) {
        this.currentScene = sceneName;
        
        // Update active navigation
        this.updateActiveNavigation(sceneName);
        
        // Load scene content from macbeth_notes.json
        this.loadSceneContent(sceneName);
    }

    loadSceneContent(sceneName) {
        if (!this.macbethData || !this.macbethData[sceneName]) {
            this.showSceneNotFound(sceneName);
            return;
        }

        const sceneData = this.macbethData[sceneName];
        const readerContent = document.getElementById('readerContent');
        
        let sceneHTML = `
            <div class="scene-header fade-in">
                <h1 class="scene-title">${sceneName}</h1>
                <p class="scene-meta">Macbeth • ${sceneName}</p>
            </div>
            <div class="play-content">
        `;

        // Convert scene data to play lines
        Object.keys(sceneData).forEach(lineNumber => {
            const lineData = sceneData[lineNumber];
            if (lineData && lineData.play) {
                const playText = lineData.play;
                
                // Check if it's a character name or dialogue
                if (playText.includes(':')) {
                    const [character, dialogue] = playText.split(':', 2);
                    sceneHTML += `
                        <div class="play-line fade-in">
                            <div class="character-name">${character.trim()}</div>
                            <div class="dialogue-text">${dialogue.trim()}</div>
                        </div>
                    `;
                } else {
                    // Stage direction
                    sceneHTML += `
                        <div class="stage-direction fade-in">${playText}</div>
                    `;
                }
            }
        });

        sceneHTML += `</div>`;
        readerContent.innerHTML = sceneHTML;
    }

    showSceneNotFound(sceneName) {
        const readerContent = document.getElementById('readerContent');
        readerContent.innerHTML = `
            <div class="empty-state fade-in">
                <div class="empty-state-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
                    </svg>
                </div>
                <h3>Scene Not Found</h3>
                <p>The scene "${sceneName}" could not be loaded. Please try another scene.</p>
            </div>
        `;
    }

    loadAct(actName) {
        // Show act overview
        const readerContent = document.getElementById('readerContent');
        readerContent.innerHTML = `
            <div class="scene-header fade-in">
                <h1 class="scene-title">${actName}</h1>
                <p class="scene-meta">Macbeth • ${actName} Overview</p>
            </div>
            <div class="play-content">
                <div class="empty-state">
                    <h3>${actName}</h3>
                    <p>Click on a scene in the navigation to read the play text.</p>
                </div>
            </div>
        `;
    }

    updateActiveNavigation(sceneName) {
        // Remove all active classes
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Add active class to current scene
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.textContent === sceneName.split(', ')[1]) {
                link.classList.add('active');
            }
        });
    }

    setAnalysisMode(mode) {
        this.currentAnalysisMode = mode;
        
        // Update tab states
        document.querySelectorAll('.mode-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        event.target.classList.add('active');
        
        // Update analysis title
        const analysisTitle = document.querySelector('.analysis-title');
        switch(mode) {
            case 'basic':
                analysisTitle.textContent = 'Basic Analysis';
                break;
            case 'expert':
                analysisTitle.textContent = 'Expert Analysis';
                break;
            case 'fullfathomfive':
                analysisTitle.textContent = 'Full Fathom Five Analysis';
                break;
        }
    }

    async explainHighlighted() {
        if (!this.selectedText || this.selectedText.length === 0) {
            this.showError('Please highlight some text first, then click "Analyze Text".');
            return;
        }

        // Check if notes exist first
        const hasNotes = await this.checkForNotes();
        
        if (!hasNotes) {
            // No notes found, generate AI analysis
            this.generateAIAnalysis();
        }
    }

    async generateAIAnalysis() {
        if (this.analysisInProgress) return;
        
        this.analysisInProgress = true;
        
        // Show loading state
        const aiContainer = document.getElementById('aiAnalysisContainer');
        aiContainer.innerHTML = `
            <div class="loading fade-in">
                <div class="loading-spinner"></div>
                <span>Generating ${this.currentAnalysisMode} analysis...</span>
            </div>
        `;
        aiContainer.style.display = 'block';
        
        // Hide notes container
        document.getElementById('notesContainer').style.display = 'none';
        
        try {
            const response = await fetch('/.netlify/functions/shakespeare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: this.selectedText,
                    level: this.currentAnalysisMode,
                    playName: this.currentPlay,
                    sceneName: this.currentScene
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.choices && data.choices[0] && data.choices[0].message) {
                const content = data.choices[0].message.content;
                this.displayAIAnalysis(content);
            } else {
                throw new Error('Invalid response format from API');
            }
            
        } catch (error) {
            console.error('Error generating analysis:', error);
            this.handleAnalysisError(error);
        } finally {
            this.analysisInProgress = false;
        }
    }

    handleAnalysisError(error) {
        const aiContainer = document.getElementById('aiAnalysisContainer');
        let errorMessage = 'An error occurred while generating analysis.';
        
        // Provide specific error messages
        if (error.message.includes('quota') || error.message.includes('rate limit')) {
            errorMessage = 'API quota exceeded. Please wait a moment and try again, or check your OpenAI account limits.';
        } else if (error.message.includes('timeout')) {
            errorMessage = 'Analysis timeout. The request took too long to process. Try using a shorter text selection or Expert level instead of Full Fathom Five.';
        } else if (error.message.includes('API key')) {
            errorMessage = 'OpenAI API key not configured. Please check your environment variables.';
        } else if (error.message.includes('network')) {
            errorMessage = 'Network error. Please check your internet connection and try again.';
        }
        
        aiContainer.innerHTML = `
            <div class="error fade-in">
                <p>${errorMessage}</p>
                <button class="btn btn-primary" onclick="app.explainHighlighted()">Try Again</button>
            </div>
        `;
    }

    displayAIAnalysis(content) {
        const aiContainer = document.getElementById('aiAnalysisContainer');
        
        // Format the content
        const formattedContent = this.formatAnalysisContent(content);
        
        aiContainer.innerHTML = `
            <div class="ai-analysis-content fade-in">
                ${formattedContent}
            </div>
        `;
        
        // Show follow-up section
        document.getElementById('followUpSection').style.display = 'block';
    }

    formatAnalysisContent(content) {
        // Enhanced formatting for better readability
        return content
            .replace(/\*\*(.*?)\*\*/g, '<h4>$1</h4>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/<p><\/p>/g, '') // Remove empty paragraphs
            .replace(/^/, '<p>') // Start with paragraph
            .replace(/$/, '</p>'); // End with paragraph
    }

    async askFollowUp() {
        const question = document.getElementById('followUpQuestion').value.trim();
        if (!question) {
            this.showError('Please enter a question.');
            return;
        }
        
        // Implementation for follow-up questions
        console.log('Follow-up question:', question);
        // This would call the AI function with the follow-up question
    }

    showError(message) {
        // Create a temporary error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error fade-in';
        errorDiv.style.position = 'fixed';
        errorDiv.style.top = '20px';
        errorDiv.style.right = '20px';
        errorDiv.style.zIndex = '1000';
        errorDiv.style.maxWidth = '300px';
        errorDiv.innerHTML = `<p>${message}</p>`;
        
        document.body.appendChild(errorDiv);
        
        // Remove after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    openSettings() {
        document.getElementById('settingsModal').style.display = 'block';
    }

    closeSettings() {
        document.getElementById('settingsModal').style.display = 'none';
    }
}

// Global app instance
let app;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    app = new ShakespeareApp();
});

// Global functions for HTML onclick handlers
function loadSelectedPlay() {
    app.loadSelectedPlay();
}

function loadScene(sceneName) {
    app.loadScene(sceneName);
}

function loadAct(actName) {
    app.loadAct(actName);
}

function setAnalysisMode(mode) {
    app.setAnalysisMode(mode);
}

function explainHighlighted() {
    app.explainHighlighted();
}

function askFollowUp() {
    app.askFollowUp();
}

function openSettings() {
    app.openSettings();
}

function closeSettings() {
    app.closeSettings();
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('settingsModal');
    if (event.target === modal) {
        closeSettings();
    }
}
