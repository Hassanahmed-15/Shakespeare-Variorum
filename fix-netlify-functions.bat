@echo off
echo Fixing Netlify functions configuration...
echo Installing openai dependency...
npm install openai
echo Adding changes to git...
git add .
git commit -m "Fix Netlify functions deployment - Add proper functions configuration to netlify.toml - Add openai dependency for shakespeare.js function - Improve test function with CORS support - Add fallback to local development server"
git push origin main
echo Netlify functions fix pushed!
pause
