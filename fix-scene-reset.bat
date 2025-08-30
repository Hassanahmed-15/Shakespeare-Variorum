@echo off
echo Fixing scene reset issue...
git add .
git commit -m "Fix scene reset issue - Prevent useEffect from resetting scene to Act 1 Scene 1 - Add initialSceneSet state to track if initial scene was set - Only set initial scene once when play is first selected - Fix dependency array to prevent unnecessary re-runs - Reset initialSceneSet when going back to library"
git push origin main
echo Scene reset fix pushed!
pause
