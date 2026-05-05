# One-time setup: register the scheduled task with Windows Task Scheduler.
# Runs publish-blog.ps1 every 2 days at 9:00 AM.
# Usage: open PowerShell as admin, cd to this folder, run: .\install-task.ps1

$ErrorActionPreference = "Stop"

$taskName   = "SkyCore-Blog-Every-2-Days"
$scriptPath = "C:\Users\ahmad\OneDrive\Documents\SkyCore Inc\Claude\site\scripts\publish-blog.ps1"

$action   = New-ScheduledTaskAction -Execute "powershell.exe" `
            -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

$trigger  = New-ScheduledTaskTrigger -Daily -DaysInterval 2 `
            -At (Get-Date "09:00:00")

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
            -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
            -WakeToRun

# Remove any previous registration
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask -TaskName $taskName `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "Publishes one SkyCore blog post every 2 days via Claude Code." `
    -RunLevel Highest

Write-Host "Scheduled task '$taskName' installed. First run: next trigger at 09:00."
Write-Host "Check status with: Get-ScheduledTask -TaskName $taskName"
