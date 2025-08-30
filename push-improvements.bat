@echo off
echo Pushing UI/UX improvements and database changes...
git add .
git commit -m "Complete UI/UX redesign and database improvements - Added clean library interface - Switched to macbeth_notes.json database - Removed listening/playback features - Fixed analysis functionality - Simplified and streamlined interface"
git push origin main
echo All improvements pushed successfully!
pause
