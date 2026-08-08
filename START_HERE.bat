@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "ROOT=%CD%"
set "PLUGIN=%ROOT%\plugins\seo-helper"
set "KB=%PLUGIN%\knowledge\SEO_Action_Decision_System.html"
set "GPT_INSTRUCTIONS=%TEMP%\seo-helper-gpt-instructions.txt"
set "GLOBAL_NOTE=%TEMP%\seo-helper-global-note.txt"

title SEO Helper Setup

goto validate

:write_gpt_instructions
> "%GPT_INSTRUCTIONS%" echo You are SEO Helper, a practical SEO decision assistant.
>> "%GPT_INSTRUCTIONS%"echo.
>> "%GPT_INSTRUCTIONS%" echo Use the uploaded SEO_Action_Decision_System.html file as the main knowledgebase.
>> "%GPT_INSTRUCTIONS%" echo Answer the exact SEO question. Do not give generic SEO advice unless the user asks for basics.
>> "%GPT_INSTRUCTIONS%" echo Use only the relevant section. Do not read, dump, or summarize the whole knowledgebase unless needed.
>> "%GPT_INSTRUCTIONS%" echo Prefer direct decisions, checks, priorities, and next actions.
>> "%GPT_INSTRUCTIONS%"echo.
>> "%GPT_INSTRUCTIONS%" echo Default answer format:
>> "%GPT_INSTRUCTIONS%" echo Mode:
>> "%GPT_INSTRUCTIONS%" echo What:
>> "%GPT_INSTRUCTIONS%" echo Why:
>> "%GPT_INSTRUCTIONS%" echo How:
>> "%GPT_INSTRUCTIONS%" echo Evidence:
>> "%GPT_INSTRUCTIONS%" echo Priority:
>> "%GPT_INSTRUCTIONS%"echo.
>> "%GPT_INSTRUCTIONS%" echo If the user pastes Reddit threads, articles, notes, or files, extract only reusable decision rules. Ignore spam, insults, repeated opinions, and unsupported shortcuts.
>> "%GPT_INSTRUCTIONS%" echo If evidence is missing, say what data is needed instead of guessing. Keep answers concise and actionable.
exit /b 0

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
echo What do you want?
echo.
echo   1. Recommended: Install once on this computer
echo      Choose this if you want SEO Helper available in future projects.
echo      What happens: copies SEO skills to your user-level Codex, Claude, and Cursor skill folders.
echo.
echo   2. Use only in one project or Custom GPT
echo      Choose this for ChatGPT GPT Builder, Claude Project, another account, or one-time sharing.
echo      What happens: opens/selects the single HTML knowledge file and copies ready instructions.
echo.
echo   3. Update SEO Helper everywhere
echo      Choose this after Bijay pushes new rules or fixes.
echo      What happens: runs git pull, validates, then re-syncs global skills.
echo.
echo   4. Advanced: Claude Code plugin install
echo      Choose this only if you specifically use Claude Code plugin commands.
echo      What happens: copies the /plugin install command and tries to open Claude Code.
echo.
echo   5. Check setup only
echo      Choose this if you only want to confirm the plugin works.
echo      What happens: exits after validation; nothing is installed or changed.
echo.
echo   0. Exit
echo.
set /p choice="Choose 1, 2, 3, 4, 5, or 0: "

if "%choice%"=="1" goto global
if "%choice%"=="2" goto project
if "%choice%"=="3" goto update_everywhere
if "%choice%"=="4" goto claude_plugin
if "%choice%"=="5" goto done
if "%choice%"=="0" exit /b 0
cls
echo Please choose a number from the menu.
echo.
goto menu

:global
cls
echo Global Install
echo ==============
echo.
echo This installs SEO Helper skills for this Windows user.
echo After this, supported local AI tools can use SEO Helper in any project.
echo.
echo Installing to common skill folders:
echo   %%USERPROFILE%%\.codex\skills
echo   %%USERPROFILE%%\.claude\skills
echo   %%USERPROFILE%%\.cursor\skills
echo.
powershell -ExecutionPolicy Bypass -File "%PLUGIN%\install-skills.ps1" -Targets codex,claude,cursor
if errorlevel 1 (
 echo.
  echo Global install had a problem. The repo plugin is still valid.
  pause
  goto menu
)

echo.
echo Creating global usage note...
> "%GLOBAL_NOTE%" echo SEO Helper is installed globally for this Windows user.
>> "%GLOBAL_NOTE%" echo.
>> "%GLOBAL_NOTE%" echo In new projects, ask:
>> "%GLOBAL_NOTE%" echo Use SEO Helper for this SEO case: [paste problem]
>> "%GLOBAL_NOTE%" echo.
>> "%GLOBAL_NOTE%" echo To update later, open this repo and run START_HERE.bat, then choose option 3.
notepad "%GLOBAL_NOTE%"

echo.
echo Done. For future projects, ask your AI tool:
echo.
echo Use SEO Helper for this SEO case: [paste problem]
echo.
echo Updates: run START_HERE.bat again and choose option 3.
echo.
pause
goto menu

:project
cls
echo One Project / Custom GPT
echo ========================
echo.
echo Use this when you do not want global install, or you are using a different AI account.
echo.
echo Choose project type:
echo.
echo   1. ChatGPT Custom GPT
echo   2. Claude/ChatGPT project file upload
echo   0. Back
echo.
set /p pchoice="Choose 1, 2, or 0: "
if "%pchoice%"=="1" goto gpt
if "%pchoice%"=="2" goto project_files
if "%pchoice%"=="0" goto menu
cls
echo Please choose 1, 2, or 0.
echo.
goto project

:gpt
cls
echo ChatGPT Custom GPT
echo ==================
echo.
echo ChatGPT cannot install a local plugin folder automatically.
echo I will do the practical setup helpers now:
echo.
echo - open GPT Builder
echo - select the exact knowledge file
echo - copy GPT instructions to clipboard
echo.
call :write_gpt_instructions
type "%GPT_INSTRUCTIONS%" | clip
explorer /select,"%KB%"
start "" "https://chatgpt.com/gpts/editor"
echo.
echo GPT instructions are copied.
echo Upload the selected SEO_Action_Decision_System.html file in GPT Builder.
echo.
pause
goto menu

:project_files
cls
echo Project File Upload
echo ===================
echo.
echo I selected the one file most projects need:
echo.
echo %KB%
echo.
echo Upload it to the AI project. Then tell the project:
echo Use this file as SEO Helper. Answer only from the relevant section.
echo.
call :write_gpt_instructions
type "%GPT_INSTRUCTIONS%" | clip
explorer /select,"%KB%"
echo.
echo Instructions are copied to clipboard.
echo.
pause
goto menu

:update_everywhere
cls
echo Update SEO Helper Everywhere
echo ===========================
echo.
echo Pulling latest repo changes...
echo.
git pull
if errorlevel 1 (
 echo.
  echo Update failed. Check Git or internet, then try again.
  pause
  goto menu
)
echo.
echo Validating latest files...
python "%PLUGIN%\scripts\maintain.py" validate
if errorlevel 1 goto validation_failed
echo.
echo Syncing global skills again...
powershell -ExecutionPolicy Bypass -File "%PLUGIN%\install-skills.ps1" -Targets codex,claude,cursor
if errorlevel 1 (
 echo.
  echo Repo updated and validated, but global skill sync had a problem.
  pause
  goto menu
)
echo.
echo Done. Latest SEO Helper is synced for this computer.
echo If you used a Custom GPT or project upload, upload the selected HTML file again.
echo.
pause
goto menu

:claude_plugin
cls
echo Claude Code Plugin Install
echo ==========================
echo.
echo This is for Claude Code's plugin system.
echo I copied the install command to your clipboard:
echo.
echo /plugin install "%PLUGIN%"
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
