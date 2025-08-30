@echo off
echo Fixing scene navigation issues...
git add .
git commit -m "Fix scene navigation - Add proper scene selection handler with debugging - Clear selected text when changing scenes - Fix scene name display regex - Add better error handling and logging"
git push origin main
echo Scene navigation fix pushed!
pause
