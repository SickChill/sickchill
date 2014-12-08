'--------------------8<----------------------
sTitle = "Batch launcher"

Set oArgs = WScript.Arguments
Set oFSO = CreateObject("Scripting.FileSystemObject")
Set oShell = CreateObject("WScript.Shell")

If oArgs.Count <> 1 Then
' Will die after 10 seconds if no one is pressing the OK button
oShell.Popup "Error: You need to supply a file path " _
& "as input parameter!", 10, sTitle, vbCritical + vbSystemModal

Wscript.Quit 1
End If

sFilePath = oArgs(0)

If Not oFSO.FileExists(sFilePath) Then
' Will die after 10 seconds if no one is pressing the OK button
oShell.Popup "Error: Batch file not found", _
10, sTitle, vbCritical + vbSystemModal

Wscript.Quit 1
End If

' add quotes around the path in case of spaces
iRC = oShell.Run("""" & sFilePath & """", 0, True)

' Return with the same errorlevel as the batch file had
Wscript.Quit iRC

'--------------------8<----------------------