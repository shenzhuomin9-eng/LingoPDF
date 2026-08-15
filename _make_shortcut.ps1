$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sc = $ws.CreateShortcut("$desktop\LingoPDF.lnk")
$sc.TargetPath = Join-Path $scriptDir 'start.bat'
$sc.WorkingDirectory = $scriptDir
$sc.Description = 'LingoPDF - Batch PDF Translator'
$sc.IconLocation = Join-Path $scriptDir 'static\favicon.ico,0'
$sc.Save()
Write-Host "Shortcut created: $desktop\LingoPDF.lnk"