@echo off
setlocal
echo =====================================================================
echo   Building EHXSetup.exe (Native Windows Setup Wizard)
echo   Developed by Yonatan Muluken ( ETHIO HACKER X )
echo =====================================================================
echo.

where pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Installing PyInstaller...
    pip install pyinstaller
)

echo [*] Compiling installer.py into standalone EHXSetup.exe...
pyinstaller --onefile --noconsole --name EHXSetup --clean installer.py

if exist dist\EHXSetup.exe (
    echo.
    echo [SUCCESS] Standalone Windows Setup created: dist\EHXSetup.exe
    copy dist\EHXSetup.exe .\EHXSetup.exe /Y
    echo [*] Output ready: EHXSetup.exe
    echo [*] Double-click EHXSetup.exe to test your native installer!
) else (
    echo.
    echo [ERROR] Build failed. Please check pyinstaller logs.
)

pause
