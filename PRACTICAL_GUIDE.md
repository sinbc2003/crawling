# 🎯 실전 사용 가이드

## 실제 시나리오별 사용법

### 시나리오 1: 회사 내부 게시판 크롤링

#### 상황
- 로그인 필요
- 드롭다운 필터: 업무구분, 년도, 부서
- 비밀글 제외
- 약 500개 게시글

#### 해결 방법

**1단계: 브라우저 준비**
```bash
# Windows
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome-work"

# Mac
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-work"
```

**2단계: 수동 작업 (브라우저에서)**
1. 회사 사이트 로그인
2. 게시판 메뉴로 이동
3. 필터 설정:
   - 업무구분: "전체" 또는 원하는 업무
   - 년도: "2024"
   - 부서: "전사"
4. 검색 버튼 클릭
5. 결과 화면 확인

**3단계: 크롤러 실행**

GUI에서:
```
[설정]
- API Key 입력
- 모델: gpt-4-turbo-preview

[크롤링]
- "기존 브라우저 연결" 선택
- "브라우저 연결" 클릭

[요청 입력]
"게시판의 모든 정보를 수집해줘.
비밀글이나 접근 불가 글은 제외하고,
제목, 작성자, 작성일, 내용 요약, 조회수, 첨부파일 여부를 가져와줘"

[옵션 설정]
- 최대 페이지: 50
- 아이템 딜레이: 0.5초 (회사 서버 부하 고려)
- 페이지 딜레이: 2초
- 페이지네이션: 체크

→ "한번에 실행" 클릭
```

**4단계: 다른 필터로 반복**

다른 업무구분이나 년도로 수집하려면:

방법 A (수동):
1. 브라우저에서 필터 다시 선택
2. 검색 클릭
3. 크롤러에서 다시 실행

방법 B (JavaScript 자동화):
```javascript
// "브라우저 제어" 탭에서 실행

// 업무구분 변경
document.querySelector('#업무구분').value = '인사';
document.querySelector('#업무구분').dispatchEvent(new Event('change'));

// 검색 버튼 클릭
document.querySelector('.btn-search').click();

// 3초 대기 후 크롤링 실행
```

---

### 시나리오 2: 공공 데이터 포털 (복잡한 필터)

#### 상황
- 로그인 불필요
- 필터: 지역, 카테고리, 기간, 정렬 순서
- 페이지네이션 복잡

#### 해결 방법

**방법 1: 수동 필터 설정 + 크롤링**
```
1. Chrome CDP 모드 실행
2. 브라우저에서 모든 필터 설정
3. 크롤러 연결 → 크롤링 실행
```

**방법 2: URL 패턴 활용**

많은 사이트는 필터가 URL에 반영됩니다:
```
https://example.com/data?region=seoul&category=health&year=2024
```

CLI 모드 사용:
```bash
UniversalCrawler.exe --cli \
  --url "https://example.com/data?region=seoul&category=health&year=2024" \
  --request "데이터 목록의 모든 정보를 수집해줘" \
  --max-pages 20
```

여러 조합을 스크립트로:
```bash
# urls.txt
https://example.com/data?region=seoul&category=health&year=2024
https://example.com/data?region=busan&category=health&year=2024
https://example.com/data?region=seoul&category=edu&year=2024

# 자동 실행
for url in $(cat urls.txt); do
  UniversalCrawler.exe --cli \
    --url "$url" \
    --request "데이터 수집" \
    --output "data_$(echo $url | md5sum | cut -d' ' -f1).json"
done
```

---

### 시나리오 3: 동적 로딩 페이지 (무한 스크롤)

#### 상황
- 스크롤하면 데이터가 계속 로딩됨
- 페이지네이션 버튼 없음

#### 해결 방법

**JavaScript로 스크롤 + 크롤링:**

```javascript
// "브라우저 제어" 탭에서

// 1. 끝까지 스크롤 (데이터 모두 로드)
async function scrollToBottom() {
  let lastHeight = document.body.scrollHeight;

  while (true) {
    // 스크롤
    window.scrollTo(0, document.body.scrollHeight);

    // 2초 대기 (로딩 시간)
    await new Promise(r => setTimeout(r, 2000));

    // 높이 변화 확인
    let newHeight = document.body.scrollHeight;
    if (newHeight === lastHeight) break;
    lastHeight = newHeight;
  }

  return "스크롤 완료";
}

scrollToBottom();
```

실행 후 → 크롤링 요청:
```
"페이지의 모든 게시글 정보를 수집해줘"
```

---

## 🤔 자주 묻는 질문

### Q1: "모든 정보를 수집해줘"라고만 해도 되나요?

**답**: 네, 가능합니다!

```
간단한 요청:
"게시판의 모든 정보를 수집해줘"

→ LLM이 자동으로:
  - 제목 (찾음)
  - 작성자 (찾음)
  - 날짜 (찾음)
  - 조회수 (찾음)
  - 기타 모든 필드 (찾음)
```

**하지만 더 구체적이면 더 정확합니다:**
```
구체적인 요청:
"게시판의 제목, 작성자, 작성일, 조회수, 첨부파일 여부를 수집해줘.
비밀글이나 권한 없는 글은 제외하고"

→ 원하는 필드만 정확히 추출
→ 조건 명시로 불필요한 데이터 제외
```

### Q2: 드롭다운을 일일이 다 선택해야 하나요?

**답**: 아니요, 두 가지 방법이 있습니다.

**방법 1: 한 번만 수동 선택 → 크롤링**
```
필터가 많아도 괜찮습니다:
1. 브라우저에서 원하는 조합 선택
2. 크롤링 실행
3. 완료!

다른 조합이 필요하면:
1. 브라우저에서 필터 다시 선택
2. 크롤링 다시 실행
```

**방법 2: JavaScript로 자동화**
```javascript
// 여러 조합을 자동으로
const filters = [
  {업무: '인사', 년도: '2024'},
  {업무: '총무', 년도: '2024'},
  {업무: '인사', 년도: '2023'}
];

for (let filter of filters) {
  // 필터 설정
  document.querySelector('#업무').value = filter.업무;
  document.querySelector('#년도').value = filter.년도;

  // 검색
  document.querySelector('.search').click();

  // 대기
  await new Promise(r => setTimeout(r, 3000));

  // 여기서 크롤링 실행 (수동으로 버튼 클릭)
}
```

### Q3: 비밀글을 자동으로 제외할 수 있나요?

**답**: 네, 요청에 포함하면 됩니다.

```
요청:
"게시판의 모든 정보를 수집해줘.
비밀글, 삭제된 글, 접근 권한 없는 글은 제외하고"

→ LLM이 비밀글 표시(🔒 아이콘 등)를 인식하고 제외
```

또는 CSS selector로:
```
요청:
"게시판에서 .secret-post 클래스가 없는 게시글만 수집해줘"
```

### Q4: 로그인은 어떻게 유지하나요?

**답**: CDP 연결이 핵심입니다.

```bash
# user-data-dir로 세션 유지
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome-session"

→ 이 Chrome 창에서 로그인
→ 크롤러 연결
→ 로그인 상태 유지됨
→ 다음번에도 이 Chrome 창 재사용 가능
```

**장점:**
- 한 번 로그인하면 계속 유지
- 쿠키 자동 저장
- 세션 만료 없음 (Chrome이 열려있는 동안)

### Q5: 여러 페이지의 다른 구조를 크롤링하려면?

**답**: 페이지마다 새로운 요청을 하면 됩니다.

```
사이트 A (게시판):
요청: "게시판의 제목, 작성자를 수집해줘"

사이트 B (상품 목록):
요청: "상품명, 가격, 재고를 수집해줘"

사이트 C (뉴스):
요청: "기사 제목, 본문, 날짜를 수집해줘"
```

**각 페이지마다 LLM이 새로 분석**하므로 구조가 달라도 상관없습니다!

---

## 💡 프로 팁

### 1. 세션 유지 전략

```bash
# 작업별로 Chrome 프로필 분리
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome-work"
chrome.exe --remote-debugging-port=9223 --user-data-dir="C:\chrome-personal"

→ 회사 계정/개인 계정 분리
→ 각각 다른 포트로 접속
```

### 2. 대량 크롤링 전략

```
큰 데이터셋 (1000+ 페이지):

1. 속도 조절 필수:
   - 아이템 딜레이: 0.5초
   - 페이지 딜레이: 3-5초

2. 중간 저장:
   - 100페이지마다 저장
   - 오류 발생 시 처음부터 다시 하지 않아도 됨

3. 밤에 실행:
   - 서버 부하가 적은 시간
   - 속도 조절 더 여유있게
```

### 3. 오류 대응

```
데이터가 제대로 안 나올 때:

1. "DOM 구조" 탭에서 페이지 분석
2. 필요하면 요청을 더 구체적으로 수정
3. JavaScript로 동적 요소 로딩 확인
4. 다른 모델 시도 (gpt-4 → gpt-3.5-turbo 또는 반대)
```

### 4. 비용 절감

```
OpenAI API 비용 줄이기:

1. 간단한 페이지: gpt-3.5-turbo 사용
   페이지당: ~$0.001-0.005

2. 복잡한 페이지: gpt-4-turbo-preview
   페이지당: ~$0.01-0.05

3. 전략 재사용:
   - 같은 구조 페이지는 전략을 재사용
   - LLM 호출 1번으로 여러 페이지 크롤링
```

---

## 🎯 체크리스트

### 크롤링 시작 전

- [ ] Chrome CDP 모드 실행
- [ ] 로그인 (필요시)
- [ ] 필터/드롭다운 설정
- [ ] 결과 페이지 확인
- [ ] OpenAI API 키 준비
- [ ] 속도 조절 설정 (서버 부하 고려)

### 크롤링 실행 중

- [ ] 로그 확인 (오류 없는지)
- [ ] 첫 페이지 결과 확인 (올바른 데이터인지)
- [ ] 속도가 적절한지 확인

### 크롤링 완료 후

- [ ] 결과 미리보기 확인
- [ ] 누락된 데이터 없는지 확인
- [ ] 원하는 형식으로 저장
- [ ] 필요시 추가 크롤링

---

## 🚀 고급: 반복 작업 자동화

### Python 스크립트 예시

```python
import subprocess
import time

# 여러 필터 조합
filters = [
    {"dept": "인사", "year": "2024"},
    {"dept": "총무", "year": "2024"},
    {"dept": "인사", "year": "2023"},
]

for f in filters:
    # JavaScript로 필터 설정 (브라우저 제어 탭에서 미리 준비)
    js_code = f"""
    document.querySelector('#dept').value = '{f['dept']}';
    document.querySelector('#year').value = '{f['year']}';
    document.querySelector('.search-btn').click();
    """

    # 대기
    time.sleep(5)

    # 크롤링 실행 (CLI)
    output_file = f"data_{f['dept']}_{f['year']}.json"
    subprocess.run([
        "UniversalCrawler.exe", "--cli",
        "--cdp-url", "http://localhost:9222",
        "--request", "게시판의 모든 정보를 수집해줘",
        "--max-pages", "10",
        "--output", output_file
    ])

    print(f"완료: {output_file}")
    time.sleep(10)
```

---

## 🎓 결론

**핵심 요점:**

1. ✅ **"모든 정보"라고만 해도 LLM이 알아서 찾습니다**
2. ✅ **드롭다운은 수동 선택 → 크롤링 실행**
3. ✅ **JavaScript로 복잡한 조작 자동화 가능**
4. ✅ **CDP로 로그인 상태 유지**
5. ✅ **페이지마다 다른 구조여도 각각 요청하면 됨**

**기억하세요:**
- LLM은 **selector 생성만** 담당
- UI 조작은 **수동 또는 JavaScript**로
- 로그인/세션은 **CDP 브라우저 연결**로 해결
