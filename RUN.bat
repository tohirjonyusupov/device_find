@echo off
title DeviceGuard
cd /d "%~dp0"

echo.
echo  ====================================
echo   DeviceGuard - Ishga tushirish
echo  ====================================
echo.

:: venv tekshirish / o'rnatish
if not exist "backend\venv\Scripts\python.exe" (
    echo  [1/2] Paketlar o'rnatilmoqda...
    cd backend
    python -m venv venv
    venv\Scripts\pip install -r requirements.txt --quiet
    cd ..
    echo  [OK] O'rnatish tugadi.
    echo.
)

:: Backend (yangi oynada)
start "Backend :8000" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn main:app --reload --port 8000"

:: Frontend (yangi oynada) — short path ishlatiladi (spaces muammosi)
timeout /t 3 /nobreak >nul
for %%I in ("%~dp0frontend") do set FEDIR=%%~sI
start "Frontend :5500" cmd /k "python -m http.server 5500 --directory %FEDIR%"

:: Brauzer
timeout /t 2 /nobreak >nul
start "" "http://localhost:5500/index.html"

echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5500
echo  API Docs: http://localhost:8000/docs
echo.
echo  Oynalarni yopish orqali to'xtatiladi.
pause
