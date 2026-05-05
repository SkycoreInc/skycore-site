# SkyCore blog publisher — local fallback.
# Runs claude with the generator prompt and publishes one new blog post.
# Schedule via Windows Task Scheduler to run every 2 days at 9:00 AM.

$ErrorActionPreference = "Stop"
$siteRoot   = "C:\Users\ahmad\OneDrive\Documents\SkyCore Inc\Claude\site"
$promptFile = Join-Path $siteRoot "blog\GENERATOR_PROMPT.md"
$logFile    = Join-Path $siteRoot "scripts\publish.log"

"=== $(Get-Date -Format o) — starting publish ===" | Out-File -FilePath $logFile -Append

try {
    $promptText = Get-Content -Path $promptFile -Raw
    Push-Location $siteRoot

    # Requires `claude` CLI on PATH. Headless print mode, auto-approved edits.
    claude --print --permission-mode acceptEdits $promptText 2>&1 |
        Out-File -FilePath $logFile -Append

    "=== $(Get-Date -Format o) — publish complete ===" | Out-File -FilePath $logFile -Append
} catch {
    "=== $(Get-Date -Format o) — ERROR: $_ ===" | Out-File -FilePath $logFile -Append
    throw
} finally {
    Pop-Location
}
