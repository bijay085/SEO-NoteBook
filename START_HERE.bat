@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "ROOT=%CD%"
set "PLUGIN=%ROOT%\plugins\seo-helper"
set "KB=%PLUGIN%\knowledge\SEO_Action_Decision_System.html"
set "GPT_INSTRUCTIONS=%TEMP%\seo-helper-gpt-instructions.txt"

title SEO Helper Setup

:validate
cls
echo SEO Helper
echo ==========
echo.
echo Checking the plugin...
echo.
python "%PLUGIN%\scripts\maintain.py" validate
if errorlevel 1 goto validation_failed

echo.
echo OK. SEO Helper is ready.
echo.

:menu
echo What do you want to use?
echo.
echo   1. Claude Code plugin
echo   2. ChatGPT Custom GPT
echo   3. Codex / local skills
echo   4. Update this repo
echo   5. Validate only
echo   0. Exit
echo.
set /p choice="Choose 1, 2, 3, 4, 5, or 0: "

if "%choice%"=="1" goto claude
if "%choice%"=="2" goto gpt
if "%choice%"=="3" goto local
if "%choice%"=="4" goto update
if "%choice%"=="5" goto done
if "%choice%"=="0" exit /b 0
cls
echo Please choose a number from the menu.
echo.
goto menu

:claude
cls
echo Claude Code Setup
echo =================
echo.
echo Claude Code requires one install command inside Claude.
echo I copied it to your clipboard:
echo.
echo /plugin install "%PLUGIN%"
echo.
echo Open Claude Code, paste it, press Enter.
echo After that, ask: Use SEO Helper for this SEO case.
echo.
<nul set /p="/plugin install "%PLUGIN%"" | clip
where claude >nul 2>nul
if not errorlevel 1 (
  echo Opening Claude Code...
  start "" claude
) else (
  echo Claude command was not found, so open Claude Code manually.
)
echo.
pause
goto menu

:gpt
cls
echo ChatGPT Custom GPT Setup
echo ========================
echo.
echo ChatGPT does not allow a local repo to install itself automatically.
echo This option removes the manual hunting:
echo.
echo 1. I will open the exact folder that contains the upload file.
echo 2. I will copy the GPT instructions to your clipboard.
echo 3. In GPT Builder, upload SEO_Action_Decision_System.html from the opened folder.
echo.
> "%GPT_INSTRUCTIONS%" echo You are SEO Helper, a practical SEO decision assistant.
>> "%GPT_INSTRUCTIONS%" echo.
>> "%GPT_INSTRUCTIONS%" echo Use the uploaded SEO_Action_Decision_System.html file as the main knowledgebase.
>> "%GPT_INSTRUCTIONS%" echo Answer the exact SEO question. Do not give generic SEO advice unless the user asks for basics.
>> "%GPT_INSTRUCTIONS%" echo Use only the relevant section. Do not read, dump, or summarize the whole knowledgebase unless needed.
>> "%GPT_INSTRUCTIONS%" echo Prefer direct decisions, checks, priorities, and next actions.
>> "%GPT_INSTRUCTIONS%" echo.
>> "%GPT_INSTRUCTIONS%" echo Default answer format:
>> "%GPT_INSTRUCTIONS%" echo Mode:
>> "%GPT_INSTRUCTIONS%" echo What:
>> "%GPT_INSTRUCTIONS%" echo Why:
>> "%GPT_INSTRUCTIONS%" echo How:
>> "%GPT_INSTRUCTIONS%" echo Evidence:
>> "%GPT_INSTRUCTIONS%" echo Priority:
>> "%GPT_INSTRUCTIONS%" echo.
>> "%GPT_INSTRUCTIONS%" echo If the user pastes Reddit threads, articles, notes, or files, extract only reusable decision rules. Ignore spam, insults, repeated opinions, and unsupported shortcuts.
>> "%GPT_INSTRUCTIONS%" echo If evidence is missing, say what data is needed instead of guessing. Keep answers concise and actionable.
type "%GPT_INSTRUCTIONS%" | clip
explorer /select,"%KB%"
start "" "https://chatgpt.com/gpts/editor"
echo.
echo GPT instructions are copied to clipboard.
echo The HTML knowledge file is selected in File Explorer.
echo GPT Builder is opening in your browser.
echo.
pause
goto menu

:local
cls
echo Codex / Local Skills Setup
echo ==========================
echo.
echo Installing local skills from the SEO Helper plugin...
echo.
powershell -ExecutionPolicy Bypass -File "%PLUGIN%\install-skills.ps1"
if errorlevel 1 (
  echo.
  echo Local skill install had a problem. The plugin itself is still valid.
  pause
  goto menu
)
echo.
echo Local skills installed. Testing again...
python "%PLUGIN%\scripts\maintain.py" validate
if errorlevel 1 goto validation_failed
echo.
echo Done. In Codex, ask: Use seo-router for this SEO case.
echo.
pause
goto menu

:update
cls
echo Updating SEO Helper
echo ===================
echo.
git pull
if errorlevel 1 (
  echo.
  echo Update failed. Check Git or internet, then try again.
  pause
  goto menu
)
echo.
echo Re-checking after update...
python "%PLUGIN%\scripts\maintain.py" validate
if errorlevel 1 goto validation_failed
echo.
echo Updated and validated.
echo.
pause
goto menu

:done
echo.
echo Validation passed. Nothing else needed.
echo.
pause
exit /b 0

:validation_failed
echo.
echo SEO Helper is not ready yet.
echo.
echo Most common fix: install Python 3, then run START_HERE.bat again.
echo Plugin folder:
echo %PLUGIN%
echo.
pause
exit /b 1
