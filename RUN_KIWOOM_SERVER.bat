@echo off
echo ============================================
echo   키움증권 OpenAPI 서버 시작
echo ============================================
echo.
echo 1. 키움증권 로그인 창이 열립니다
echo 2. 로그인하세요
echo 3. WebSocket 서버가 ws://localhost:9999 에서 실행됩니다
echo.
echo 종료: Ctrl+C
echo ============================================
echo.

python kiwoom_server.py

pause
