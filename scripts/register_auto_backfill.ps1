# Register auto-backfill as a Windows Task Scheduler job.
# Triggers on user logon — catches up missing dates automatically.
# Run this script ONCE (elevated/admin not required for current-user tasks).

$taskName = "SEPA Auto Backfill"
$projectRoot = Split-Path -Parent $PSScriptRoot
$batPath = Join-Path $projectRoot "scripts\auto_backfill.bat"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Refresh market data and backfill missing SEPA daily signals on logon"

Write-Host ""
Write-Host "[OK] Task '$taskName' registered successfully." -ForegroundColor Green
Write-Host "     Trigger: every time you log in to Windows"
Write-Host "     Action:  $batPath"
Write-Host ""
Write-Host "To test now:  Start-ScheduledTask -TaskName '$taskName'"
Write-Host "To remove:    Unregister-ScheduledTask -TaskName '$taskName'"
