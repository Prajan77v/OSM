# OMS Sentinel - Camera Fix Script
# Right-click this file → "Run with PowerShell" (or open as Admin)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  OMS Sentinel - Camera Access Fix" -ForegroundColor Cyan  
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: System camera allow
Write-Host "[1/4] System camera access..." -ForegroundColor Yellow
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam" /v "Value" /t REG_SZ /d "Allow" /f
Write-Host "      OK" -ForegroundColor Green

# Step 2: User camera allow  
Write-Host "[2/4] User camera access..." -ForegroundColor Yellow
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam" /v "Value" /t REG_SZ /d "Allow" /f
Write-Host "      OK" -ForegroundColor Green

# Step 3: NonPackaged (Win32/Python apps) allow
Write-Host "[3/4] Desktop apps (NonPackaged) camera access..." -ForegroundColor Yellow
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\NonPackaged" /v "Value" /t REG_SZ /d "Allow" /f
Write-Host "      OK" -ForegroundColor Green

# Step 4: Remove WdmCompanionFilter from USB camera device
Write-Host "[4/4] Removing camera isolation filter (WdmCompanionFilter)..." -ForegroundColor Yellow
$regPath = "HKLM:\SYSTEM\CurrentControlSet\Enum\USB\VID_30C9&PID_00A6\01.00.00\Device Parameters"
try {
    Remove-ItemProperty -Path $regPath -Name "LowerFilters" -Force -ErrorAction Stop
    Write-Host "      Filter removed!" -ForegroundColor Green
} catch {
    # Try alternate path format
    try {
        $regPath2 = "HKLM:\SYSTEM\CurrentControlSet\Enum\USB\VID_30C9&PID_00A6&MI_00\6&FBA136A&0&0000\Device Parameters"
        Remove-ItemProperty -Path $regPath2 -Name "LowerFilters" -Force -ErrorAction Stop
        Write-Host "      Filter removed (alternate path)!" -ForegroundColor Green
    } catch {
        Write-Host "      Note: Filter not found (may already be clear)" -ForegroundColor DarkYellow
    }
}

# Restart FrameServer
Write-Host "" 
Write-Host "Restarting Camera service..." -ForegroundColor Yellow
Stop-Service FrameServer -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Start-Service FrameServer -ErrorAction SilentlyContinue
Write-Host "Done!" -ForegroundColor Green

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SUCCESS! Camera access enabled." -ForegroundColor Green
Write-Host "  Please RESTART your PC, then run OMS." -ForegroundColor White
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
