@echo off
echo Fixing analysis functionality...
git add .
git commit -m "Fix analysis functionality - Add better error handling and debugging - Fix context updates when play is selected - Add test function button - Improve error messages and logging"
git push origin main
echo Analysis fixes pushed!
pause
