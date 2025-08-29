# Shakespeare Digital Variorum - React Frontend

A modern, professional React frontend for the Shakespeare Digital Variorum project, featuring scholarly commentary and AI analysis.

## 🚀 Features

### Modern UI/UX
- **React 18** with modern hooks and functional components
- **Tailwind CSS** for beautiful, responsive design
- **Lucide React** icons for consistent iconography
- **Glass morphism** and gradient effects
- **Smooth animations** and transitions
- **Dark theme** optimized for reading

### Enhanced Functionality
- **Improved Commentary vs Analysis Logic**:
  - **Basic & Expert modes**: Show only AI analysis, never commentary
  - **Full Fathom Five mode**: Show commentary when available, analysis with "No commentary for this line" message when not
- **Larger, more appealing analysis section** with better typography and spacing
- **Real-time text highlighting** with visual feedback
- **Responsive design** that works on all devices

### Technical Improvements
- **Context API** for state management
- **Custom hooks** for reusable logic
- **Component-based architecture** for maintainability
- **Modern build system** with Vite
- **TypeScript-ready** structure

## 🛠️ Development

### Prerequisites
- Node.js 18.x or higher
- npm or yarn

### Installation
```bash
npm install
```

### Development Server
```bash
npm run dev
```
The app will be available at `http://localhost:3000`

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## 📁 Project Structure

```
src/
├── components/          # React components
│   ├── Header.jsx      # Main header with brand and actions
│   ├── Sidebar.jsx     # Navigation and play selection
│   ├── ReaderPanel.jsx # Main content display
│   ├── AnalysisPanel.jsx # Analysis and commentary display
│   └── Footer.jsx      # Footer with attribution
├── context/            # React context providers
│   └── NotesContext.jsx # Notes data management
├── App.jsx             # Main app component
├── main.jsx            # React entry point
└── index.css           # Global styles and Tailwind imports
```

## 🎨 Design System

### Colors
- **Primary**: Blue gradient (`#0ea5e9` to `#0284c7`)
- **Background**: Dark gray (`#111827`)
- **Text**: Light gray (`#f9fafb`)
- **Accents**: Various semantic colors for different states

### Typography
- **Sans-serif**: Inter (UI elements)
- **Serif**: Source Serif 4 (play content)
- **Responsive**: Scales appropriately across devices

### Components
- **Cards**: Glass morphism with subtle borders
- **Buttons**: Gradient backgrounds with hover effects
- **Inputs**: Dark theme with focus states
- **Highlights**: Yellow-orange gradient for selected text

## 🔧 Configuration

### Vite Configuration
- React plugin for JSX support
- Public directory for static assets
- Development server on port 3000

### Tailwind Configuration
- Custom color palette
- Custom animations
- Responsive breakpoints
- Component utilities

## 🚀 Deployment

The project is configured for deployment on Netlify with:
- Build command: `npm run build`
- Publish directory: `dist`
- Environment variables for API endpoints

## 📝 Key Improvements

1. **Frontend Framework**: Migrated from vanilla HTML/CSS to React with modern tooling
2. **Commentary Logic**: Implemented the requested logic for different analysis modes
3. **UI Design**: Complete redesign with modern, professional appearance
4. **Analysis Section**: Larger, more readable design with better typography
5. **Footer**: Added the requested attribution
6. **Performance**: Optimized with modern React patterns and efficient rendering

## 🎯 Future Enhancements

- Add more plays beyond Macbeth
- Implement advanced search functionality
- Add user preferences and settings
- Enhance mobile responsiveness
- Add keyboard shortcuts
- Implement offline support

## 📄 License

Created by Brad Carson MIT 2025
