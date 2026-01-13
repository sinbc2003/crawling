"""
메인 GUI 애플리케이션
Tkinter 기반 크롤러 인터페이스
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List
import subprocess
import platform
import os

from src.browser_connector import BrowserConnector
from src.dom_extractor import DOMExtractor
from src.llm_analyzer import LLMAnalyzer
from src.data_extractor import DataExtractor
from src.exporter import DataExporter

logger = logging.getLogger(__name__)


class CrawlerApp:
    """크롤러 GUI 애플리케이션"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🕷️ AI-Powered Universal Web Crawler")
        self.root.geometry("1000x800")

        # 상태 변수
        self.config = self.load_config()
        self.browser_connector: Optional[BrowserConnector] = None
        self.llm_analyzer: Optional[LLMAnalyzer] = None
        self.current_strategy: Optional[Dict] = None
        self.extracted_data: List[Dict] = []

        # GUI 생성
        self.create_widgets()

        # 초기화
        self.initialize_llm()

    def load_config(self) -> Dict:
        """설정 파일 로드"""
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 설정 파일이 없으면 기본값 반환 및 생성
        default_config = {
            "openai_api_key": "",
            "default_model": "gpt-4-turbo-preview",
            "browser": {
                "headless": False,
                "timeout": 30000
            },
            "crawler": {
                "max_pages": 10,
                "delay_between_pages": 1000
            }
        }

        # 기본 설정 파일 생성
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
        except:
            pass

        return default_config

    def save_config(self):
        """설정 파일 저장"""
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")
            return False

    def create_widgets(self):
        """GUI 위젯 생성"""
        # 노트북 (탭)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 탭 1: 설정
        self.create_settings_tab(notebook)

        # 탭 2: 크롤링
        self.create_crawling_tab(notebook)

        # 탭 3: DOM 구조 뷰어
        self.create_dom_viewer_tab(notebook)

        # 탭 4: 브라우저 제어
        self.create_browser_control_tab(notebook)

        # 탭 5: 결과
        self.create_results_tab(notebook)

        # 상태바
        self.status_var = tk.StringVar(value="준비")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_settings_tab(self, notebook: ttk.Notebook):
        """설정 탭 생성"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="⚙️ 설정")

        # OpenAI API 설정
        api_frame = ttk.LabelFrame(frame, text="OpenAI API 설정", padding=10)
        api_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_entry = ttk.Entry(api_frame, width=50, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5)
        if self.config.get('openai_api_key'):
            self.api_key_entry.insert(0, self.config['openai_api_key'])

        ttk.Label(api_frame, text="모델:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.model_combo = ttk.Combobox(api_frame, width=47, state='readonly')
        self.model_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(api_frame, text="모델 목록 불러오기", command=self.load_models).grid(
            row=2, column=1, sticky=tk.E, pady=5
        )

        ttk.Button(api_frame, text="설정 저장", command=self.save_settings).grid(
            row=3, column=1, sticky=tk.E, pady=5
        )

        # 브라우저 연결 설정
        browser_frame = ttk.LabelFrame(frame, text="브라우저 연결", padding=10)
        browser_frame.pack(fill=tk.X, padx=10, pady=10)

        self.browser_mode = tk.StringVar(value="new")
        ttk.Radiobutton(
            browser_frame, text="새 브라우저 시작", variable=self.browser_mode, value="new"
        ).grid(row=0, column=0, sticky=tk.W, pady=5)

        ttk.Radiobutton(
            browser_frame, text="기존 브라우저 연결 (CDP)", variable=self.browser_mode, value="existing"
        ).grid(row=1, column=0, sticky=tk.W, pady=5)

        ttk.Label(browser_frame, text="CDP URL:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cdp_url_entry = ttk.Entry(browser_frame, width=50)
        self.cdp_url_entry.insert(0, "http://localhost:9222")
        self.cdp_url_entry.grid(row=2, column=1, padx=5, pady=5)

        # 안내 메시지
        info_text = """
💡 기존 브라우저 연결 방법:
Chrome을 다음 명령으로 실행하세요:

Windows:
chrome.exe --remote-debugging-port=9222

Mac/Linux:
google-chrome --remote-debugging-port=9222
        """
        info_label = ttk.Label(browser_frame, text=info_text, justify=tk.LEFT, foreground="blue")
        info_label.grid(row=3, column=0, columnspan=2, pady=10)

    def create_crawling_tab(self, notebook: ttk.Notebook):
        """크롤링 탭 생성"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🔍 크롤링")

        # 브라우저 제어
        control_frame = ttk.LabelFrame(frame, text="브라우저 제어", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(control_frame, text="🚀 Chrome CDP 실행", command=self.launch_chrome_cdp).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="🔗 브라우저 연결", command=self.connect_browser).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="📍 URL 이동", command=self.navigate_to_url).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="❌ 연결 해제", command=self.disconnect_browser).pack(
            side=tk.LEFT, padx=5
        )

        self.url_entry = ttk.Entry(control_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 크롤링 요청
        request_frame = ttk.LabelFrame(frame, text="크롤링 요청 (자연어)", padding=10)
        request_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(request_frame, text="수집하고 싶은 데이터를 자연어로 설명하세요:").pack(
            anchor=tk.W, pady=5
        )

        self.request_text = scrolledtext.ScrolledText(request_frame, height=5, wrap=tk.WORD)
        self.request_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.request_text.insert(
            "1.0",
            "예시: 게시판의 제목, 작성자, 날짜를 모두 수집해주세요"
        )

        # 크롤링 옵션
        options_frame = ttk.Frame(request_frame)
        options_frame.pack(fill=tk.X, pady=5)

        ttk.Label(options_frame, text="최대 페이지:").pack(side=tk.LEFT, padx=5)
        self.max_pages_spin = ttk.Spinbox(options_frame, from_=1, to=100, width=10)
        self.max_pages_spin.set(5)
        self.max_pages_spin.pack(side=tk.LEFT, padx=5)

        self.pagination_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="페이지네이션 처리", variable=self.pagination_var
        ).pack(side=tk.LEFT, padx=20)

        # 속도 조절 옵션
        speed_frame = ttk.Frame(request_frame)
        speed_frame.pack(fill=tk.X, pady=5)

        ttk.Label(speed_frame, text="크롤링 속도 조절:").pack(side=tk.LEFT, padx=5)

        # 아이템 간 딜레이
        ttk.Label(speed_frame, text="아이템 딜레이(초):").pack(side=tk.LEFT, padx=5)
        self.item_delay_spin = ttk.Spinbox(speed_frame, from_=0, to=10, increment=0.1, width=10)
        self.item_delay_spin.set(0.0)
        self.item_delay_spin.pack(side=tk.LEFT, padx=5)

        # 페이지 간 딜레이
        ttk.Label(speed_frame, text="페이지 딜레이(초):").pack(side=tk.LEFT, padx=10)
        self.page_delay_spin = ttk.Spinbox(speed_frame, from_=0, to=30, increment=0.5, width=10)
        self.page_delay_spin.set(1.0)
        self.page_delay_spin.pack(side=tk.LEFT, padx=5)

        # 설명
        ttk.Label(speed_frame, text="💡 서버 부하 방지", foreground="gray").pack(side=tk.LEFT, padx=10)

        # 실행 버튼
        button_frame = ttk.Frame(request_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame, text="1️⃣ 전략 생성 (분석)", command=self.generate_strategy
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, text="2️⃣ 데이터 추출", command=self.extract_data
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, text="⚡ 한번에 실행", command=self.run_full_crawling
        ).pack(side=tk.LEFT, padx=5)

        # 로그
        log_frame = ttk.LabelFrame(frame, text="로그", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def create_results_tab(self, notebook: ttk.Notebook):
        """결과 탭 생성"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📊 결과")

        # 통계
        stats_frame = ttk.LabelFrame(frame, text="통계", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)

        self.stats_label = ttk.Label(stats_frame, text="데이터 없음")
        self.stats_label.pack(anchor=tk.W)

        # 미리보기
        preview_frame = ttk.LabelFrame(frame, text="데이터 미리보기", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # 내보내기
        export_frame = ttk.LabelFrame(frame, text="내보내기", padding=10)
        export_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(export_frame, text="JSON으로 저장", command=lambda: self.export_data('json')).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(export_frame, text="CSV로 저장", command=lambda: self.export_data('csv')).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(export_frame, text="Excel로 저장", command=lambda: self.export_data('excel')).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(export_frame, text="모든 형식으로 저장", command=lambda: self.export_data('all')).pack(
            side=tk.LEFT, padx=5
        )

    def create_dom_viewer_tab(self, notebook: ttk.Notebook):
        """DOM 구조 뷰어 탭 생성 (F12처럼 페이지 구조 보기)"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🔍 DOM 구조")

        # 설명
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(
            info_frame,
            text="현재 페이지의 DOM 구조를 확인하세요 (F12 개발자 도구와 유사)",
            font=("", 10, "bold")
        ).pack(anchor=tk.W)

        # 버튼
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(button_frame, text="🔄 페이지 구조 분석", command=self.analyze_page_structure).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="📋 HTML 복사", command=self.copy_html).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="💾 HTML 저장", command=self.save_html).pack(
            side=tk.LEFT, padx=5
        )

        # DOM 구조 표시
        dom_frame = ttk.LabelFrame(frame, text="페이지 구조 요약", padding=10)
        dom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.dom_text = scrolledtext.ScrolledText(dom_frame, wrap=tk.WORD)
        self.dom_text.pack(fill=tk.BOTH, expand=True)

    def create_browser_control_tab(self, notebook: ttk.Notebook):
        """브라우저 원격 제어 탭 생성"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🎮 브라우저 제어")

        # 설명
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(
            info_frame,
            text="브라우저를 원격으로 제어하고 JavaScript를 실행하세요",
            font=("", 10, "bold")
        ).pack(anchor=tk.W)

        # 기본 제어
        control_frame = ttk.LabelFrame(frame, text="기본 제어", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        # 네비게이션
        nav_frame = ttk.Frame(control_frame)
        nav_frame.pack(fill=tk.X, pady=5)

        ttk.Button(nav_frame, text="◀ 뒤로", command=self.browser_back).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="▶ 앞으로", command=self.browser_forward).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="🔄 새로고침", command=self.browser_reload).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="📸 스크린샷", command=self.take_screenshot).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="📍 현재 URL", command=self.show_current_url).pack(side=tk.LEFT, padx=5)

        # JavaScript 실행
        js_frame = ttk.LabelFrame(frame, text="JavaScript 실행", padding=10)
        js_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(js_frame, text="JavaScript 코드를 입력하세요:").pack(anchor=tk.W, pady=5)

        self.js_text = scrolledtext.ScrolledText(js_frame, height=8, wrap=tk.WORD)
        self.js_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.js_text.insert("1.0", "// 예시: document.title")

        js_button_frame = ttk.Frame(js_frame)
        js_button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(js_button_frame, text="▶️ 실행", command=self.execute_javascript).pack(side=tk.LEFT, padx=5)
        ttk.Button(js_button_frame, text="🗑️ 지우기", command=lambda: self.js_text.delete("1.0", tk.END)).pack(
            side=tk.LEFT, padx=5
        )

        # 결과
        result_frame = ttk.LabelFrame(frame, text="실행 결과", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.js_result_text = scrolledtext.ScrolledText(result_frame, height=6, wrap=tk.WORD)
        self.js_result_text.pack(fill=tk.BOTH, expand=True)

    # === 이벤트 핸들러 ===

    def initialize_llm(self):
        """LLM 초기화"""
        api_key = self.config.get('openai_api_key')
        if api_key:
            try:
                self.llm_analyzer = LLMAnalyzer(api_key)
                self.log("LLM 초기화 완료")
            except Exception as e:
                self.log(f"LLM 초기화 실패: {e}")

    def load_models(self):
        """사용 가능한 모델 목록 불러오기"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("오류", "API Key를 입력하세요")
            return

        self.status_var.set("모델 목록 불러오는 중...")
        threading.Thread(target=self._load_models_thread, args=(api_key,), daemon=True).start()

    def _load_models_thread(self, api_key: str):
        """모델 목록 불러오기 (백그라운드)"""
        try:
            analyzer = LLMAnalyzer(api_key)
            models = analyzer.list_available_models()

            self.root.after(0, lambda: self.model_combo.config(values=models))
            if models:
                self.root.after(0, lambda: self.model_combo.current(0))

            self.root.after(0, lambda: self.status_var.set("모델 목록 불러오기 완료"))
            self.log(f"{len(models)}개 모델 불러오기 완료")

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"모델 불러오기 실패: {e}"))
            self.root.after(0, lambda: self.status_var.set("준비"))

    def save_settings(self):
        """설정 저장"""
        api_key = self.api_key_entry.get().strip()
        model = self.model_combo.get()

        if not api_key:
            messagebox.showerror("오류", "API Key를 입력하세요")
            return

        self.config['openai_api_key'] = api_key
        if model:
            self.config['default_model'] = model

        if self.save_config():
            self.initialize_llm()
            messagebox.showinfo("완료", "설정이 저장되었습니다\nconfig.json 파일에 저장되었습니다")
            self.log("설정 저장 완료")
        else:
            messagebox.showerror("오류", "설정 저장에 실패했습니다")

    def connect_browser(self):
        """브라우저 연결"""
        mode = self.browser_mode.get()

        self.status_var.set("브라우저 연결 중...")
        threading.Thread(target=self._connect_browser_thread, args=(mode,), daemon=True).start()

    def _connect_browser_thread(self, mode: str):
        """브라우저 연결 (백그라운드)"""
        try:
            self.browser_connector = BrowserConnector(self.config)

            if mode == "new":
                self.browser_connector.start_new_browser(headless=False)
                self.log("새 브라우저 시작 완료")
            else:
                cdp_url = self.cdp_url_entry.get().strip()
                self.browser_connector.connect_to_existing_browser(cdp_url)
                self.log(f"기존 브라우저 연결 완료: {cdp_url}")

            self.root.after(0, lambda: self.status_var.set("브라우저 연결됨"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"브라우저 연결 실패: {e}"))
            self.root.after(0, lambda: self.status_var.set("준비"))
            logger.error(f"브라우저 연결 실패: {e}")

    def disconnect_browser(self):
        """브라우저 연결 해제"""
        if self.browser_connector:
            self.browser_connector.close()
            self.browser_connector = None
            self.log("브라우저 연결 해제")
            self.status_var.set("준비")

    def navigate_to_url(self):
        """URL로 이동"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("오류", "URL을 입력하세요")
            return

        threading.Thread(target=self._navigate_thread, args=(url,), daemon=True).start()

    def _navigate_thread(self, url: str):
        """URL 이동 (백그라운드)"""
        try:
            self.root.after(0, lambda: self.status_var.set(f"이동 중: {url}"))
            self.browser_connector.navigate_to(url)
            self.log(f"페이지 이동 완료: {url}")
            self.root.after(0, lambda: self.status_var.set("준비"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"페이지 이동 실패: {e}"))
            self.root.after(0, lambda: self.status_var.set("준비"))

    def generate_strategy(self):
        """크롤링 전략 생성"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        if not self.llm_analyzer:
            messagebox.showerror("오류", "먼저 OpenAI API를 설정하세요")
            return

        request = self.request_text.get("1.0", tk.END).strip()
        if not request or request == "예시: 게시판의 제목, 작성자, 날짜를 모두 수집해주세요":
            messagebox.showerror("오류", "크롤링 요청을 입력하세요")
            return

        threading.Thread(target=self._generate_strategy_thread, args=(request,), daemon=True).start()

    def _generate_strategy_thread(self, request: str):
        """전략 생성 (백그라운드)"""
        try:
            self.root.after(0, lambda: self.status_var.set("페이지 분석 중..."))

            # DOM 추출
            extractor = DOMExtractor(self.browser_connector.page)
            page_html = extractor.get_full_html()

            self.log("LLM 분석 중...")
            self.root.after(0, lambda: self.status_var.set("LLM 분석 중..."))

            # LLM 분석
            strategy = self.llm_analyzer.generate_selectors_from_html(page_html, request)
            self.current_strategy = strategy

            self.log("크롤링 전략 생성 완료:")
            self.log(json.dumps(strategy, ensure_ascii=False, indent=2))

            self.root.after(0, lambda: self.status_var.set("전략 생성 완료"))
            self.root.after(0, lambda: messagebox.showinfo(
                "완료", "크롤링 전략이 생성되었습니다.\n이제 '데이터 추출' 버튼을 클릭하세요."
            ))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"전략 생성 실패: {e}"))
            self.root.after(0, lambda: self.status_var.set("준비"))
            logger.error(f"전략 생성 실패: {e}")

    def extract_data(self):
        """데이터 추출"""
        if not self.current_strategy:
            messagebox.showerror("오류", "먼저 크롤링 전략을 생성하세요")
            return

        threading.Thread(target=self._extract_data_thread, daemon=True).start()

    def _extract_data_thread(self):
        """데이터 추출 (백그라운드)"""
        try:
            self.root.after(0, lambda: self.status_var.set("데이터 추출 중..."))

            # 속도 조절 파라미터 가져오기
            item_delay = float(self.item_delay_spin.get())
            page_delay = float(self.page_delay_spin.get())

            extractor = DataExtractor(self.browser_connector.page, item_delay=item_delay)

            # 페이지네이션 처리 여부
            if self.pagination_var.get():
                max_pages = int(self.max_pages_spin.get())
                data = extractor.extract_with_pagination(
                    self.current_strategy,
                    max_pages=max_pages,
                    delay=page_delay
                )
            else:
                data = extractor.extract_data(self.current_strategy)

            self.extracted_data = data

            self.log(f"데이터 추출 완료: {len(data)}개 아이템")
            self.root.after(0, lambda: self.update_results())
            self.root.after(0, lambda: self.status_var.set(f"{len(data)}개 아이템 추출 완료"))

            self.root.after(0, lambda: messagebox.showinfo(
                "완료", f"{len(data)}개 아이템이 추출되었습니다.\n'결과' 탭에서 확인하세요."
            ))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"데이터 추출 실패: {e}"))
            self.root.after(0, lambda: self.status_var.set("준비"))
            logger.error(f"데이터 추출 실패: {e}")

    def run_full_crawling(self):
        """전체 크롤링 실행 (전략 생성 + 데이터 추출)"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        if not self.llm_analyzer:
            messagebox.showerror("오류", "먼저 OpenAI API를 설정하세요")
            return

        request = self.request_text.get("1.0", tk.END).strip()
        if not request or request == "예시: 게시판의 제목, 작성자, 날짜를 모두 수집해주세요":
            messagebox.showerror("오류", "크롤링 요청을 입력하세요")
            return

        threading.Thread(target=self._run_full_crawling_thread, args=(request,), daemon=True).start()

    def _run_full_crawling_thread(self, request: str):
        """전체 크롤링 (백그라운드)"""
        try:
            # 1. 전략 생성
            self._generate_strategy_thread(request)

            # 잠시 대기
            import time
            time.sleep(1)

            # 2. 데이터 추출
            if self.current_strategy:
                self._extract_data_thread()

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"크롤링 실패: {e}"))
            self.root.after(0, lambda: self.status_var.set("준비"))

    def update_results(self):
        """결과 탭 업데이트"""
        exporter = DataExporter()

        # 통계 업데이트
        stats = exporter.get_statistics(self.extracted_data)
        stats_text = f"총 아이템: {stats['total_items']}개\n\n필드별 통계:\n"
        for field, info in stats.get('fields', {}).items():
            stats_text += f"  - {field}: {info['non_null_count']}/{info['total_count']} ({info['coverage']:.1f}%)\n"

        self.stats_label.config(text=stats_text)

        # 미리보기 업데이트
        preview = exporter.preview_data(self.extracted_data, max_items=10)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", preview)

    def export_data(self, format_type: str):
        """데이터 내보내기"""
        if not self.extracted_data:
            messagebox.showerror("오류", "추출된 데이터가 없습니다")
            return

        exporter = DataExporter()

        try:
            if format_type == 'all':
                results = exporter.export_to_all_formats(self.extracted_data)
                message = "저장된 파일:\n" + "\n".join([f"- {fmt}: {path}" for fmt, path in results.items()])
                messagebox.showinfo("완료", message)
                self.log(f"모든 형식으로 내보내기 완료")

            else:
                if format_type == 'json':
                    filepath = exporter.export_to_json(self.extracted_data)
                elif format_type == 'csv':
                    filepath = exporter.export_to_csv(self.extracted_data)
                elif format_type == 'excel':
                    filepath = exporter.export_to_excel(self.extracted_data)

                messagebox.showinfo("완료", f"저장 완료:\n{filepath}")
                self.log(f"{format_type.upper()} 내보내기 완료: {filepath}")

        except Exception as e:
            messagebox.showerror("오류", f"내보내기 실패: {e}")

    # === 새로운 기능 핸들러 ===

    def analyze_page_structure(self):
        """페이지 구조 분석 (DOM 뷰어)"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        threading.Thread(target=self._analyze_page_structure_thread, daemon=True).start()

    def _analyze_page_structure_thread(self):
        """페이지 구조 분석 (백그라운드)"""
        try:
            self.root.after(0, lambda: self.status_var.set("페이지 구조 분석 중..."))

            extractor = DOMExtractor(self.browser_connector.page)
            summary = extractor.get_page_structure_summary()

            # 상세 정보 추가
            html = extractor.get_full_html()
            summary += f"\n\n전체 HTML 크기: {len(html):,} bytes"
            summary += f"\n현재 URL: {self.browser_connector.get_current_url()}"

            self.root.after(0, lambda: self.dom_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.dom_text.insert("1.0", summary))

            self.log("페이지 구조 분석 완료")
            self.root.after(0, lambda: self.status_var.set("준비"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"페이지 분석 실패: {e}"))
            self.root.after(0, lambda: self.status_var.set("준비"))

    def copy_html(self):
        """HTML을 클립보드에 복사"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        try:
            extractor = DOMExtractor(self.browser_connector.page)
            html = extractor.get_full_html()

            self.root.clipboard_clear()
            self.root.clipboard_append(html)
            messagebox.showinfo("완료", "HTML이 클립보드에 복사되었습니다")
            self.log("HTML 클립보드 복사 완료")

        except Exception as e:
            messagebox.showerror("오류", f"HTML 복사 실패: {e}")

    def save_html(self):
        """HTML을 파일로 저장"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        try:
            from datetime import datetime
            default_name = f"page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

            filepath = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
                initialfile=default_name
            )

            if filepath:
                extractor = DOMExtractor(self.browser_connector.page)
                html = extractor.get_full_html()

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html)

                messagebox.showinfo("완료", f"HTML 저장 완료:\n{filepath}")
                self.log(f"HTML 저장: {filepath}")

        except Exception as e:
            messagebox.showerror("오류", f"HTML 저장 실패: {e}")

    def browser_back(self):
        """브라우저 뒤로 가기"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        try:
            self.browser_connector.page.go_back()
            self.log("뒤로 가기")
        except Exception as e:
            messagebox.showerror("오류", f"뒤로 가기 실패: {e}")

    def browser_forward(self):
        """브라우저 앞으로 가기"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        try:
            self.browser_connector.page.go_forward()
            self.log("앞으로 가기")
        except Exception as e:
            messagebox.showerror("오류", f"앞으로 가기 실패: {e}")

    def browser_reload(self):
        """브라우저 새로고침"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        try:
            self.browser_connector.page.reload()
            self.log("새로고침")
        except Exception as e:
            messagebox.showerror("오류", f"새로고침 실패: {e}")

    def take_screenshot(self):
        """스크린샷 저장"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        try:
            from datetime import datetime
            default_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                initialfile=default_name
            )

            if filepath:
                self.browser_connector.take_screenshot(filepath)
                messagebox.showinfo("완료", f"스크린샷 저장 완료:\n{filepath}")
                self.log(f"스크린샷 저장: {filepath}")

        except Exception as e:
            messagebox.showerror("오류", f"스크린샷 실패: {e}")

    def show_current_url(self):
        """현재 URL 표시"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        try:
            url = self.browser_connector.get_current_url()
            messagebox.showinfo("현재 URL", url)
            self.log(f"현재 URL: {url}")
        except Exception as e:
            messagebox.showerror("오류", f"URL 조회 실패: {e}")

    def execute_javascript(self):
        """JavaScript 실행"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        js_code = self.js_text.get("1.0", tk.END).strip()
        if not js_code or js_code == "// 예시: document.title":
            messagebox.showerror("오류", "JavaScript 코드를 입력하세요")
            return

        try:
            result = self.browser_connector.execute_script(js_code)

            # 결과 표시
            self.js_result_text.delete("1.0", tk.END)
            self.js_result_text.insert("1.0", f"결과:\n{result}")

            self.log(f"JavaScript 실행 완료")

        except Exception as e:
            self.js_result_text.delete("1.0", tk.END)
            self.js_result_text.insert("1.0", f"오류:\n{e}")
            messagebox.showerror("오류", f"JavaScript 실행 실패: {e}")

    def launch_chrome_cdp(self):
        """Chrome을 CDP 모드로 자동 실행"""
        try:
            system = platform.system()
            port = "9222"
            user_data_dir = os.path.join(os.path.expanduser("~"), "chrome-crawler-profile")

            # OS별 Chrome 경로 및 실행 명령
            if system == "Windows":
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.join(os.getenv('LOCALAPPDATA', ''), r"Google\Chrome\Application\chrome.exe")
                ]
                chrome_path = next((p for p in chrome_paths if os.path.exists(p)), None)

                if not chrome_path:
                    messagebox.showerror(
                        "오류",
                        "Chrome을 찾을 수 없습니다.\n\n수동으로 실행하세요:\nchrome.exe --remote-debugging-port=9222"
                    )
                    return

                cmd = [chrome_path, f"--remote-debugging-port={port}", f"--user-data-dir={user_data_dir}"]

            elif system == "Darwin":  # macOS
                chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                if not os.path.exists(chrome_path):
                    messagebox.showerror(
                        "오류",
                        "Chrome을 찾을 수 없습니다.\n\n수동으로 실행하세요:\n" +
                        "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome " +
                        f"--remote-debugging-port={port}"
                    )
                    return

                cmd = [chrome_path, f"--remote-debugging-port={port}", f"--user-data-dir={user_data_dir}"]

            else:  # Linux
                chrome_paths = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
                chrome_path = None
                for path in chrome_paths:
                    try:
                        subprocess.run([path, "--version"], capture_output=True, check=True)
                        chrome_path = path
                        break
                    except:
                        continue

                if not chrome_path:
                    messagebox.showerror(
                        "오류",
                        "Chrome을 찾을 수 없습니다.\n\n수동으로 실행하세요:\n" +
                        f"google-chrome --remote-debugging-port={port}"
                    )
                    return

                cmd = [chrome_path, f"--remote-debugging-port={port}", f"--user-data-dir={user_data_dir}"]

            # Chrome 실행
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            self.log(f"Chrome CDP 모드로 실행됨 (포트 {port})")
            messagebox.showinfo(
                "성공",
                f"Chrome이 CDP 모드로 실행되었습니다!\n\n" +
                f"포트: {port}\n\n" +
                "잠시 후 '🔗 브라우저 연결' 버튼을 클릭하세요."
            )

            # CDP URL 자동 입력
            self.cdp_url_entry.delete(0, tk.END)
            self.cdp_url_entry.insert(0, f"http://localhost:{port}")

        except Exception as e:
            messagebox.showerror("오류", f"Chrome 실행 실패:\n{e}\n\n수동으로 실행해주세요.")
            logger.error(f"Chrome CDP 실행 실패: {e}")

    def log(self, message: str):
        """로그 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        logger.info(message)


def run_gui():
    """GUI 실행"""
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    root = tk.Tk()
    app = CrawlerApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
