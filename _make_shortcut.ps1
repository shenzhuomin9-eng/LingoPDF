$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$sc = $ws.CreateShortcut("$desktop\LingoPDF.lnk")
$sc.TargetPath = 'C:\Users\szm\ZCodeProject\LingoPDF\start.bat'
$sc.WorkingDirectory = 'C:\Users\szm\ZCodeProject\LingoPDF'
$sc.Description = 'LingoPDF - Batch PDF Translator'
$sc.IconLocation = 'C:\Users\szm\ZCodeProject\LingoPDF\static\favicon.ico,0'
$sc.Save()
Write-Host "Shortcut created: $desktop\LingoPDF.lnk"