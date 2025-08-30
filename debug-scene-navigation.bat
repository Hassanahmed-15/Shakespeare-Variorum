@echo off
echo Adding debugging for scene navigation...
git add .
git commit -m "Add debugging for scene navigation - Add detailed logging to getSceneContent function - Add scene selection debugging - Add context setup logging - Help identify why other acts/scenes not loading"
git push origin main
echo Scene navigation debugging pushed!
pause
