@echo off
setlocal

cd /d "%~dp0"

echo SEO Helper
echo ==========
echo.
echo This folder is ready.
echo Plugin path:
echo %CD%\plugins\seo-helper
echo.
echo Testing the local SEO router...
echo.
python plugins\seo-helper\server\seo_router_server.py --self-test
if errorlevel 1 (
  echo.
  echo Test did not run. Make sure Python is installed, then run this file again.
  echo Plugin files are still here:
  echo %CD%\plugins\seo-helper
  pause
  exit /b 1
)

echo.
echo OK. SEO Helper is working locally.
echo.
echo To install in Claude Code, paste this inside Claude Code:
echo /plugin install %CD%\plugins\seo-helper
echo.
echo To use in ChatGPT or Claude Project, upload:
echo %CD%\plugins\seo-helper\skills\seo-router
echo %CD%\plugins\seo-helper\knowledge\SEO_Action_Decision_System.html
echo.
pause