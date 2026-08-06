@echo off
echo Starting 2DA GitHub Sync...

:: Add all changes (including new HTML files and python files)
git add .

:: Commit with a dynamic timestamp message
git commit -m "Automated update on %DATE% at %TIME%"

:: Push to your main branch
git push origin main

echo Sync complete!
pause