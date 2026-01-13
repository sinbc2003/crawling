# 🕷️ AI-Powered Universal Web Crawler

LLM 기반 범용 웹 크롤러 - 자연어로 요청하면 어떤 웹페이지든 자동으로 크롤링합니다.

## 주요 기능

- 🌐 **범용 크롤링**: 모든 웹페이지 구조 자동 분석
- 🤖 **LLM 통합**: OpenAI API로 지능형 데이터 추출
- 🔗 **브라우저 연결**: 이미 열린 브라우저에 연결 가능
- 💬 **자연어 요청**: "게시판의 제목과 작성자를 수집해줘" 같은 요청 가능
- 📊 **다양한 출력**: JSON, CSV, Excel 형식 지원
- 📄 **페이지네이션**: 여러 페이지 자동 수집
- 🖥️ **GUI 지원**: 사용하기 쉬운 인터페이스

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

## 사용 예시

1. **게시판 크롤링**
   - 요청: "게시판의 제목, 작성자, 날짜를 모두 수집해줘"
   - 결과: LLM이 자동으로 해당 요소를 찾아 추출

2. **상품 목록 크롤링**
   - 요청: "상품명, 가격, 평점을 수집해줘"
   - 결과: 모든 페이지 자동 순회하며 데이터 수집

3. **뉴스 기사 크롤링**
   - 요청: "기사 제목, 본문, 작성일을 가져와줘"
   - 결과: 구조화된 데이터로 저장

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

## 라이센스

MIT License
