@echo off
echo Fixing scene rendering issues...
git add .
git commit -m "Fix scene rendering - Add useMemo for scene content calculation - Add forceUpdate state for re-rendering - Add useEffect to monitor scene changes - Add key prop to force complete re-render - Fix timing issues with scene content updates"
git push origin main
echo Scene rendering fix pushed!
pause
