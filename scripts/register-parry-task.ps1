# Registers the LarryParryGuardian scheduled task.
# Run once (as your normal user, not admin).
#
# Before running: replace {{VAULT_PATH}} in parry-scheduled-task.xml
# with your actual vault path.

$ErrorActionPreference = "Stop"

$XmlPath = "{{VAULT_PATH}}\03-projects\ml-brainclone\bus\startup\parry-scheduled-task.xml"
$TaskName = "LarryParryGuardian"

if (-not (Test-Path $XmlPath)) {
    Write-Host "ERROR: task XML not found at $XmlPath"
    exit 1
}

# Remove existing task if present (idempotent)
try {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    Write-Host "Removing existing task $TaskName..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
} catch {
    # Task didn't exist - fine
}

# Register via schtasks (accepts XML from Task Scheduler 1.4 schema)
Write-Host "Registering $TaskName from $XmlPath..."
$result = schtasks /Create /TN $TaskName /XML $XmlPath 2>&1
Write-Host $result

Write-Host ""
Write-Host "Verify with: schtasks /Query /TN $TaskName /V /FO LIST"
Write-Host "Trigger:     schtasks /Run /TN $TaskName"
Write-Host "Remove:      schtasks /Delete /TN $TaskName /F"
