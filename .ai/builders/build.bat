@echo off
setlocal enabledelayedexpansion

echo.
echo ==================================================
echo BUILD START
echo ==================================================

:: ==================================================
:: PATHS
:: ==================================================

:: Получаем путь к папке, где лежит build.bat
set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%..\.."
set "DOCS_DIR=%ROOT%\docs"


:: ==================================================
:: PROJECT TREE
:: ==================================================

echo.
echo [1/3] Generating project structure...

:: Вариант 1: Используем tree (встроен в Windows)
tree "%ROOT%" /F /A > "%DOCS_DIR%\STRUCT.md" 2>nul

:: Вариант 2: Если хочешь красивее — можно использовать PowerShell (раскомментируй ниже)
:: powershell -NoProfile -Command "Get-ChildItem -Path '%ROOT%' -Recurse -Force | Where-Object { $_.FullName -notmatch '\\\.git|\\node_modules|\\__pycache__' } | Format-Table FullName" > "%DOCS_DIR%\STRUCT.md"

echo Generated STRUCT.md

:: ==================================================
:: PYTHON SEMANTIC SCAN
:: ==================================================

echo.
echo [2/3] Running Python semantic scan...

python "%ROOT%\.ai\builders\back\py_map.py"

if %errorlevel% neq 0 (
    echo [ERROR] Python script failed!
    pause
    exit /b 1
)

echo Python scan complete

:: ==================================================
:: TYPESCRIPT SEMANTIC SCAN
:: ==================================================

echo.
echo [3/3] Running frontend semantic scan...

npx ts-node "%ROOT%\.ai\builders\front\ts_map.ts"

if %errorlevel% neq 0 (
    echo [ERROR] TypeScript scan failed!
    pause
    exit /b 1
)

echo Frontend scan complete

echo.
echo ==================================================
echo BUILD COMPLETE
echo ==================================================

endlocal
pause