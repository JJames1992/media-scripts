# Start the OmniRoute scheduled task and report node processes running omniroute
Start-ScheduledTask -TaskName 'OmniRoute'
Start-Sleep -Seconds 6
Get-Process node -ErrorAction SilentlyContinue | ForEach-Object {
  $c = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
  if ($c -match 'omniroute') {
    Write-Output ("PID={0} :: {1}" -f $_.Id, $c.Substring(0, [Math]::Min(120, $c.Length)))
  }
}
