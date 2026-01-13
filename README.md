# 🕷️ AI-Powered Universal Web Crawler

LLM 기반 범용 웹 크롤러 - 자연어로 요청하면 어떤 웹페이지든 자동으로 크롤링합니다.

## ✨ 주요 기능

- 🌐 **범용 크롤링**: 모든 웹페이지 구조 자동 분석
- 🤖 **LLM 통합**: OpenAI API로 지능형 CSS Selector 생성 (코드 변경 X)
- 🔗 **브라우저 연결**: 이미 열린 브라우저에 연결 가능 (CDP)
- 💬 **자연어 요청**: "게시판의 제목과 작성자를 수집해줘" 같은 요청 가능
- ⚡ **속도 조절**: 아이템/페이지 딜레이 설정으로 서버 부하 방지
- 🔍 **DOM 구조 뷰어**: F12처럼 페이지 구조 분석
- 🎮 **브라우저 원격 제어**: 뒤로/앞으로/JavaScript 실행
- 📊 **다양한 출력**: JSON, CSV, Excel 형식 지원
- 📄 **페이지네이션**: 여러 페이지 자동 수집
- 🖥️ **GUI 지원**: 사용하기 쉬운 인터페이스
- 💻 **CLI 지원**: 스크립트 자동화 가능
- 📦 **실행파일 빌드**: PyInstaller로 exe 생성

## 설치 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

## 사용 방법

### 1. 설정

`config.json` 파일 생성:
```json
{
  "openai_api_key": "your-api-key-here",
  "default_model": "gpt-4-turbo-preview"
}
```

### 2. 실행

```bash
# GUI 모드
python main.py

# CLI 모드
python main.py --cli
```

### 3. 실행파일 빌드

```bash
pyinstaller build.spec
# dist/crawler.exe 생성됨
```

## 💡 작동 원리

**중요**: LLM이 코드를 수정하는 것이 아닙니다!

```
1. 사용자 요청 (자연어)
   "게시판의 제목, 작성자를 수집해줘"

2. LLM이 CSS Selector 생성
   {
     "container": ".post-item",
     "fields": [
       {"name": "title", "selector": ".title"},
       {"name": "author", "selector": ".author"}
     ]
   }

3. 고정된 추출 로직이 실행
   생성된 selector로 안전하게 데이터 추출
```

✅ 더 안전하고 안정적인 방식!

자세한 내용: [HOW_IT_WORKS.md](HOW_IT_WORKS.md)

## 🎯 사용 예시

1. **게시판 크롤링**
   - 요청: "게시판의 제목, 작성자, 날짜를 모두 수집해줘"
   - 결과: LLM이 자동으로 CSS selector 생성 → 데이터 추출

2. **상품 목록 크롤링 (속도 조절)**
   - 요청: "상품명, 가격, 평점을 수집해줘"
   - 설정: 아이템 딜레이 0.5초, 페이지 딜레이 2초
   - 결과: 서버에 부담 없이 안정적으로 수집

3. **로그인 필요한 사이트**
   - CDP로 기존 브라우저 연결
   - 수동으로 로그인
   - 크롤러로 데이터 수집

## 아키텍처

```
User Request (자연어)
    ↓
Browser Connection (Playwright)
    ↓
DOM Extraction
    ↓
LLM Analysis (GPT-4)
    ↓
Selector Generation
    ↓
Data Extraction
    ↓
Export (JSON/CSV/Excel)
```

## 🎮 새로운 기능

### 1. 크롤링 속도 조절
- 아이템 딜레이: 각 아이템 추출 사이의 대기 시간
- 페이지 딜레이: 다음 페이지 이동 시 대기 시간
- 서버 부하 방지 및 안정적인 크롤링

### 2. DOM 구조 뷰어
- 브라우저 F12처럼 페이지 구조 분석
- HTML 복사/저장 기능
- 크롤링 전략 수립에 유용

### 3. 브라우저 원격 제어
- 뒤로/앞으로/새로고침
- JavaScript 실행
- 스크린샷 저장
- 현재 URL 확인

### 4. 기존 브라우저 연결 (CDP)
- 로그인 상태 유지
- 쿠키/세션 활용
- 더 안정적인 크롤링

## 📚 문서

- **[HOW_IT_WORKS.md](HOW_IT_WORKS.md)**: 상세 작동 원리 및 EXE 빌드 가이드
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)**: 사용 방법 및 예시
- **[README.md](README.md)**: 프로젝트 개요 (이 파일)

## 📦 EXE 파일 빌드

```bash
# Windows
build.bat

# Linux/Mac
./build.sh
```

실행파일 생성 위치: `dist/UniversalCrawler.exe` (또는 `dist/UniversalCrawler`)

자세한 내용: [HOW_IT_WORKS.md](HOW_IT_WORKS.md#-exe-파일-빌드-방법)

## ⚠️ 주의사항

1. **OpenAI API 비용**: LLM 사용으로 비용 발생 (페이지당 약 $0.01-$0.05)
2. **크롤링 에티켓**: 적절한 속도 조절 사용
3. **법적 고려사항**: 웹사이트 이용약관 및 robots.txt 확인

## 🐛 문제 해결

문제가 발생하면 [HOW_IT_WORKS.md](HOW_IT_WORKS.md#-문제-해결) 참고

## 라이센스

MIT License
