@echo off
echo Fixing Netlify functions configuration...
git add .
git commit -m "Fix Netlify functions deployment - Add proper functions configuration to netlify.toml - Improve test function with CORS support - Add fallback to local development server - Fix function directory configuration"
git push origin main
echo Netlify functions fix pushed!
pause
