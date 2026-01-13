@echo off
chcp 65001 > nul
echo ====================================
echo 🕷️  Universal Crawler 설치 시작
echo ====================================
echo.

REM Python 버전 확인
echo [1/4] Python 버전 확인 중...
python --version
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다!
    echo.
    echo Python 3.11 또는 3.12를 설치하세요:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Python 버전 경고 (3.13의 경우)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python 버전: %PYTHON_VERSION%
echo.

REM 의존성 설치
echo [2/4] 필요한 패키지 설치 중...
echo (이 작업은 몇 분 정도 걸릴 수 있습니다)
echo.
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ⚠️  설치 중 오류가 발생했습니다.
    echo.
    echo Python 3.13을 사용 중이라면 3.11이나 3.12로 다운그레이드하세요.
    echo 또는 수동으로 설치하세요:
    echo   pip install playwright openai beautifulsoup4 lxml openpyxl
    pause
    exit /b 1
)

echo.
echo [3/4] Playwright 브라우저 설치 중...
python -m playwright install chromium

if errorlevel 1 (
    echo ⚠️  Playwright 브라우저 설치 실패
    echo 수동으로 설치하세요: python -m playwright install chromium
)

REM 설정 파일 생성
echo.
echo [4/4] 설정 파일 생성 중...
if not exist config.json (
    copy config.example.json config.json > nul
    echo ✅ config.json 파일이 생성되었습니다
    echo    OpenAI API 키를 입력하세요!
) else (
    echo ℹ️  config.json 파일이 이미 존재합니다
)

echo.
echo ====================================
echo ✅ 설치 완료!
echo ====================================
echo.
echo 다음 단계:
echo   1. config.json 파일을 열어서 OpenAI API 키 입력
echo   2. python main.py 명령으로 실행
echo.
echo 또는 GUI로 실행:
echo   python main.py
echo.
pause
