@echo off
title NBA Competitor Tracker

cd /d "%~dp0"

echo ============================================
echo NBA Competitor Tracker
echo Weekly Instagram Collection
echo ============================================
echo.

python src\collect_instagram.py --mode interactive --headed

echo.
pause
