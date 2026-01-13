@echo off
REM 빌드 스크립트 (Windows)

echo 🛠️  Universal Crawler 빌드 시작...

REM 1. 의존성 확인
echo.
echo [1/4] 의존성 확인 중...
pip install -r requirements.txt

REM 2. Playwright 브라우저 설치
echo.
echo [2/4] Playwright 브라우저 설치 중...
playwright install chromium

REM 3. PyInstaller로 빌드
echo.
echo [3/4] 실행파일 빌드 중...
pyinstaller build.spec

REM 4. 결과 확인
echo.
echo [4/4] 빌드 완료!

if exist "dist\UniversalCrawler.exe" (
    echo ✅ 실행파일 생성 완료: dist\UniversalCrawler.exe
    echo.
    echo 실행 방법:
    echo   dist\UniversalCrawler.exe
    echo   dist\UniversalCrawler.exe --cli --help
) else (
    echo ❌ 빌드 실패
    exit /b 1
)
