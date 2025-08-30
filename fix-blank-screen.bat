@echo off
echo Fixing blank screen issue...
git add .
git commit -m "Fix blank screen when selecting Macbeth - Move PlayViewWithContext outside App component - Fix context access issue - Add debug logging - Pass selectedPlay prop correctly"
git push origin main
echo Blank screen fix pushed!
pause
