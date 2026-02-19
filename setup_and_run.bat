@echo off
chcp 65001 >nul 2>&1
title 주식 포트폴리오 대시보드 설치

echo ========================================
echo   주식 포트폴리오 대시보드
echo   초기 설치 및 실행
echo ========================================
echo.

cd /d %~dp0

:: Python 확인
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [오류] Python이 설치되어 있지 않습니다!
    echo https://www.python.org/downloads/ 에서 설치하세요.
    echo 설치 시 "Add Python to PATH" 체크 필수!
    pause
    exit /b 1
)

echo [1/3] Python 패키지 설치 중...
pip install fastapi uvicorn requests beautifulsoup4 lxml --quiet 2>nul
echo       완료!

echo.
echo [2/3] 서버 시작 중...
echo       (최초 실행 시 종목 리스트 생성에 1~2분 소요)

:: 기존 8502 포트 프로세스 종료
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8502.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo.
echo [3/3] 브라우저를 엽니다...
start http://localhost:8502

echo.
echo ========================================
echo   http://localhost:8502 에서 접속하세요
echo   이 창을 닫으면 서버가 종료됩니다.
echo ========================================
echo.

python viewer_server.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [오류] 서버 시작 실패!
    pause
)
