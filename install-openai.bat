@echo off
echo Installing openai dependency...
npm install openai
echo Adding changes to git...
git add .
git commit -m "Add openai dependency for Netlify functions - Fix missing openai package in package.json - Required for shakespeare.js function to work properly"
git push origin main
echo OpenAI dependency added and pushed!
pause
