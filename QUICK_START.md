# 🚀 5분 빠른 시작 가이드

코딩 지식이 전혀 없어도 괜찮습니다! 단계별로 따라하세요.

## ⚠️ 중요: Python 버전

**Python 3.13은 아직 지원되지 않습니다!**

✅ **Python 3.11** 또는 **Python 3.12**를 사용하세요.

현재 버전 확인:
```bash
python --version
```

3.13이 나온다면:
1. Python 3.12 다운로드: https://www.python.org/downloads/
2. 설치 시 "Add Python to PATH" 체크 필수!

---

## 📦 설치 (Windows)

### 방법 1: 자동 설치 (가장 쉬움) ⭐

1. **install.bat 더블클릭**

끝! 모든 것이 자동으로 설치됩니다.

### 방법 2: 수동 설치

PowerShell이나 CMD를 열고:

```bash
# 1. 패키지 설치
pip install playwright openai beautifulsoup4 lxml openpyxl

# 2. Playwright 브라우저 설치
python -m playwright install chromium

# 3. 설정 파일 생성
copy config.example.json config.json
```

---

## 🔑 OpenAI API 키 설정

### 1. API 키 발급

1. https://platform.openai.com/api-keys 접속
2. 로그인 (없으면 회원가입)
3. "Create new secret key" 클릭
4. 키 복사 (sk-로 시작)

### 2. 설정 파일에 입력

`config.json` 파일을 메모장으로 열고:

```json
{
  "openai_api_key": "sk-여기에-복사한-키-붙여넣기",
  "default_model": "gpt-4-turbo-preview"
}
```

저장!

---

## 🎮 실행

### GUI 모드 (추천)

```bash
python main.py
```

또는 `main.py` 파일을 더블클릭!

---

## 🎯 첫 크롤링 해보기

### 1단계: Chrome CDP 실행

GUI에서:
1. **[크롤링]** 탭 클릭
2. **"🚀 Chrome CDP 실행"** 버튼 클릭
3. Chrome이 자동으로 열립니다

### 2단계: 브라우저 연결

1. **"🔗 브라우저 연결"** 버튼 클릭
2. 성공 메시지 확인

### 3단계: 크롤링할 페이지 열기

열린 Chrome 브라우저에서:
- 크롤링하고 싶은 웹사이트로 이동
- 예: 네이버 뉴스, 쇼핑몰, 게시판 등

### 4단계: 크롤링 요청 입력

GUI의 **"크롤링 요청"** 박스에:

```
게시판의 모든 정보를 수집해줘
```

또는 더 구체적으로:

```
게시판의 제목, 작성자, 날짜, 조회수를 수집해줘.
비밀글은 제외하고
```

### 5단계: 실행!

**"⚡ 한번에 실행"** 버튼 클릭

기다리면... LLM이 분석하고 데이터를 수집합니다!

### 6단계: 결과 확인

1. **[결과]** 탭 클릭
2. 수집된 데이터 확인
3. **"Excel로 저장"** 클릭

완료! 🎉

---

## 💡 자주 묻는 질문 (FAQ)

### Q1: "Python을 찾을 수 없습니다" 오류

**해결**: Python 설치 시 "Add Python to PATH" 체크 필수!

또는 수동으로:
1. 시스템 환경 변수 편집
2. Path에 Python 경로 추가

### Q2: "playwright 명령을 찾을 수 없습니다"

**해결**:
```bash
python -m playwright install chromium
```

`playwright` 대신 `python -m playwright` 사용

### Q3: "pandas 설치 실패" 또는 "numpy 컴파일 오류"

**해결**: Python 3.13을 사용 중이라면 3.11이나 3.12로 다운그레이드

또는 미리 빌드된 버전 설치:
```bash
pip install pandas --only-binary=:all:
```

### Q4: Chrome CDP 실행 버튼이 작동하지 않음

**수동으로 Chrome 실행**:

Windows:
```bash
chrome.exe --remote-debugging-port=9222
```

Chrome 경로를 모른다면:
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

### Q5: "OpenAI API 오류" 또는 "Invalid API key"

**체크리스트**:
- [ ] API 키가 `sk-`로 시작하나요?
- [ ] config.json에 올바르게 입력했나요?
- [ ] 따옴표 안에 넣었나요?
- [ ] OpenAI 계정에 크레딧이 있나요?

### Q6: 크롤링이 느려요

**속도 조절** (GUI에서):
- 아이템 딜레이: 0.0초 (빠름)
- 페이지 딜레이: 1초 (빠름)

하지만 서버 부하 방지를 위해:
- 아이템 딜레이: 0.3초
- 페이지 딜레이: 2초

권장합니다.

### Q7: 로그인이 필요한 사이트는?

**CDP 모드 사용**:
1. Chrome CDP 실행
2. 브라우저에서 수동으로 로그인
3. 크롤러 연결
4. 크롤링 실행

로그인 상태가 유지됩니다!

### Q8: "모든 정보"라고만 해도 되나요?

**네!** LLM이 페이지를 분석해서 모든 필드를 자동으로 찾습니다.

하지만 더 구체적으로 요청하면 더 정확합니다:
```
게시판의 제목, 작성자, 날짜만 수집해줘
```

---

## 🆘 문제 해결이 안 되면

1. **로그 확인**: GUI의 "로그" 탭에서 오류 메시지 확인
2. **GitHub Issues**: https://github.com/your-repo/issues
3. **재설치**:
   ```bash
   pip uninstall -y playwright openai beautifulsoup4 lxml pandas openpyxl
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

---

## 📚 더 알아보기

- **실전 가이드**: [PRACTICAL_GUIDE.md](PRACTICAL_GUIDE.md)
- **작동 원리**: [HOW_IT_WORKS.md](HOW_IT_WORKS.md)
- **초보자 가이드**: [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)

---

## ✨ 팁

### 로그인 사이트 크롤링

```
1. Chrome CDP 실행
2. 브라우저에서 로그인
3. 원하는 페이지 이동
4. 크롤러 연결
5. 크롤링 실행
```

### 여러 페이지 크롤링

GUI에서:
- 최대 페이지: 원하는 수 (예: 10)
- 페이지네이션 처리: 체크
- 실행!

### 속도 vs 안정성

**빠르게** (위험):
- 아이템 딜레이: 0.0초
- 페이지 딜레이: 0.5초

**안전하게** (권장):
- 아이템 딜레이: 0.5초
- 페이지 딜레이: 3초

---

**이제 시작하세요!** 🚀

`python main.py`
