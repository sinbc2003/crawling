# 🚀 고급 기능 가이드

AI 웹 크롤러의 고급 기능들을 설명합니다.

## 📑 목차

1. [상세 페이지 자동 추출](#1-상세-페이지-자동-추출)
2. [Vision AI 분석](#2-vision-ai-분석)
3. [전략 저장 및 재사용](#3-전략-저장-및-재사용)
4. [모달 및 SPA 지원](#4-모달-및-spa-지원)
5. [실전 예제](#5-실전-예제)

---

## 1. 상세 페이지 자동 추출

### 💡 개념

게시판이나 상품 목록처럼 **목록 페이지**와 **상세 페이지**가 분리된 경우, 크롤러가 자동으로:

1. 목록에서 각 항목의 링크를 찾음
2. 링크를 하나씩 클릭
3. 상세 페이지에서 추가 정보 추출
4. 다시 목록으로 돌아옴
5. 다음 항목 처리

### 🎯 언제 사용하나요?

- ✅ 커뮤니티 게시판 (제목만 보이고 클릭하면 본문 표시)
- ✅ 쇼핑몰 상품 목록 (목록에서는 이름/가격만, 상세 페이지에는 상세 설명)
- ✅ 뉴스 사이트 (헤드라인 클릭 → 기사 전문)
- ✅ GitHub Issues (목록 → 각 issue 상세)

### 📝 사용 방법

GUI에서:
```
1. 목록 페이지로 이동
2. "각 게시글 자동 클릭하여 상세 내용 수집" 체크박스 선택
3. 크롤링 요청: "게시판의 모든 정보 수집"
4. 실행!
```

결과:
- `title`: 목록에서 추출한 제목
- `author`: 목록에서 추출한 작성자
- `detail_content`: 상세 페이지에서 추출한 본문 (자동으로 추가됨!)
- `detail_date`: 상세 페이지의 날짜

### ⚙️ 동작 원리

```python
from src.detail_extractor import DetailExtractor

# 기본 목록 전략
list_strategy = {
    "container_selector": ".post-item",
    "fields": [
        {"name": "title", "selector": ".title", "attribute": None},
        {"name": "link", "selector": "a", "attribute": "href"}  # 중요: 링크 필드 필수
    ]
}

# 자동 추출
extractor = DetailExtractor(page, item_delay=0.5, page_delay=1.0)
data = extractor.extract_list_with_details(
    list_strategy=list_strategy,
    detail_link_field="link"  # 어떤 필드가 링크인지 지정
)

# 결과: 목록 데이터 + 상세 데이터 합쳐짐
# [
#   {
#     "title": "...",
#     "link": "...",
#     "detail_content": "...",  # 자동 추출!
#     "detail_author": "...",   # 자동 추출!
#   }
# ]
```

---

## 2. Vision AI 분석

### 💡 개념

일반 분석은 **HTML 코드**를 분석하지만, Vision AI는 **화면 스크린샷**을 직접 봅니다.

| 항목 | HTML 분석 | Vision AI |
|------|-----------|-----------|
| 속도 | 빠름 ⚡ | 느림 🐢 |
| 비용 | 저렴 💰 | 비쌈 💰💰💰 |
| 정확도 | 보통 | 높음 ✨ |
| 동적 페이지 | 어려움 | 쉬움 ✅ |

### 🎯 언제 사용하나요?

- ✅ JavaScript로 동적 생성되는 복잡한 페이지
- ✅ HTML 구조가 매우 복잡하거나 의미 없는 class명
- ✅ Canvas/SVG로 그려진 요소
- ✅ iframe 내부 요소
- ✅ 일반 분석이 실패했을 때

### 📝 사용 방법

GUI에서:
```
1. "Vision AI로 화면 분석" 체크박스 선택
2. 크롤링 요청: "화면에 보이는 모든 버튼 찾기"
3. 실행!
```

Vision AI는 **사람이 보는 것처럼** 화면을 인식합니다:
- "상단 좌측의 파란색 버튼"
- "가장 큰 제목"
- "반복되는 카드 형태의 요소들"

### 💰 비용 주의

- GPT-4 Vision은 일반 모델보다 **약 2-3배** 비쌉니다
- 스크린샷이 클수록 비용 증가
- 반복 사용 시 전략 저장 필수!

### ⚙️ 동작 원리

```python
from src.vision_detector import VisionDetector

detector = VisionDetector(api_key)

# 페이지 스크린샷 → GPT-4 Vision 분석 → 전략 생성
strategy = detector.generate_extraction_strategy_from_screenshot(
    page,
    user_request="게시판의 모든 정보 수집"
)

# 일반 전략과 동일한 형식으로 반환됨
# {
#   "container_selector": "...",
#   "fields": [...]
# }
```

---

## 3. 전략 저장 및 재사용

### 💡 개념

한 번 생성한 크롤링 전략(CSS selector 등)을 파일로 저장하여, 다음에 같은 사이트를 크롤링할 때 **LLM 분석 없이** 바로 사용할 수 있습니다.

### 💰 장점

- ✅ **비용 절약**: LLM API 호출 불필요
- ✅ **시간 절약**: 즉시 크롤링 시작
- ✅ **일관성**: 매번 같은 방식으로 추출
- ✅ **안정성**: 검증된 전략 재사용

### 📝 사용 방법

#### 저장:
```
1. 크롤링 실행 후 성공 확인
2. "전략 관리 → 저장" 버튼 클릭
3. 전략 이름 입력 (예: "네이버 카페 게시판")
4. 설명 입력 (선택)
5. 완료!
```

전략은 `strategies/` 폴더에 JSON 파일로 저장됩니다:
```
strategies/
  ├── example.com_20250113_143022.json
  ├── github.com_20250113_145130.json
  └── ...
```

#### 불러오기:
```
1. 크롤링하려는 사이트로 이동
2. "전략 관리 → 불러오기" 버튼 클릭
3. 목록에서 원하는 전략 선택
4. "불러오기" 클릭
5. "크롤링 시작" → 즉시 실행!
```

### 📄 전략 파일 구조

```json
{
  "name": "GitHub Issues 크롤러",
  "url": "https://github.com/user/repo/issues",
  "domain": "github.com",
  "description": "GitHub Issues 목록 추출",
  "tags": ["github", "issues", "개발"],
  "created_at": "2025-01-13T14:30:22",
  "strategy": {
    "container_selector": ".js-issue-row",
    "fields": [
      {
        "name": "title",
        "selector": ".js-navigation-open",
        "attribute": null
      },
      {
        "name": "author",
        "selector": ".opened-by",
        "attribute": null
      }
    ],
    "pagination": {
      "next_button_selector": ".next_page"
    }
  }
}
```

### ⚙️ 프로그래밍 방식

```python
from src.strategy_manager import StrategyManager

manager = StrategyManager()

# 저장
manager.save_strategy(
    url="https://example.com",
    strategy=my_strategy,
    name="예시 사이트 크롤러",
    tags=["shopping", "products"]
)

# 불러오기 (URL로 자동 찾기)
strategy_data = manager.find_strategy_by_url("https://example.com")
if strategy_data:
    strategy = strategy_data['strategy']
    # 바로 크롤링 시작!

# 검색
results = manager.search_strategies("github")

# 목록 조회
all_strategies = manager.list_strategies()
domain_strategies = manager.list_strategies(domain="github.com")
```

---

## 4. 모달 및 SPA 지원

### 💡 개념

최근 웹사이트들은 페이지 이동 없이 팝업(모달)으로 내용을 보여주거나, URL이 변경되지 않는 Single Page Application(SPA) 방식을 많이 사용합니다.

이 크롤러는 **자동으로 감지**하여 처리합니다.

### 🎯 감지 방식

```python
# 링크 클릭 전 URL 저장
old_url = page.url

# 클릭!
element.click()
time.sleep(1)

# 클릭 후 URL 확인
new_url = page.url

if old_url == new_url:
    # URL이 안 바뀜 → 모달!
    print("모달 감지됨")
    extract_modal_content()
    close_modal()
else:
    # URL이 바뀜 → 일반 페이지
    print("페이지 이동됨")
    extract_page_content()
    go_back()
```

### 🚪 모달 닫기 자동 처리

크롤러는 다음 방법들을 순서대로 시도합니다:

1. ✅ 닫기 버튼 클릭 (`.close`, `[data-dismiss="modal"]` 등)
2. ✅ ESC 키 누르기
3. ✅ 모달 배경(backdrop) 클릭

```python
# 자동으로 처리됨!
detail_extractor = DetailExtractor(page)
data = detail_extractor.extract_list_with_details(strategy)
# 모달이든 일반 페이지든 알아서 처리!
```

### 📝 지원되는 모달 라이브러리

- ✅ Bootstrap Modal
- ✅ Material-UI Dialog
- ✅ Semantic UI Modal
- ✅ 대부분의 커스텀 모달

---

## 5. 실전 예제

### 예제 1: 커뮤니티 게시판 (모달 방식)

**상황**: 게시글을 클릭하면 모달 팝업으로 본문 표시

```python
from src.detail_extractor import DetailExtractor
from src.browser_connector import BrowserConnector

# 브라우저 연결
browser = BrowserConnector(config)
browser.navigate_to("https://community.example.com/board")

# 목록 전략 (LLM이 자동 생성 or 저장된 전략)
list_strategy = {
    "container_selector": ".board-item",
    "fields": [
        {"name": "title", "selector": ".title", "attribute": None},
        {"name": "author", "selector": ".author", "attribute": None},
        {"name": "link", "selector": "a", "attribute": "href"}
    ]
}

# 상세 추출 (모달 자동 처리!)
extractor = DetailExtractor(browser.page)
data = extractor.extract_list_with_details(
    list_strategy=list_strategy,
    max_items=50
)

# 결과
for item in data:
    print(f"제목: {item['title']}")
    print(f"작성자: {item['author']}")
    print(f"본문: {item['detail_content']}")  # 모달에서 자동 추출!
    print("---")
```

### 예제 2: GitHub Issues (페이지네이션 + 상세)

```python
# 페이지네이션 포함 전략
strategy = {
    "container_selector": ".js-issue-row",
    "fields": [
        {"name": "title", "selector": ".js-navigation-open", "attribute": None},
        {"name": "link", "selector": ".js-navigation-open", "attribute": "href"},
        {"name": "author", "selector": ".opened-by a", "attribute": None},
        {"name": "labels", "selector": ".labels .label", "attribute": None}
    ],
    "pagination": {
        "next_button_selector": ".pagination .next_page"
    }
}

# 여러 페이지 + 각 issue 상세 내용 추출
extractor = DetailExtractor(browser.page, item_delay=1.0, page_delay=2.0)
data = extractor.extract_with_pagination_and_details(
    list_strategy=strategy,
    max_pages=5,
    progress_callback=lambda page, cur, total: print(f"페이지 {page}: {cur}/{total}")
)
```

### 예제 3: Vision AI로 복잡한 페이지 분석

```python
from src.vision_detector import VisionDetector

detector = VisionDetector(api_key)

# 스크린샷 기반 자동 분석
strategy = detector.generate_extraction_strategy_from_screenshot(
    page,
    user_request="화면에 보이는 모든 상품 정보를 수집해줘"
)

# 생성된 전략으로 즉시 추출
extractor = DataExtractor(page)
data = extractor.extract_data(strategy)
```

### 예제 4: 전략 저장 후 재사용

```python
from src.strategy_manager import StrategyManager

manager = StrategyManager()

# === 첫 번째 실행 (전략 생성 + 저장) ===
analyzer = LLMAnalyzer(api_key)
strategy = analyzer.generate_selectors_from_html(html, "게시판 수집")

# 크롤링
extractor = DataExtractor(page)
data = extractor.extract_data(strategy)

# 전략 저장
manager.save_strategy(
    url=page.url,
    strategy=strategy,
    name="우리 회사 게시판"
)

# === 이후 실행들 (LLM 호출 없이 즉시 크롤링!) ===
loaded = manager.find_strategy_by_url(page.url)
if loaded:
    strategy = loaded['strategy']
    extractor = DataExtractor(page)
    data = extractor.extract_data(strategy)  # 바로 실행!
```

---

## 🎓 팁 & 트릭

### 속도 최적화

```python
# 빠른 크롤링 (서버 부하 주의)
extractor = DetailExtractor(page, item_delay=0.0, page_delay=0.5)

# 안전한 크롤링 (권장)
extractor = DetailExtractor(page, item_delay=0.5, page_delay=2.0)

# 매우 느린 서버용
extractor = DetailExtractor(page, item_delay=1.0, page_delay=5.0)
```

### Vision AI 비용 절감

1. **먼저 HTML 분석 시도** → 실패하면 Vision 사용
2. **첫 페이지만 Vision으로 분석** → 전략 생성 → 저장 → 재사용
3. **스크린샷 크기 축소** (full_page=False)

### 에러 처리

```python
try:
    data = extractor.extract_list_with_details(strategy)
except Exception as e:
    print(f"에러 발생: {e}")
    # 기본 추출로 폴백
    basic_extractor = DataExtractor(page)
    data = basic_extractor.extract_data(strategy)
```

### 진행률 모니터링

```python
def progress_callback(current, total):
    percent = (current / total) * 100
    print(f"진행률: {percent:.1f}% ({current}/{total})")

data = extractor.extract_list_with_details(
    strategy,
    progress_callback=progress_callback
)
```

---

## ⚠️ 주의사항

1. **로그인이 필요한 사이트**
   - CDP로 이미 로그인된 브라우저에 연결하세요
   - `chrome --remote-debugging-port=9222`

2. **동적 로딩**
   - 페이지 로딩 후 충분한 대기 시간 설정
   - `page_delay` 파라미터 조정

3. **IP 차단 방지**
   - `item_delay`, `page_delay` 적절히 설정
   - 짧은 시간에 너무 많은 요청 금지

4. **메모리 사용**
   - 수천 개 아이템 추출 시 메모리 주의
   - 배치 처리 권장

---

## 📚 추가 자료

- [QUICK_START.md](QUICK_START.md) - 빠른 시작 가이드
- [HOW_IT_WORKS.md](HOW_IT_WORKS.md) - 동작 원리 설명
- [PRACTICAL_GUIDE.md](PRACTICAL_GUIDE.md) - 실전 가이드
- [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) - 초보자 가이드

---

## 💬 문의 및 피드백

이 기능들에 대해 질문이나 개선 제안이 있으시면 GitHub Issues에 남겨주세요!
