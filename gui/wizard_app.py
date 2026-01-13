"""
개선된 GUI - 단계별 워크플로우
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
from src.detail_extractor import DetailExtractor
from src.strategy_manager import StrategyManager
from src.vision_detector import VisionDetector
from src.exporter import DataExporter

logger = logging.getLogger(__name__)


class WizardCrawlerApp:
    """단계별 워크플로우 크롤러 GUI"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🕷️ AI 웹 크롤러 - 프로젝트 관리")
        self.root.geometry("1400x800")

        # 상태 변수
        self.config = self.load_config()
        self.browser_connector: Optional[BrowserConnector] = None
        self.llm_analyzer: Optional[LLMAnalyzer] = None
        self.vision_detector: Optional[VisionDetector] = None
        self.strategy_manager = StrategyManager()
        self.current_strategy: Optional[Dict] = None
        self.current_project: Optional[Dict] = None
        self.extracted_data: List[Dict] = []
        self.current_step = 0

        # 새 기능 플래그
        self.use_detail_extraction = tk.BooleanVar(value=False)
        self.use_vision_analysis = tk.BooleanVar(value=False)

        # 프로젝트 리스트박스 참조
        self.project_listbox = None

        # GUI 생성
        self.create_ui()

        # 초기화
        self.initialize_llm()
        self.load_projects()

    def load_config(self) -> Dict:
        """설정 파일 로드"""
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 기본 설정
        default_config = {
            "openai_api_key": "",
            "default_model": "gpt-4-turbo-preview",
            "browser": {"headless": False, "timeout": 30000},
            "crawler": {"max_pages": 10, "delay_between_pages": 1000}
        }

        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
        except:
            pass

        return default_config

    def save_config(self) -> bool:
        """설정 저장"""
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")
            return False

    def create_ui(self):
        """사이드바가 있는 UI 생성"""
        # 메인 컨테이너 (좌우 분할)
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 좌측: 프로젝트 사이드바
        self.create_sidebar(main_container)

        # 구분선
        separator = ttk.Separator(main_container, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # 우측: 메인 영역 (기존 wizard)
        right_container = ttk.Frame(main_container)
        right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 상단: 단계 표시
        self.create_step_indicator(right_container)

        # 중앙: 메인 컨텐츠 영역
        self.content_frame = ttk.Frame(right_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 하단: 네비게이션 버튼
        self.create_navigation(right_container)

        # 상태바
        self.status_var = tk.StringVar(value="준비")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 첫 번째 단계 표시
        self.show_step(0)

    def create_wizard(self):
        """하위 호환성을 위한 별칭"""
        self.create_ui()

    def create_sidebar(self, parent):
        """프로젝트 사이드바 생성"""
        sidebar = ttk.Frame(parent, width=280)
        sidebar.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        sidebar.pack_propagate(False)  # 고정 너비 유지

        # 헤더
        header_frame = ttk.Frame(sidebar)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="📁 저장된 프로젝트",
            font=("", 12, "bold")
        ).pack(side=tk.LEFT, padx=5)

        # 새 프로젝트 버튼
        ttk.Button(
            header_frame,
            text="+",
            width=3,
            command=self.new_project
        ).pack(side=tk.RIGHT, padx=2)

        # 검색 바
        search_frame = ttk.Frame(sidebar)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_projects())

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, padx=5)
        search_entry.insert(0, "🔍 검색...")
        search_entry.bind('<FocusIn>', lambda e: search_entry.delete(0, tk.END) if search_entry.get() == "🔍 검색..." else None)

        # 프로젝트 리스트
        list_frame = ttk.Frame(sidebar)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.project_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("", 10),
            selectmode=tk.SINGLE,
            activestyle='none',
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.project_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.project_listbox.yview)

        # 프로젝트 선택 이벤트
        self.project_listbox.bind('<<ListboxSelect>>', self.on_project_select)
        self.project_listbox.bind('<Double-Button-1>', lambda e: self.edit_project())

        # 프로젝트 관리 버튼
        button_frame = ttk.Frame(sidebar)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="✏️ 편집",
            command=self.edit_project,
            width=8
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        ttk.Button(
            button_frame,
            text="🗑️ 삭제",
            command=self.delete_project,
            width=8
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # 현재 프로젝트 정보 표시
        info_frame = ttk.LabelFrame(sidebar, text="ℹ️ 프로젝트 정보", padding=10)
        info_frame.pack(fill=tk.X, pady=(10, 0))

        self.project_info_label = ttk.Label(
            info_frame,
            text="프로젝트를 선택하세요",
            font=("", 9),
            foreground="gray",
            wraplength=250,
            justify=tk.LEFT
        )
        self.project_info_label.pack(anchor=tk.W)

    def create_step_indicator(self, parent):
        """단계 표시 바 생성"""
        indicator_frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        indicator_frame.pack(fill=tk.X, pady=(0, 10))

        self.step_labels = []
        steps = [
            ("1️⃣", "설정", "API 키 입력"),
            ("2️⃣", "연결", "브라우저 연결"),
            ("3️⃣", "크롤링", "데이터 수집"),
            ("4️⃣", "결과", "데이터 확인")
        ]

        for i, (emoji, title, desc) in enumerate(steps):
            frame = ttk.Frame(indicator_frame)
            frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=10)

            label = ttk.Label(
                frame,
                text=f"{emoji} {title}\n{desc}",
                font=("", 10),
                justify=tk.CENTER,
                foreground="gray"
            )
            label.pack()
            self.step_labels.append(label)

        self.update_step_indicator()

    def update_step_indicator(self):
        """단계 표시 업데이트"""
        for i, label in enumerate(self.step_labels):
            if i == self.current_step:
                label.config(foreground="blue", font=("", 10, "bold"))
            elif i < self.current_step:
                label.config(foreground="green", font=("", 10))
            else:
                label.config(foreground="gray", font=("", 10))

    def create_navigation(self, parent):
        """네비게이션 버튼 생성"""
        nav_frame = ttk.Frame(parent)
        nav_frame.pack(fill=tk.X, padx=20, pady=10)

        self.prev_button = ttk.Button(
            nav_frame,
            text="◀ 이전",
            command=self.prev_step,
            state=tk.DISABLED
        )
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = ttk.Button(
            nav_frame,
            text="다음 ▶",
            command=self.next_step
        )
        self.next_button.pack(side=tk.RIGHT, padx=5)

        # 진행 상황 표시
        self.progress_label = ttk.Label(nav_frame, text="1 / 4 단계", font=("", 10))
        self.progress_label.pack(side=tk.RIGHT, padx=20)

    def show_step(self, step: int):
        """특정 단계 표시"""
        # 기존 컨텐츠 제거
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.current_step = step
        self.update_step_indicator()
        self.progress_label.config(text=f"{step + 1} / 4 단계")

        # 단계별 컨텐츠 표시
        if step == 0:
            self.show_setup_step()
        elif step == 1:
            self.show_connection_step()
        elif step == 2:
            self.show_crawling_step()
        elif step == 3:
            self.show_results_step()

        # 버튼 상태 업데이트
        self.prev_button.config(state=tk.NORMAL if step > 0 else tk.DISABLED)
        self.next_button.config(
            text="완료" if step == 3 else "다음 ▶"
        )

    def prev_step(self):
        """이전 단계로"""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def next_step(self):
        """다음 단계로"""
        # 현재 단계 검증
        if self.current_step == 0:
            # Step 1: API 키 확인
            if not self.config.get('openai_api_key'):
                messagebox.showwarning("알림", "먼저 OpenAI API 키를 입력하고 저장하세요")
                return
        elif self.current_step == 1:
            # Step 2: 브라우저 연결 확인
            if not self.browser_connector:
                messagebox.showwarning("알림", "먼저 브라우저를 연결하세요")
                return
        elif self.current_step == 2:
            # Step 3: 데이터 추출 확인
            if not self.extracted_data:
                messagebox.showwarning("알림", "먼저 크롤링을 실행하세요")
                return

        # 마지막 단계에서는 종료
        if self.current_step == 3:
            if messagebox.askyesno("완료", "크롤러를 종료하시겠습니까?"):
                self.root.quit()
            return

        # 다음 단계로
        self.show_step(self.current_step + 1)

    # === Step 1: 설정 ===
    def show_setup_step(self):
        """Step 1: API 키 설정"""
        # 타이틀
        title = ttk.Label(
            self.content_frame,
            text="🔑 OpenAI API 키 설정",
            font=("", 16, "bold")
        )
        title.pack(pady=(0, 10))

        desc = ttk.Label(
            self.content_frame,
            text="크롤링에 AI를 사용하기 위해 OpenAI API 키가 필요합니다",
            foreground="gray"
        )
        desc.pack(pady=(0, 20))

        # API 키 입력
        api_frame = ttk.LabelFrame(self.content_frame, text="API 키 입력", padding=20)
        api_frame.pack(fill=tk.X, pady=10)

        ttk.Label(api_frame, text="API Key:", font=("", 11)).grid(row=0, column=0, sticky=tk.W, pady=10)
        self.api_key_entry = ttk.Entry(api_frame, width=50, show="*", font=("", 10))
        self.api_key_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.EW)
        if self.config.get('openai_api_key'):
            self.api_key_entry.insert(0, self.config['openai_api_key'])

        ttk.Label(api_frame, text="모델:", font=("", 11)).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.model_combo = ttk.Combobox(api_frame, width=47, state='readonly', font=("", 10))
        self.model_combo.grid(row=1, column=1, padx=10, pady=10, sticky=tk.EW)

        api_frame.columnconfigure(1, weight=1)

        # 버튼
        button_frame = ttk.Frame(api_frame)
        button_frame.grid(row=2, column=1, pady=10, sticky=tk.E)

        ttk.Button(button_frame, text="📋 모델 목록 불러오기", command=self.load_models).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="💾 저장", command=self.save_settings).pack(
            side=tk.LEFT, padx=5
        )

        # 가이드
        guide_frame = ttk.LabelFrame(self.content_frame, text="💡 API 키 발급 방법", padding=15)
        guide_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        guide_text = """
1. https://platform.openai.com/api-keys 접속
2. 로그인 (없으면 회원가입)
3. "Create new secret key" 클릭
4. 생성된 키 복사 (sk-로 시작)
5. 위 입력란에 붙여넣기
6. "저장" 클릭

💰 비용: 페이지당 약 $0.01-0.05 (gpt-4 기준)
        """
        ttk.Label(guide_frame, text=guide_text, justify=tk.LEFT, foreground="blue").pack(anchor=tk.W)

    # === Step 2: 브라우저 연결 ===
    def show_connection_step(self):
        """Step 2: 브라우저 연결"""
        title = ttk.Label(
            self.content_frame,
            text="🌐 브라우저 연결",
            font=("", 16, "bold")
        )
        title.pack(pady=(0, 10))

        desc = ttk.Label(
            self.content_frame,
            text="Chrome 브라우저를 연결하여 웹페이지를 크롤링합니다",
            foreground="gray"
        )
        desc.pack(pady=(0, 20))

        # 연결 옵션
        option_frame = ttk.LabelFrame(self.content_frame, text="연결 방법 선택", padding=20)
        option_frame.pack(fill=tk.X, pady=10)

        self.browser_mode = tk.StringVar(value="new")

        # 옵션 1: 새 브라우저
        opt1_frame = ttk.Frame(option_frame)
        opt1_frame.pack(fill=tk.X, pady=10)

        ttk.Radiobutton(
            opt1_frame,
            text="🆕 새 Chrome 브라우저 실행 (권장)",
            variable=self.browser_mode,
            value="new",
            style="Large.TRadiobutton"
        ).pack(side=tk.LEFT)

        ttk.Button(
            opt1_frame,
            text="▶ 실행하기",
            command=self.quick_start_browser
        ).pack(side=tk.RIGHT, padx=10)

        # 옵션 2: 기존 브라우저
        opt2_frame = ttk.Frame(option_frame)
        opt2_frame.pack(fill=tk.X, pady=10)

        ttk.Radiobutton(
            opt2_frame,
            text="🔗 이미 열린 Chrome 연결 (로그인 상태 유지)",
            variable=self.browser_mode,
            value="existing"
        ).pack(side=tk.LEFT)

        # CDP URL
        cdp_frame = ttk.Frame(option_frame)
        cdp_frame.pack(fill=tk.X, pady=10, padx=30)

        ttk.Label(cdp_frame, text="CDP URL:").pack(side=tk.LEFT, padx=5)
        self.cdp_url_entry = ttk.Entry(cdp_frame, width=40)
        self.cdp_url_entry.insert(0, "http://localhost:9222")
        self.cdp_url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(cdp_frame, text="연결", command=self.connect_browser).pack(side=tk.LEFT, padx=5)

        # 상태 표시
        status_frame = ttk.LabelFrame(self.content_frame, text="📊 연결 상태", padding=15)
        status_frame.pack(fill=tk.X, pady=10)

        self.connection_status = ttk.Label(
            status_frame,
            text="❌ 연결 안 됨",
            font=("", 11),
            foreground="red"
        )
        self.connection_status.pack()

        # URL 이동
        url_frame = ttk.LabelFrame(self.content_frame, text="🔗 페이지 이동", padding=15)
        url_frame.pack(fill=tk.X, pady=10)

        ttk.Label(url_frame, text="URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(url_frame, text="이동", command=self.navigate_to_url).pack(side=tk.LEFT, padx=5)

        # 가이드
        guide_frame = ttk.LabelFrame(self.content_frame, text="💡 사용 팁", padding=15)
        guide_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        guide_text = """
📌 새 브라우저 (권장):
   • "실행하기" 버튼만 클릭하면 자동으로 시작됩니다
   • 가장 간단한 방법입니다

📌 기존 브라우저 연결:
   • 이미 로그인한 상태를 유지하고 싶을 때 사용
   • CMD에서 다음 명령 실행 후 "연결" 클릭:
     chrome.exe --remote-debugging-port=9222
        """
        ttk.Label(guide_frame, text=guide_text, justify=tk.LEFT, foreground="blue").pack(anchor=tk.W)

    # === Step 3: 크롤링 ===
    def show_crawling_step(self):
        """Step 3: 크롤링 실행"""
        title = ttk.Label(
            self.content_frame,
            text="🕷️ 데이터 크롤링",
            font=("", 16, "bold")
        )
        title.pack(pady=(0, 10))

        desc = ttk.Label(
            self.content_frame,
            text="자연어로 원하는 데이터를 설명하면 AI가 자동으로 수집합니다",
            foreground="gray"
        )
        desc.pack(pady=(0, 20))

        # 크롤링 요청
        request_frame = ttk.LabelFrame(self.content_frame, text="📝 수집할 데이터 설명", padding=15)
        request_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Label(
            request_frame,
            text="원하는 데이터를 자연어로 설명하세요:",
            font=("", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.request_text = scrolledtext.ScrolledText(request_frame, height=4, wrap=tk.WORD, font=("", 10))
        self.request_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.request_text.insert("1.0", "예시:\n- 게시판의 모든 정보를 수집해줘\n- 제목, 작성자, 날짜, 조회수를 가져와줘")

        # 옵션
        option_frame = ttk.LabelFrame(self.content_frame, text="⚙️ 크롤링 옵션", padding=15)
        option_frame.pack(fill=tk.X, pady=10)

        # 첫 번째 줄
        row1 = ttk.Frame(option_frame)
        row1.pack(fill=tk.X, pady=5)

        ttk.Label(row1, text="최대 페이지:").pack(side=tk.LEFT, padx=5)
        self.max_pages_spin = ttk.Spinbox(row1, from_=1, to=100, width=10)
        self.max_pages_spin.set(5)
        self.max_pages_spin.pack(side=tk.LEFT, padx=5)

        self.pagination_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row1, text="자동 페이지 넘김", variable=self.pagination_var).pack(
            side=tk.LEFT, padx=20
        )

        # 두 번째 줄 - 속도
        row2 = ttk.Frame(option_frame)
        row2.pack(fill=tk.X, pady=5)

        ttk.Label(row2, text="수집 속도:").pack(side=tk.LEFT, padx=5)

        self.speed_preset = tk.StringVar(value="normal")
        ttk.Radiobutton(row2, text="빠름 ⚡", variable=self.speed_preset, value="fast").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(row2, text="보통 ⏱️", variable=self.speed_preset, value="normal").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(row2, text="안전 🐢", variable=self.speed_preset, value="safe").pack(side=tk.LEFT, padx=10)

        # 세 번째 줄 - 고급 기능
        row3 = ttk.Frame(option_frame)
        row3.pack(fill=tk.X, pady=5)

        ttk.Checkbutton(
            row3,
            text="🔍 각 게시글 자동 클릭하여 상세 내용 수집 (게시판 추천)",
            variable=self.use_detail_extraction
        ).pack(side=tk.LEFT, padx=5)

        # 네 번째 줄 - Vision AI
        row4 = ttk.Frame(option_frame)
        row4.pack(fill=tk.X, pady=5)

        ttk.Checkbutton(
            row4,
            text="👁️ Vision AI로 화면 분석 (더 정확, 비용 증가)",
            variable=self.use_vision_analysis
        ).pack(side=tk.LEFT, padx=5)

        # 다섯 번째 줄 - SPA 옵션 (목록 버튼)
        row5 = ttk.Frame(option_frame)
        row5.pack(fill=tk.X, pady=5)

        ttk.Label(row5, text="🔙 목록 버튼 (SPA용):", font=("", 9)).pack(side=tk.LEFT, padx=5)
        self.back_button_entry = ttk.Entry(row5, width=40, font=("", 9))
        self.back_button_entry.pack(side=tk.LEFT, padx=5)
        self.back_button_entry.insert(0, "자동 감지 (비워두세요)")

        ttk.Label(
            row5,
            text="(URL 고정 페이지용, 예: button.back)",
            font=("", 8),
            foreground="gray"
        ).pack(side=tk.LEFT, padx=5)

        # 안내 메시지
        info_frame = ttk.Frame(option_frame)
        info_frame.pack(fill=tk.X, pady=10)

        ttk.Label(
            info_frame,
            text="💡 크롤링 성공 후 좌측 사이드바에서 '+ 버튼'을 눌러 프로젝트로 저장하세요",
            font=("", 9),
            foreground="blue",
            wraplength=800
        ).pack(side=tk.LEFT, padx=5)

        # 실행 버튼
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(pady=20)

        ttk.Button(
            button_frame,
            text="🚀 크롤링 시작 (한번에 실행)",
            command=self.run_full_crawling,
            style="Big.TButton"
        ).pack()

        # 도움말 (접을 수 있는 섹션)
        help_frame = ttk.LabelFrame(self.content_frame, text="💡 기능 설명 (클릭하여 확장)", padding=10)
        help_frame.pack(fill=tk.X, pady=5)

        help_text_widget = tk.Text(help_frame, height=0, wrap=tk.WORD, font=("", 9), bg="#f0f0f0")
        help_text_widget.pack(fill=tk.X)

        help_text = """
🔍 각 게시글 자동 클릭하여 상세 내용 수집:
   - 게시판 목록에서 각 게시글을 자동으로 클릭하여 상세 내용을 추출합니다
   - 모달 팝업, SPA, 일반 페이지 모두 자동 지원합니다
   - 예: 커뮤니티 게시판, GitHub Issues, 상품 상세 페이지 등

👁️ Vision AI로 화면 분석:
   - 스크린샷을 GPT-4 Vision이 직접 분석하여 요소를 찾습니다
   - HTML 구조가 복잡하거나 동적인 페이지에 유용합니다
   - 비용이 조금 더 들지만 정확도가 높습니다

🔙 목록 버튼 (SPA용):
   - URL이 변하지 않는 Single Page App에서 목록으로 돌아가는 버튼을 지정합니다
   - 비워두면 "목록", "뒤로", "Back" 등의 버튼을 자동으로 찾습니다
   - 자동 감지가 실패하면 CSS selector를 직접 입력하세요
   - 예: button.back, a:has-text("목록"), [data-action="back"]

💾 프로젝트 저장:
   - 한 번 생성한 크롤링 전략을 프로젝트로 저장해서 재사용할 수 있습니다
   - 좌측 사이드바에서 프로젝트를 선택하면 자동으로 로드됩니다
   - 메모 기능으로 크롤링 목적과 주의사항을 기록하세요
        """

        help_text_widget.insert("1.0", help_text)
        help_text_widget.config(state=tk.DISABLED)

        def toggle_help():
            current_height = help_text_widget.cget("height")
            if current_height == 0:
                help_text_widget.config(height=10)
                help_frame.config(text="💡 기능 설명 (클릭하여 축소)")
            else:
                help_text_widget.config(height=0)
                help_frame.config(text="💡 기능 설명 (클릭하여 확장)")

        help_frame.bind("<Button-1>", lambda e: toggle_help())

        # 로그
        log_frame = ttk.LabelFrame(self.content_frame, text="📋 진행 상황", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # === Step 4: 결과 ===
    def show_results_step(self):
        """Step 4: 결과 확인"""
        title = ttk.Label(
            self.content_frame,
            text="📊 크롤링 결과",
            font=("", 16, "bold")
        )
        title.pack(pady=(0, 10))

        # 통계
        stats_frame = ttk.LabelFrame(self.content_frame, text="📈 통계", padding=15)
        stats_frame.pack(fill=tk.X, pady=10)

        self.stats_label = ttk.Label(stats_frame, text="데이터 없음", font=("", 10))
        self.stats_label.pack(anchor=tk.W)

        # 미리보기
        preview_frame = ttk.LabelFrame(self.content_frame, text="👀 데이터 미리보기", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, font=("Consolas", 9))
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # 내보내기
        export_frame = ttk.LabelFrame(self.content_frame, text="💾 데이터 저장", padding=15)
        export_frame.pack(fill=tk.X, pady=10)

        button_row = ttk.Frame(export_frame)
        button_row.pack()

        ttk.Button(button_row, text="📄 JSON", command=lambda: self.export_data('json'), width=12).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_row, text="📊 CSV", command=lambda: self.export_data('csv'), width=12).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_row, text="📗 Excel", command=lambda: self.export_data('excel'), width=12).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_row, text="💼 모든 형식", command=lambda: self.export_data('all'), width=12).pack(
            side=tk.LEFT, padx=5
        )

        # 결과 업데이트
        if self.extracted_data:
            self.update_results()

    # === 이벤트 핸들러 (기존 코드 재사용) ===

    def initialize_llm(self):
        """LLM 초기화"""
        api_key = self.config.get('openai_api_key')
        if api_key:
            try:
                self.llm_analyzer = LLMAnalyzer(api_key)
                self.log("✅ LLM 초기화 완료")
            except Exception as e:
                self.log(f"❌ LLM 초기화 실패: {e}")

    def load_models(self):
        """모델 목록 불러오기"""
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

            self.root.after(0, lambda: self.status_var.set("준비"))
            self.log(f"✅ {len(models)}개 모델 불러오기 완료")

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
            messagebox.showinfo("완료", "✅ 설정이 저장되었습니다!")
            self.log("✅ 설정 저장 완료")
        else:
            messagebox.showerror("오류", "설정 저장 실패")

    def quick_start_browser(self):
        """빠른 브라우저 시작"""
        self.launch_chrome_cdp()
        # 2초 후 자동 연결
        self.root.after(2000, self.auto_connect_browser)

    def auto_connect_browser(self):
        """자동 브라우저 연결"""
        self.browser_mode.set("existing")
        self.connect_browser()

    def launch_chrome_cdp(self):
        """Chrome CDP 실행"""
        try:
            system = platform.system()
            port = "9222"
            user_data_dir = os.path.join(os.path.expanduser("~"), "chrome-crawler-profile")

            if system == "Windows":
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.join(os.getenv('LOCALAPPDATA', ''), r"Google\Chrome\Application\chrome.exe")
                ]
                chrome_path = next((p for p in chrome_paths if os.path.exists(p)), None)

                if not chrome_path:
                    messagebox.showerror("오류", "Chrome을 찾을 수 없습니다")
                    return

                cmd = [chrome_path, f"--remote-debugging-port={port}", f"--user-data-dir={user_data_dir}"]

            elif system == "Darwin":
                chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                if not os.path.exists(chrome_path):
                    messagebox.showerror("오류", "Chrome을 찾을 수 없습니다")
                    return
                cmd = [chrome_path, f"--remote-debugging-port={port}", f"--user-data-dir={user_data_dir}"]

            else:  # Linux
                chrome_paths = ["google-chrome", "google-chrome-stable", "chromium"]
                chrome_path = None
                for path in chrome_paths:
                    try:
                        subprocess.run([path, "--version"], capture_output=True, check=True)
                        chrome_path = path
                        break
                    except:
                        continue

                if not chrome_path:
                    messagebox.showerror("오류", "Chrome을 찾을 수 없습니다")
                    return
                cmd = [chrome_path, f"--remote-debugging-port={port}", f"--user-data-dir={user_data_dir}"]

            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            self.log(f"✅ Chrome CDP 실행 (포트 {port})")
            self.cdp_url_entry.delete(0, tk.END)
            self.cdp_url_entry.insert(0, f"http://localhost:{port}")

        except Exception as e:
            messagebox.showerror("오류", f"Chrome 실행 실패: {e}")
            logger.error(f"Chrome CDP 실행 실패: {e}")

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
                self.log("✅ 새 브라우저 시작 완료")
            else:
                cdp_url = self.cdp_url_entry.get().strip()
                self.browser_connector.connect_to_existing_browser(cdp_url)
                self.log(f"✅ 기존 브라우저 연결 완료")

            self.root.after(0, lambda: self.connection_status.config(
                text="✅ 연결됨",
                foreground="green"
            ))
            self.root.after(0, lambda: self.status_var.set("준비"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"브라우저 연결 실패: {e}"))
            self.root.after(0, lambda: self.status_var.set("준비"))
            logger.error(f"브라우저 연결 실패: {e}")

    def navigate_to_url(self):
        """URL 이동"""
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
            self.log(f"✅ 페이지 이동: {url}")
            self.root.after(0, lambda: self.status_var.set("준비"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"이동 실패: {e}"))
            self.root.after(0, lambda: self.status_var.set("준비"))

    def run_full_crawling(self):
        """전체 크롤링 실행"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        if not self.llm_analyzer:
            messagebox.showerror("오류", "먼저 API를 설정하세요")
            return

        request = self.request_text.get("1.0", tk.END).strip()
        if not request or "예시" in request:
            messagebox.showerror("오류", "크롤링 요청을 입력하세요")
            return

        # HTML 추출
        self.status_var.set("페이지 HTML 추출 중...")
        try:
            extractor = DOMExtractor(self.browser_connector.page)
            page_html = extractor.get_full_html()
            self.log("✅ 페이지 HTML 추출 완료")
        except Exception as e:
            messagebox.showerror("오류", f"HTML 추출 실패: {e}")
            return

        threading.Thread(target=self._run_full_crawling_thread, args=(request, page_html), daemon=True).start()

    def _run_full_crawling_thread(self, request: str, page_html: str):
        """전체 크롤링 (백그라운드)"""
        try:
            # 1. 전략 생성
            self.log("🔍 크롤링 전략 분석 중...")
            self.root.after(0, lambda: self.status_var.set("전략 분석 중..."))

            # Vision AI 사용 여부 확인
            use_vision = self.use_vision_analysis.get()

            if use_vision:
                self.log("👁️ Vision AI로 화면 분석 중... (비용 높음, 정확도 높음)")
                if not self.vision_detector:
                    api_key = self.config.get('openai_api_key')
                    self.vision_detector = VisionDetector(api_key)

                strategy = self.vision_detector.generate_extraction_strategy_from_screenshot(
                    self.browser_connector.page,
                    request
                )
            else:
                self.log("📝 HTML 기반 분석 중... (빠르고 경제적)")
                strategy = self.llm_analyzer.generate_selectors_from_html(page_html, request)

            self.current_strategy = strategy
            self.log("✅ 크롤링 전략 생성 완료")
            self.log(f"   컨테이너: {strategy.get('container_selector', 'N/A')}")
            self.log(f"   필드 개수: {len(strategy.get('fields', []))}개")

            # 2. 데이터 추출
            import time
            time.sleep(1)

            self.log("📥 데이터 추출 중...")
            self.root.after(0, lambda: self.status_var.set("데이터 추출 중..."))

            # 속도 프리셋 적용
            speed = self.speed_preset.get()
            if speed == "fast":
                item_delay, page_delay = 0.0, 0.5
            elif speed == "safe":
                item_delay, page_delay = 0.5, 3.0
            else:  # normal
                item_delay, page_delay = 0.2, 1.5

            # 상세 페이지 자동 추출 여부
            use_detail = self.use_detail_extraction.get()

            if use_detail:
                self.log("🔍 상세 페이지 자동 추출 모드 활성화")

                # 목록 버튼 selector 가져오기
                back_button_text = self.back_button_entry.get().strip()
                back_button_selector = None if back_button_text == "자동 감지 (비워두세요)" or not back_button_text else back_button_text

                if back_button_selector:
                    self.log(f"   목록 버튼 지정: {back_button_selector}")
                else:
                    self.log("   목록 버튼: 자동 감지 모드")

                detail_extractor = DetailExtractor(
                    self.browser_connector.page,
                    item_delay=item_delay,
                    page_delay=page_delay,
                    back_button_selector=back_button_selector,
                    use_smart_waiting=True
                )

                if self.pagination_var.get():
                    max_pages = int(self.max_pages_spin.get())
                    self.log(f"📄 페이지네이션 활성화 (최대 {max_pages}페이지)")
                    data = detail_extractor.extract_with_pagination_and_details(
                        list_strategy=strategy,
                        max_pages=max_pages,
                        progress_callback=self._detail_progress_callback
                    )
                else:
                    self.log("📝 단일 페이지 모드")
                    data = detail_extractor.extract_list_with_details(
                        list_strategy=strategy,
                        progress_callback=self._detail_progress_callback
                    )
            else:
                # 기본 추출 (상세 페이지 없음)
                extractor = DataExtractor(self.browser_connector.page, item_delay=item_delay)

                if self.pagination_var.get():
                    max_pages = int(self.max_pages_spin.get())
                    self.log(f"📄 페이지네이션 활성화 (최대 {max_pages}페이지)")
                    data = extractor.extract_with_pagination(strategy, max_pages=max_pages, delay=page_delay)
                else:
                    self.log("📝 단일 페이지 모드")
                    data = extractor.extract_data(strategy)

            self.extracted_data = data

            self.log(f"✅ 데이터 추출 완료: {len(data)}개 아이템")
            self.root.after(0, lambda: self.status_var.set("완료"))

            # 자동으로 결과 단계로 이동
            self.root.after(0, lambda: messagebox.showinfo(
                "완료",
                f"✅ {len(data)}개 아이템 수집 완료!\n\n'다음' 버튼을 클릭하여 결과를 확인하세요."
            ))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"크롤링 실패: {e}"))
            self.root.after(0, lambda: self.status_var.set("준비"))
            logger.error(f"크롤링 실패: {e}")

    def _detail_progress_callback(self, current: int, total: int, page: int = 1):
        """상세 추출 진행률 콜백"""
        self.log(f"   [{current}/{total}] 상세 페이지 추출 중...")
        self.root.after(0, lambda: self.status_var.set(f"상세 추출 중... ({current}/{total})"))

    def update_results(self):
        """결과 업데이트"""
        exporter = DataExporter()

        # 통계
        stats = exporter.get_statistics(self.extracted_data)
        stats_text = f"📊 총 {stats['total_items']}개 아이템\n\n"
        for field, info in stats.get('fields', {}).items():
            stats_text += f"  • {field}: {info['non_null_count']}/{info['total_count']} ({info['coverage']:.1f}%)\n"

        self.stats_label.config(text=stats_text)

        # 미리보기
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
                message = "저장 완료:\n" + "\n".join([f"✅ {fmt}: {path}" for fmt, path in results.items()])
                messagebox.showinfo("완료", message)
                self.log("✅ 모든 형식 저장 완료")
            else:
                if format_type == 'json':
                    filepath = exporter.export_to_json(self.extracted_data)
                elif format_type == 'csv':
                    filepath = exporter.export_to_csv(self.extracted_data)
                elif format_type == 'excel':
                    filepath = exporter.export_to_excel(self.extracted_data)

                messagebox.showinfo("완료", f"✅ 저장 완료:\n{filepath}")
                self.log(f"✅ {format_type.upper()} 저장: {filepath}")

        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}")

    def save_strategy(self):
        """현재 크롤링 전략 저장"""
        if not self.current_strategy:
            messagebox.showerror("오류", "저장할 전략이 없습니다.\n먼저 크롤링을 실행하세요.")
            return

        if not self.browser_connector:
            messagebox.showerror("오류", "브라우저 정보가 없습니다")
            return

        # 사용자에게 전략 이름 입력 받기
        from tkinter import simpledialog
        strategy_name = simpledialog.askstring(
            "전략 저장",
            "이 전략의 이름을 입력하세요:\n(예: 네이버 카페 게시판, GitHub Issues)"
        )

        if not strategy_name:
            return

        # 설명 입력 받기
        description = simpledialog.askstring(
            "전략 설명",
            "간단한 설명을 입력하세요 (선택사항):",
        )

        try:
            url = self.browser_connector.page.url
            filepath = self.strategy_manager.save_strategy(
                url=url,
                strategy=self.current_strategy,
                name=strategy_name,
                description=description or f"{strategy_name} 크롤링 전략"
            )

            messagebox.showinfo(
                "저장 완료",
                f"✅ 전략이 저장되었습니다!\n\n파일: {filepath}\n\n이 전략은 다음에 같은 사이트를 크롤링할 때 재사용할 수 있습니다."
            )
            self.log(f"✅ 전략 저장 완료: {strategy_name}")

        except Exception as e:
            messagebox.showerror("오류", f"전략 저장 실패: {e}")

    def load_strategy(self):
        """저장된 전략 불러오기"""
        if not self.browser_connector:
            messagebox.showerror("오류", "먼저 브라우저를 연결하세요")
            return

        # 현재 URL로 전략 찾기
        current_url = self.browser_connector.page.url

        # 저장된 전략 목록 가져오기
        strategies = self.strategy_manager.list_strategies()

        if not strategies:
            messagebox.showinfo(
                "알림",
                "저장된 전략이 없습니다.\n\n크롤링을 실행한 후 '전략 저장' 버튼을 눌러 전략을 저장하세요."
            )
            return

        # 전략 선택 다이얼로그 생성
        dialog = tk.Toplevel(self.root)
        dialog.title("전략 선택")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog,
            text="💾 저장된 크롤링 전략 목록",
            font=("", 14, "bold")
        ).pack(pady=10)

        ttk.Label(
            dialog,
            text=f"현재 페이지: {current_url[:80]}...",
            foreground="gray"
        ).pack(pady=5)

        # 리스트박스
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        strategy_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("", 10),
            height=15
        )
        strategy_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=strategy_listbox.yview)

        # 전략 목록 채우기
        for strategy in strategies:
            display_text = f"{strategy['name']} | {strategy['domain']} | {strategy['created_at'][:10]}"
            strategy_listbox.insert(tk.END, display_text)

        # 상세 정보 레이블
        detail_label = ttk.Label(dialog, text="", font=("", 9), foreground="blue", wraplength=650)
        detail_label.pack(pady=5)

        def on_select(event):
            selection = strategy_listbox.curselection()
            if selection:
                idx = selection[0]
                selected = strategies[idx]
                detail_text = f"설명: {selected['description']}\nURL: {selected['url']}"
                detail_label.config(text=detail_text)

        strategy_listbox.bind('<<ListboxSelect>>', on_select)

        # 버튼
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        def load_selected():
            selection = strategy_listbox.curselection()
            if not selection:
                messagebox.showwarning("알림", "전략을 선택하세요")
                return

            idx = selection[0]
            selected = strategies[idx]

            try:
                strategy_data = self.strategy_manager.load_strategy(selected['filepath'])
                self.current_strategy = strategy_data['strategy']

                dialog.destroy()

                messagebox.showinfo(
                    "불러오기 완료",
                    f"✅ 전략 불러오기 완료!\n\n이름: {strategy_data['name']}\n\n이제 '크롤링 시작' 버튼을 눌러 데이터를 수집하세요.\n(자동으로 저장된 selector를 사용합니다)"
                )
                self.log(f"✅ 전략 불러오기: {strategy_data['name']}")

            except Exception as e:
                messagebox.showerror("오류", f"전략 불러오기 실패: {e}")

        ttk.Button(button_frame, text="불러오기", command=load_selected, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)

    # === 프로젝트 관리 기능 ===

    def load_projects(self):
        """저장된 프로젝트 목록 불러오기"""
        if not self.project_listbox:
            return

        self.project_listbox.delete(0, tk.END)
        strategies = self.strategy_manager.list_strategies()

        for strategy in strategies:
            display_name = f"📌 {strategy['name']}"
            self.project_listbox.insert(tk.END, display_name)

        if strategies:
            self.project_listbox.itemconfig(0, bg='#e3f2fd')

    def filter_projects(self):
        """프로젝트 검색 필터"""
        if not self.project_listbox:
            return

        keyword = self.search_var.get().strip()
        if keyword == "🔍 검색..." or not keyword:
            self.load_projects()
            return

        self.project_listbox.delete(0, tk.END)
        strategies = self.strategy_manager.search_strategies(keyword)

        for strategy in strategies:
            display_name = f"📌 {strategy['name']}"
            self.project_listbox.insert(tk.END, display_name)

    def on_project_select(self, event):
        """프로젝트 선택 이벤트"""
        selection = self.project_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        strategies = self.strategy_manager.list_strategies()

        if idx < len(strategies):
            project = strategies[idx]
            self.current_project = project

            # 프로젝트 정보 표시
            info_text = f"📛 이름: {project['name']}\n"
            info_text += f"🌐 URL: {project['url'][:50]}...\n"
            info_text += f"📅 생성일: {project['created_at'][:10]}\n"
            if project.get('notes'):
                info_text += f"\n📝 메모:\n{project['notes']}"

            self.project_info_label.config(text=info_text)

            # 전략 자동 로드
            try:
                strategy_data = self.strategy_manager.load_strategy(project['filepath'])
                self.current_strategy = strategy_data['strategy']
                self.log(f"✅ 프로젝트 로드: {project['name']}")
            except Exception as e:
                logger.error(f"프로젝트 로드 실패: {e}")

    def new_project(self):
        """새 프로젝트 생성"""
        if not self.browser_connector:
            messagebox.showwarning("알림", "먼저 브라우저를 연결한 후 크롤링을 실행하세요")
            return

        if not self.current_strategy:
            messagebox.showwarning("알림", "먼저 크롤링을 실행하여 전략을 생성하세요")
            return

        self.save_strategy_dialog(is_new=True)

    def edit_project(self):
        """프로젝트 편집"""
        if not self.current_project:
            messagebox.showwarning("알림", "편집할 프로젝트를 선택하세요")
            return

        self.save_strategy_dialog(is_new=False)

    def delete_project(self):
        """프로젝트 삭제"""
        if not self.current_project:
            messagebox.showwarning("알림", "삭제할 프로젝트를 선택하세요")
            return

        if not messagebox.askyesno("확인", f"'{self.current_project['name']}' 프로젝트를 삭제하시겠습니까?"):
            return

        try:
            self.strategy_manager.delete_strategy(self.current_project['filepath'])
            messagebox.showinfo("완료", "프로젝트가 삭제되었습니다")
            self.load_projects()
            self.current_project = None
            self.project_info_label.config(text="프로젝트를 선택하세요")
        except Exception as e:
            messagebox.showerror("오류", f"프로젝트 삭제 실패: {e}")

    def save_strategy_dialog(self, is_new=True):
        """전략 저장 다이얼로그"""
        dialog = tk.Toplevel(self.root)
        dialog.title("프로젝트 저장" if is_new else "프로젝트 편집")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        # 프레임
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        ttk.Label(
            main_frame,
            text="💾 프로젝트 정보" if is_new else "✏️ 프로젝트 편집",
            font=("", 14, "bold")
        ).pack(pady=(0, 20))

        # 프로젝트 이름
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(name_frame, text="프로젝트 이름:", font=("", 10, "bold"), width=15).pack(side=tk.LEFT)
        name_entry = ttk.Entry(name_frame, font=("", 10))
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if not is_new and self.current_project:
            name_entry.insert(0, self.current_project['name'])

        # URL (자동 입력, 수정 불가)
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=5)

        ttk.Label(url_frame, text="URL:", font=("", 10, "bold"), width=15).pack(side=tk.LEFT)
        url_entry = ttk.Entry(url_frame, font=("", 9), state='readonly')
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if is_new and self.browser_connector:
            url_entry.config(state='normal')
            url_entry.insert(0, self.browser_connector.page.url)
            url_entry.config(state='readonly')
        elif not is_new and self.current_project:
            url_entry.config(state='normal')
            url_entry.insert(0, self.current_project['url'])
            url_entry.config(state='readonly')

        # 설명
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=5)

        ttk.Label(desc_frame, text="설명:", font=("", 10, "bold"), width=15).pack(side=tk.LEFT, anchor=tk.N)
        desc_text = tk.Text(desc_frame, height=3, wrap=tk.WORD, font=("", 9))
        desc_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if not is_new and self.current_project:
            desc_text.insert("1.0", self.current_project.get('description', ''))

        # 메모 (비고)
        notes_frame = ttk.Frame(main_frame)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(notes_frame, text="📝 메모 (비고):", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(
            notes_frame,
            text="크롤링 목적, 주의사항 등을 자유롭게 메모하세요",
            font=("", 8),
            foreground="gray"
        ).pack(anchor=tk.W)

        notes_text = scrolledtext.ScrolledText(notes_frame, height=8, wrap=tk.WORD, font=("", 9))
        notes_text.pack(fill=tk.BOTH, expand=True)

        if not is_new and self.current_project:
            notes_text.insert("1.0", self.current_project.get('notes', ''))

        # 태그
        tag_frame = ttk.Frame(main_frame)
        tag_frame.pack(fill=tk.X, pady=5)

        ttk.Label(tag_frame, text="태그 (,로 구분):", font=("", 10, "bold"), width=15).pack(side=tk.LEFT)
        tag_entry = ttk.Entry(tag_frame, font=("", 9))
        tag_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if not is_new and self.current_project:
            tags = self.current_project.get('tags', [])
            tag_entry.insert(0, ", ".join(tags))

        # 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("오류", "프로젝트 이름을 입력하세요")
                return

            description = desc_text.get("1.0", tk.END).strip()
            notes = notes_text.get("1.0", tk.END).strip()
            tags_str = tag_entry.get().strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]

            try:
                if is_new:
                    # 새 프로젝트 저장
                    url = self.browser_connector.page.url
                    self.strategy_manager.save_strategy(
                        url=url,
                        strategy=self.current_strategy,
                        name=name,
                        description=description,
                        tags=tags,
                        notes=notes
                    )
                    messagebox.showinfo("완료", "프로젝트가 저장되었습니다!")
                else:
                    # 기존 프로젝트 업데이트
                    self.strategy_manager.update_strategy(
                        filepath=self.current_project['filepath'],
                        name=name,
                        description=description,
                        tags=tags,
                        notes=notes
                    )
                    messagebox.showinfo("완료", "프로젝트가 업데이트되었습니다!")

                self.load_projects()
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("오류", f"저장 실패: {e}")

        ttk.Button(button_frame, text="💾 저장", command=save, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)

    def log(self, message: str):
        """로그 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
        logger.info(message)


def run_wizard_gui():
    """위저드 GUI 실행"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    root = tk.Tk()

    # 스타일 설정
    style = ttk.Style()
    style.configure("Big.TButton", font=("", 12, "bold"), padding=10)
    style.configure("Large.TRadiobutton", font=("", 10))

    app = WizardCrawlerApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_wizard_gui()
