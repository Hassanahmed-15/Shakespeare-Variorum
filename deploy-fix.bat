@echo off
echo Fixing deployment issues...
git add .
git commit -m "Fix deployment issues - CSS import order and Netlify config"
git push origin main
echo Done!
pause
