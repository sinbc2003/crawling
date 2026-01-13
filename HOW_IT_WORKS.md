# 🔍 작동 원리 및 빌드 가이드

## 💡 LLM이 코드를 수정하는 방식인가요?

**아니요!** LLM은 코드를 수정하지 않습니다. 훨씬 더 안전하고 안정적인 방식으로 작동합니다.

### 실제 작동 방식

```
1. 사용자 요청 (자연어)
   "게시판의 제목, 작성자, 날짜를 수집해줘"

2. 페이지 HTML 추출
   현재 브라우저 페이지의 HTML 구조를 가져옵니다

3. LLM이 CSS Selector 생성 ⭐
   {
     "container_selector": ".post-item",
     "fields": [
       {"name": "title", "selector": ".post-title", "attribute": null},
       {"name": "author", "selector": ".author", "attribute": null},
       {"name": "date", "selector": ".date", "attribute": null}
     ],
     "pagination": {
       "next_button_selector": ".pagination .next"
     }
   }

4. 고정된 추출 로직이 실행
   생성된 selector를 사용하여 데이터를 추출합니다
   (코드는 변경되지 않고, selector만 동적으로 생성됨)
```

### 왜 이 방식이 더 좋은가?

| 방식 | LLM이 코드 생성 | LLM이 Selector 생성 (우리 방식) |
|------|----------------|-------------------------------|
| 안정성 | ❌ 낮음 (코드 오류 가능) | ✅ 높음 (검증된 코드) |
| 보안 | ❌ 위험 (임의 코드 실행) | ✅ 안전 (selector만 생성) |
| 예측 가능성 | ❌ 낮음 | ✅ 높음 |
| 유지보수 | ❌ 어려움 | ✅ 쉬움 |

## 🏗️ EXE 파일 빌드 방법

### 방법 1: 빌드 스크립트 사용 (권장)

#### Windows:
```bash
# 1. 저장소 클론
git clone https://github.com/your-username/crawling.git
cd crawling

# 2. 가상환경 생성 (선택사항이지만 권장)
python -m venv venv
venv\Scripts\activate

# 3. 빌드 실행
build.bat

# 4. 실행파일 확인
# dist/UniversalCrawler.exe 생성됨
```

#### Linux/Mac:
```bash
# 1. 저장소 클론
git clone https://github.com/your-username/crawling.git
cd crawling

# 2. 가상환경 생성 (선택사항이지만 권장)
python3 -m venv venv
source venv/bin/activate

# 3. 빌드 실행
chmod +x build.sh
./build.sh

# 4. 실행파일 확인
# dist/UniversalCrawler 생성됨
```

### 방법 2: 수동 빌드

```bash
# 1. 의존성 설치
pip install -r requirements.txt
playwright install chromium

# 2. PyInstaller로 빌드
pyinstaller build.spec

# 3. 실행파일 확인
# Windows: dist/UniversalCrawler.exe
# Linux/Mac: dist/UniversalCrawler
```

## 🚀 EXE 파일 사용 방법

### 1. 실행파일만 사용 (배포판)

빌드된 exe 파일은 **단독 실행 가능**합니다!

```bash
# Windows
UniversalCrawler.exe

# Linux/Mac
./UniversalCrawler
```

**중요**: 실행 시 `config.json` 파일이 필요합니다.

### 2. 설정 파일 준비

실행파일과 같은 디렉토리에 `config.json` 생성:

```json
{
  "openai_api_key": "sk-your-api-key-here",
  "default_model": "gpt-4-turbo-preview"
}
```

### 3. CLI 모드로 사용

```bash
# 기본 사용
UniversalCrawler.exe --cli \
  --url "https://example.com/board" \
  --request "게시판의 제목과 작성자를 수집해주세요"

# CDP로 기존 브라우저 연결
UniversalCrawler.exe --cli \
  --cdp-url "http://localhost:9222" \
  --request "현재 페이지의 상품 정보를 수집해주세요"

# 속도 조절하면서 크롤링
UniversalCrawler.exe --cli \
  --url "https://example.com/products" \
  --request "상품명, 가격을 가져와주세요" \
  --max-pages 10 \
  --format excel
```

### 4. GUI 모드로 사용

```bash
# 그냥 더블클릭 또는
UniversalCrawler.exe
```

## 🎮 주요 기능 상세

### 1. 크롤링 속도 조절 ⚡

서버 부하를 방지하고 안정적인 크롤링을 위한 기능입니다.

**GUI에서:**
- **아이템 딜레이**: 각 아이템 추출 사이의 대기 시간 (초)
- **페이지 딜레이**: 다음 페이지로 이동할 때의 대기 시간 (초)

**사용 예시:**
```
아이템 딜레이: 0.5초
→ 게시글 1 추출 → 0.5초 대기 → 게시글 2 추출 → ...

페이지 딜레이: 2초
→ 1페이지 완료 → 2초 대기 → 2페이지 이동 → ...
```

**권장 설정:**
- 빠른 크롤링: 아이템 0.0초, 페이지 1초
- 안정적 크롤링: 아이템 0.3초, 페이지 2초
- 매우 안정적: 아이템 0.5초, 페이지 3초

### 2. DOM 구조 뷰어 (F12 기능) 🔍

브라우저 개발자 도구(F12)처럼 페이지 구조를 분석합니다.

**기능:**
- 📊 페이지 구조 요약 (헤더, 메인, 테이블 등)
- 📋 HTML 복사 (클립보드)
- 💾 HTML 저장 (파일)
- 🔄 실시간 분석

**사용 시나리오:**
1. 크롤링할 페이지 열기
2. "DOM 구조" 탭 이동
3. "페이지 구조 분석" 클릭
4. 페이지 구조 확인하여 크롤링 전략 수립

### 3. 브라우저 원격 제어 🎮

이미 열린 브라우저를 원격으로 제어합니다.

**기능:**
- ◀◀▶ 뒤로/앞으로/새로고침
- 📸 스크린샷 저장
- 📍 현재 URL 확인
- ▶️ JavaScript 실행

**JavaScript 실행 예시:**
```javascript
// 페이지 제목 가져오기
document.title

// 모든 링크 수집
Array.from(document.querySelectorAll('a')).map(a => a.href)

// 특정 요소 클릭
document.querySelector('.load-more-button').click()

// 스크롤
window.scrollTo(0, document.body.scrollHeight)

// 데이터 추출
Array.from(document.querySelectorAll('.product')).map(p => ({
  name: p.querySelector('.name').textContent,
  price: p.querySelector('.price').textContent
}))
```

### 4. 기존 브라우저 연결 (CDP) 🔗

가장 강력한 기능 중 하나입니다!

**장점:**
- ✅ 로그인 상태 유지
- ✅ 쿠키/세션 활용
- ✅ 수동 탐색 + 자동 크롤링 조합
- ✅ 더 안정적

**사용 방법:**

1. Chrome을 디버깅 모드로 실행:

```bash
# Windows
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"

# Mac
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-debug"

# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-debug"
```

2. 크롤러에서 연결:
- GUI: "기존 브라우저 연결 (CDP)" 선택 → "브라우저 연결"
- CLI: `--cdp-url "http://localhost:9222"`

3. 이제 열린 Chrome 브라우저를 크롤러가 제어합니다!

## 🎯 실제 사용 시나리오

### 시나리오 1: 로그인이 필요한 사이트

```
1. Chrome을 CDP 모드로 실행
2. 수동으로 로그인
3. 크롤러 실행
4. 로그인 상태로 크롤링 진행
```

### 시나리오 2: 복잡한 SPA (Single Page Application)

```
1. 브라우저 원격 제어로 페이지 로딩 확인
2. JavaScript 실행으로 동적 데이터 로드
3. DOM 구조 뷰어로 구조 파악
4. 크롤링 실행
```

### 시나리오 3: 대량 데이터 수집

```
1. 속도 조절 설정 (서버 부하 방지)
   - 아이템 딜레이: 0.5초
   - 페이지 딜레이: 3초
2. 최대 페이지: 100
3. 자동 페이지네이션 활성화
4. 밤에 실행하고 아침에 확인
```

## 📦 배포 방법

### 다른 사람에게 배포

```
배포 패키지 구성:
📁 UniversalCrawler/
  ├── UniversalCrawler.exe (또는 실행파일)
  ├── config.example.json
  └── README.md (간단한 사용 설명)
```

**사용자가 해야 할 일:**
1. `config.example.json`을 `config.json`으로 복사
2. OpenAI API 키 입력
3. 실행파일 더블클릭

## ⚠️ 주의사항

### 1. OpenAI API 비용

LLM을 사용하므로 OpenAI API 비용이 발생합니다.

**비용 예시 (gpt-4-turbo-preview 기준):**
- 페이지 분석 1회: 약 $0.01 ~ $0.05
- 게시판 100개 아이템 수집: 약 $0.05 ~ $0.10

**절약 팁:**
- gpt-3.5-turbo 사용 (약 10배 저렴)
- 간단한 페이지는 3.5-turbo로 충분

### 2. 크롤링 에티켓

- ⏱️ 적절한 속도 조절 사용
- 🤖 robots.txt 확인
- 📊 필요한 데이터만 수집
- 🔄 과도한 요청 자제

### 3. 법적 고려사항

웹 크롤링 전에:
- 웹사이트 이용약관 확인
- 저작권 존중
- 개인정보 보호법 준수

## 🐛 문제 해결

### "브라우저 연결 실패"

```bash
# CDP 포트가 열려있는지 확인
netstat -an | findstr 9222

# Chrome이 디버깅 모드로 실행되었는지 확인
chrome://inspect 접속 확인
```

### "LLM 분석 실패"

```
1. API 키 확인
2. 모델 이름 확인 (gpt-4-turbo-preview 등)
3. API 크레딧 확인
4. 네트워크 연결 확인
```

### "데이터가 추출되지 않음"

```
1. DOM 구조 뷰어로 페이지 구조 확인
2. 크롤링 요청을 더 구체적으로 작성
3. 페이지가 완전히 로드될 때까지 대기
4. JavaScript가 필요한 페이지인지 확인
```

## 💡 고급 팁

### 1. 전략 재사용

생성된 크롤링 전략을 저장해서 재사용:

```python
# 로그에 표시되는 전략을 복사해서 파일로 저장
strategy = {...}

# 다음번에 직접 사용
extractor = DataExtractor(page)
data = extractor.extract_data(strategy)
```

### 2. 커스텀 JavaScript로 전처리

```javascript
// 페이지 로딩 대기
await new Promise(r => setTimeout(r, 3000));

// 더 보기 버튼 클릭
document.querySelector('.load-more')?.click();

// 크롤링 실행
```

### 3. 여러 페이지를 한번에

```bash
# 스크립트로 자동화
for url in urls.txt; do
  UniversalCrawler.exe --cli --url "$url" --request "..."
done
```

## 📚 추가 자료

- [OpenAI API 문서](https://platform.openai.com/docs)
- [Playwright 문서](https://playwright.dev)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)

## 🆘 지원

문제가 발생하면:
1. 로그 확인 (GUI의 로그 탭)
2. GitHub Issues에 버그 리포트
3. 상세한 오류 메시지 포함
