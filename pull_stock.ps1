$ErrorActionPreference = "Stop"
$dir = "."
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }

$headers = @{
    "Client-Id" = "163276"
    "Api-Key"   = $env:OZON_API_KEY
}

function Invoke-Ozon($path, $bodyObj) {
    $body = $bodyObj | ConvertTo-Json -Depth 10
    return Invoke-RestMethod -Uri ("https://api-seller.ozon.ru" + $path) -Method Post -Headers $headers -Body $body -ContentType "application/json"
}

try {
    $resp = Invoke-Ozon "/v2/analytics/stock_on_warehouses" @{ limit = 1000; offset = 0; warehouse_type = "ALL" }
    $rows = $resp.result.rows
    Write-Host "TOTAL ROWS: $($rows.Count)"
    ($rows | ConvertTo-Json -Depth 10) | Out-File "$dir\stock_raw.json" -Encoding UTF8
    Write-Host "=== SAMPLE (first 3 rows) ==="
    $rows | Select-Object -First 3 | ConvertTo-Json -Depth 10
    Write-Host "=== FIELD NAMES ==="
    if ($rows.Count -gt 0) { $rows[0].PSObject.Properties.Name -join ", " }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    if ($_.ErrorDetails) { Write-Host $_.ErrorDetails.Message }
}
