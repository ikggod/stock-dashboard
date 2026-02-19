@echo off
chcp 65001 >nul 2>&1
title 주식 대시보드 뷰어

echo ========================================
echo   주식 포트폴리오 대시보드 뷰어
echo ========================================
echo.

cd /d C:\Users\ikggo\stock-dashboard

:: 기존 8502 포트 프로세스 종료
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8502.*LISTENING"') do (
    echo 기존 서버 종료 중 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo 서버 시작 중...
echo 브라우저에서 http://localhost:8502 접속하세요
echo.
echo 종료하려면 이 창을 닫으세요.
echo ========================================

python viewer_server.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [오류] 서버 시작 실패!
    echo - Python이 설치되어 있는지 확인하세요
    echo - pip install fastapi uvicorn 실행해보세요
    pause
)
