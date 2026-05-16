' ============================================
' Zwift RGB Control - Silent Launcher
' Run without showing command prompt window
' ============================================

Set objFso = CreateObject("Scripting.FileSystemObject")
strProjectPath = objFso.GetParentFolderName(WScript.ScriptFullName)

' Get batch file path
strBatchFile = objFso.BuildPath(strProjectPath, "RUN.bat")

' Create shell object
Set objShell = CreateObject("WScript.Shell")

' Run the batch file hidden (0 = hidden window)
objShell.Run strBatchFile, 0, False

' Alternative: show window
' objShell.Run strBatchFile, 1, False
