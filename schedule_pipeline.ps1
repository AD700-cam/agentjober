# schedule_pipeline.ps1
# PowerShell script to register the daily AI Career Assistant automated pipeline task in Windows Task Scheduler.

$ProjectRoot = Resolve-Path "."
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$ScriptPath = Join-Path $ProjectRoot "run_pipeline.py"
$TaskName = "AICareerAssistantPipeline"

# Command to execute
$ActionCommand = "`"$PythonPath`""
$ActionArgs = "`"$ScriptPath`""

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Scheduler Setup - Windows Task Scheduler" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot"
Write-Host "Python Path:  $PythonPath"
Write-Host "Script Path:  $ScriptPath"
Write-Host "Task Name:    $TaskName"
Write-Host "Time:         Daily at 09:00 AM"

# Helper actions
if ($args[0] -eq "delete" -or $args[0] -eq "remove" -or $args[0] -eq "uninstall") {
    Write-Host "`nDeleting existing scheduled task..." -ForegroundColor Yellow
    & schtasks.exe /delete /tn $TaskName /f
    Write-Host "✅ Scheduled task '$TaskName' removed successfully." -ForegroundColor Green
    exit 0
}

# Create Scheduled Task
Write-Host "`nCreating daily scheduled task..." -ForegroundColor Yellow
& schtasks.exe /create /tn $TaskName /tr "$ActionCommand $ActionArgs" /sc daily /st 09:00 /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Success! Scheduled task '$TaskName' registered successfully." -ForegroundColor Green
    Write-Host "It is scheduled to run automatically every morning at 09:00 AM." -ForegroundColor Green
    Write-Host "To manually run the task now, execute:" -ForegroundColor Gray
    Write-Host "  schtasks /run /tn `"$TaskName`"" -ForegroundColor Gray
    Write-Host "To remove the scheduled task, execute:" -ForegroundColor Gray
    Write-Host "  .\schedule_pipeline.ps1 remove" -ForegroundColor Gray
} else {
    Write-Host "`n❌ Error: Failed to register scheduled task. Ensure you are running PowerShell with Administrator privileges if required." -ForegroundColor Red
}
