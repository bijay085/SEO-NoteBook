@echo off
setlocal

cd /d "%~dp0"

echo SEO Helper
echo ==========
echo.
echo Plugin path:
echo %CD%\plugins\seo-helper
echo.
echo Running production validation...
echo.
python plugins\seo-helper\scripts\maintain.py validate
if errorlevel 1 (
  echo.
  echo Validation failed. Make sure Python is installed, then run this file again.
  echo Plugin files are here:
  echo %CD%\plugins\seo-helper
  pause
  exit /b 1
)

echo.
echo OK. SEO Helper is working locally.
echo.
echo Claude Code install command:
echo /plugin install %CD%\plugins\seo-helper
echo.
echo Basic custom GPT knowledge file:
echo %CD%\plugins\seo-helper\knowledge\SEO_Action_Decision_System.html
echo.
echo To update later:
echo git pull
echo python plugins\seo-helper\scripts\maintain.py validate
echo.
pause
