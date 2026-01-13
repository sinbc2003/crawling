# 사용 가이드

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 설정 파일 생성

`config.json` 파일 생성:

```json
{
  "openai_api_key": "your-openai-api-key",
  "default_model": "gpt-4-turbo-preview"
}
```

또는 `config.example.json`을 복사:

```bash
cp config.example.json config.json
# 그리고 API 키 입력
```

## 사용 방법

### GUI 모드 (추천)

```bash
python main.py
```

#### 단계별 사용법:

1. **설정 탭**
   - OpenAI API Key 입력
   - "모델 목록 불러오기" 클릭하여 사용 가능한 모델 확인
   - 원하는 모델 선택 (gpt-4-turbo-preview 추천)
   - "설정 저장" 클릭

2. **브라우저 연결 (두 가지 방법)**

   **방법 A: 새 브라우저 시작**
   - "새 브라우저 시작" 라디오 버튼 선택
   - "브라우저 연결" 버튼 클릭

   **방법 B: 기존 브라우저 연결 (권장)**
   - Chrome을 다음 명령으로 실행:
     ```bash
     # Windows
     chrome.exe --remote-debugging-port=9222

     # Mac
     /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

     # Linux
     google-chrome --remote-debugging-port=9222
     ```
   - "기존 브라우저 연결 (CDP)" 라디오 버튼 선택
   - "브라우저 연결" 버튼 클릭

3. **페이지 이동**
   - URL 입력 필드에 크롤링할 페이지 URL 입력
   - "URL 이동" 버튼 클릭
   - 또는 이미 열린 브라우저에서 직접 탐색

4. **크롤링 요청**
   - 텍스트 영역에 자연어로 요청 입력
   - 예시:
     - "게시판의 제목, 작성자, 날짜를 수집해주세요"
     - "상품명, 가격, 평점을 가져와주세요"
     - "뉴스 기사의 제목, 본문, 작성일을 추출해주세요"

5. **실행 방법 선택**

   **방법 A: 단계별 실행**
   - "1️⃣ 전략 생성 (분석)" 버튼 클릭 → LLM이 페이지 분석
   - 생성된 전략 확인
   - "2️⃣ 데이터 추출" 버튼 클릭 → 실제 데이터 수집

   **방법 B: 한번에 실행 (권장)**
   - "⚡ 한번에 실행" 버튼 클릭
   - 전략 생성과 데이터 추출이 자동으로 진행

6. **결과 확인 및 내보내기**
   - "결과" 탭으로 이동
   - 통계 및 데이터 미리보기 확인
   - 원하는 형식으로 저장:
     - JSON으로 저장
     - CSV로 저장
     - Excel로 저장
     - 모든 형식으로 저장

### CLI 모드

기본 사용:

```bash
python main.py --cli \
  --url "https://example.com/board" \
  --request "게시판의 제목, 작성자, 날짜를 수집해주세요" \
  --max-pages 5 \
  --output "result.json"
```

옵션 설명:

- `--cli`: CLI 모드 활성화
- `--url URL`: 크롤링할 URL
- `--request "요청"`: 자연어 크롤링 요청
- `--max-pages N`: 최대 N 페이지 수집 (기본: 1)
- `--output FILE`: 출력 파일명
- `--format {json,csv,excel}`: 출력 형식
- `--model MODEL`: 사용할 OpenAI 모델
- `--cdp-url URL`: 기존 브라우저 연결 (예: http://localhost:9222)
- `--headless`: 헤드리스 모드
- `--no-preview`: 미리보기 비활성화
- `--keep-open`: 브라우저 연결 유지
- `--verbose`: 상세 로그

예시:

```bash
# 헤드리스 모드로 실행
python main.py --cli --headless \
  --url "https://news.ycombinator.com" \
  --request "게시글 제목과 점수를 수집해주세요"

# 기존 브라우저에 연결
python main.py --cli \
  --cdp-url "http://localhost:9222" \
  --request "현재 페이지의 상품 정보를 수집해주세요" \
  --format excel

# 여러 페이지 크롤링
python main.py --cli \
  --url "https://example.com/products" \
  --request "상품명, 가격, 리뷰 수를 가져와주세요" \
  --max-pages 10 \
  --format csv
```

## 실행파일 빌드

### PyInstaller로 빌드

```bash
# 빌드 실행
pyinstaller build.spec

# 생성된 실행파일
# Windows: dist/UniversalCrawler.exe
# Mac/Linux: dist/UniversalCrawler
```

### 빌드된 실행파일 사용

```bash
# Windows
UniversalCrawler.exe

# Mac/Linux
./UniversalCrawler

# CLI 모드
UniversalCrawler.exe --cli --url "..." --request "..."
```

## 크롤링 요청 예시

### 게시판 크롤링

```
"게시판의 모든 글 제목, 작성자, 작성일, 조회수를 수집해주세요"
```

### 쇼핑몰 상품 크롤링

```
"상품명, 가격, 할인율, 평점, 리뷰 수를 가져와주세요"
```

### 뉴스 기사 크롤링

```
"기사 제목, 본문, 작성자, 게시일, 카테고리를 추출해주세요"
```

### 테이블 데이터 크롤링

```
"표에 있는 모든 데이터를 수집해주세요"
```

### 링크 수집

```
"모든 링크의 텍스트와 URL을 가져와주세요"
```

## 팁과 트릭

### 1. 기존 브라우저 연결 사용

기존 브라우저를 연결하면:
- 로그인 상태 유지
- 쿠키/세션 활용
- 수동으로 페이지 탐색 가능
- 더 안정적인 크롤링

### 2. 모델 선택

- **gpt-4-turbo-preview**: 가장 정확, 복잡한 페이지에 추천
- **gpt-3.5-turbo**: 빠르고 저렴, 간단한 페이지에 적합

### 3. 크롤링 요청 작성

명확하고 구체적으로 작성:
- ✅ 좋은 예: "게시글의 제목, 작성자, 날짜를 수집해주세요"
- ❌ 나쁜 예: "데이터 가져와줘"

### 4. 페이지네이션

여러 페이지가 있는 경우:
- "페이지네이션 처리" 체크박스 활성화
- 최대 페이지 수 설정
- LLM이 자동으로 "다음" 버튼 찾아서 순회

### 5. 문제 해결

**데이터가 추출되지 않을 때:**
1. 페이지가 완전히 로드될 때까지 대기
2. 크롤링 요청을 더 구체적으로 작성
3. 다른 모델(gpt-4) 시도
4. 로그 확인하여 오류 메시지 확인

**브라우저 연결 실패:**
1. CDP URL이 정확한지 확인
2. Chrome이 디버깅 모드로 실행되었는지 확인
3. 포트(9222)가 사용 중인지 확인

## 출력 형식

### JSON

```json
[
  {
    "title": "게시글 제목",
    "author": "작성자",
    "date": "2024-01-01"
  },
  ...
]
```

### CSV

```csv
title,author,date
게시글 제목,작성자,2024-01-01
...
```

### Excel

`*.xlsx` 파일로 저장, Excel에서 바로 열 수 있음

## 라이센스

MIT License
