# Netlify Deployment Guide

This project is configured for seamless deployment on Netlify with Node.js 18.

## 🚀 **Deployment Settings**

### **Build Configuration**
- **Build command**: `npm run build`
- **Publish directory**: `dist`
- **Node.js version**: 18.x

### **Environment Variables**
No additional environment variables required for basic deployment.

## 📋 **Deployment Steps**

### **Option 1: Connect to GitHub (Recommended)**
1. Go to [Netlify](https://netlify.com)
2. Click "New site from Git"
3. Connect to GitHub
4. Select repository: `Hassanahmed-15/Shakespeare-Variorum`
5. Build settings will be auto-detected from `netlify.toml`
6. Click "Deploy site"

### **Option 2: Manual Configuration**
If auto-detection doesn't work:
1. **Build command**: `npm run build`
2. **Publish directory**: `dist`
3. **Node.js version**: 18

## ⚙️ **Configuration Files**

### **netlify.toml**
- Specifies Node.js version 18
- Sets build command and publish directory
- Configures redirects for SPA routing
- Preserves Netlify functions

### **package.json**
- Uses compatible dependency versions
- Specifies Node.js 18.x requirement
- Includes all necessary build scripts

### **.nvmrc**
- Ensures Node.js 18 is used during build

## 🔧 **Troubleshooting**

### **Build Fails**
1. Check build logs in Netlify dashboard
2. Ensure Node.js version is set to 18
3. Verify all dependencies are compatible

### **Functions Not Working**
1. Ensure `netlify/functions/` directory is preserved
2. Check function redirects in `netlify.toml`

### **Routing Issues**
1. Verify SPA redirect rule in `netlify.toml`
2. Check that `/*` redirects to `/index.html`

## 📁 **File Structure for Netlify**
```
├── dist/                    # Build output (publish directory)
├── Public/                  # Static assets
├── netlify/functions/       # Netlify functions
├── src/                     # React source code
├── netlify.toml            # Netlify configuration
├── package.json            # Dependencies and scripts
└── .nvmrc                  # Node.js version
```

## ✅ **Compatibility**
- ✅ Node.js 18.x (Netlify supported)
- ✅ React 18.2.0
- ✅ Vite 4.4.5
- ✅ Tailwind CSS 3.3.3
- ✅ All dependencies compatible

## 🎯 **Expected Build Time**
- **First build**: ~2-3 minutes
- **Subsequent builds**: ~1-2 minutes

## 📞 **Support**
If deployment fails, check:
1. Netlify build logs
2. Node.js version compatibility
3. Dependency conflicts
4. Build script errors
