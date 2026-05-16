@echo off
REM ============================================
REM Create Desktop Shortcut
REM ============================================

REM Get current directory
set "PROJECT_DIR=%~dp0"

REM Expected desktop path for current user
set "DESKTOP=%USERPROFILE%\Desktop"

REM Check if desktop exists
if not exist "%DESKTOP%" (
    echo  Error: Desktop folder not found
    pause
    exit /b 1
)

echo.
echo  Creating desktop shortcut...
echo.

REM Create VBS script to make shortcut (VBS is more reliable than PowerShell for this)
(
    echo Set objShell = CreateObject("WScript.Shell"^)
    echo Set objLink = objShell.CreateShortcut("%DESKTOP%\Zwift RGB Control.lnk"^)
    echo objLink.TargetPath = "%PROJECT_DIR%RUN.bat"
    echo objLink.WorkingDirectory = "%PROJECT_DIR%"
    echo objLink.Description = "Zwift RGB Controller - Start averaging power to Tuya lights"
    @REM echo objLink.IconLocation = "C:\Windows\System32\shell32.dll, 107"
    echo objLink.IconLocation = "%PROJECT_DIR%icon.ico, 0"
    echo objLink.Save
    echo WScript.Echo "Shortcut created!"
) > "%TEMP%\create_shortcut.vbs"

REM Run the VBS script
cscript "%TEMP%\create_shortcut.vbs"

REM Clean up temp file
del "%TEMP%\create_shortcut.vbs"

echo.
echo  ✅ Desktop shortcut created!
echo  📍 Location: %DESKTOP%\🚴 Zwift RGB Control.lnk
echo.
echo  You can now click the shortcut to start the app anytime!
echo.
pause
