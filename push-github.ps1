Write-Host "Pushing to GitHub..." -ForegroundColor Green
$env:GIT_PAGER = "cat"
git push origin main
Write-Host "Push completed!" -ForegroundColor Green
Read-Host "Press Enter to continue"
