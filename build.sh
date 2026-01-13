#!/bin/bash
# 빌드 스크립트 (Linux/Mac)

echo "🛠️  Universal Crawler 빌드 시작..."

# 1. 의존성 확인
echo ""
echo "[1/4] 의존성 확인 중..."
pip install -r requirements.txt

# 2. Playwright 브라우저 설치
echo ""
echo "[2/4] Playwright 브라우저 설치 중..."
playwright install chromium

# 3. PyInstaller로 빌드
echo ""
echo "[3/4] 실행파일 빌드 중..."
pyinstaller build.spec

# 4. 결과 확인
echo ""
echo "[4/4] 빌드 완료!"

if [ -f "dist/UniversalCrawler" ]; then
    echo "✅ 실행파일 생성 완료: dist/UniversalCrawler"
    echo ""
    echo "실행 방법:"
    echo "  ./dist/UniversalCrawler"
    echo "  ./dist/UniversalCrawler --cli --help"
else
    echo "❌ 빌드 실패"
    exit 1
fi
