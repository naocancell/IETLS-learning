' Start IELTS Master without a console window.
' Uses .venv\Scripts\pythonw.exe created by setup.bat; otherwise falls back to run.bat (with console, so errors are visible).
Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dirPath = fso.GetParentFolderName(WScript.ScriptFullName)
ws.CurrentDirectory = dirPath
pyw = dirPath & "\.venv\Scripts\pythonw.exe"
If fso.FileExists(pyw) Then
  ws.Run """" & pyw & """ """ & dirPath & "\ielts_client\app.py""", 0, False
Else
  ws.Run """" & dirPath & "\run.bat""", 1, False
End If
