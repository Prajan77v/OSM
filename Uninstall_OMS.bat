@echo off
echo Deleting OMS Sentinel from system...
del /f /q "C:\Users\Prajan\Desktop\OMS Sentinel.lnk" >nul 2>&1
echo Removing folder C:\Users\Prajan\OMS_Sentinel...
cd \
start /b "" cmd /c "timeout /t 2 /nobreak >nul & rmdir /s /q \"C:\Users\Prajan\OMS_Sentinel\""
echo OMS fully removed.
