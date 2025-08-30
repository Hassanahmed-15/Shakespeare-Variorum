@echo off
echo Fixing loading issues...
git add .
git commit -m "Fix loading issues - Update file paths and add fallbacks"
git push origin main
echo Loading fixes pushed!
pause
