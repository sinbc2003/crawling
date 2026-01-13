"""
브라우저 연결 모듈
Playwright를 사용하여 새 브라우저를 열거나 기존 브라우저에 연결
"""

from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class BrowserConnector:
    """브라우저 연결 및 제어 클래스"""

    def __init__(self, config: Dict):
        self.config = config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start_new_browser(self, headless: bool = False) -> Page:
        """
        새 브라우저 인스턴스 시작

        Args:
            headless: 헤드리스 모드 여부

        Returns:
            Page 객체
        """
        logger.info("새 브라우저 시작 중...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=['--start-maximized']
        )
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = self.context.new_page()
        logger.info("브라우저 시작 완료")
        return self.page

    def connect_to_existing_browser(self, cdp_url: str) -> Page:
        """
        기존 브라우저에 연결 (Chrome DevTools Protocol)

        Chrome을 다음 명령으로 실행해야 함:
        chrome.exe --remote-debugging-port=9222

        Args:
            cdp_url: CDP URL (예: http://localhost:9222)

        Returns:
            Page 객체
        """
        logger.info(f"기존 브라우저에 연결 중... ({cdp_url})")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.connect_over_cdp(cdp_url)

        # 기존 컨텍스트와 페이지 사용
        contexts = self.browser.contexts
        if contexts:
            self.context = contexts[0]
            pages = self.context.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = self.context.new_page()
        else:
            self.context = self.browser.new_context()
            self.page = self.context.new_page()

        logger.info("브라우저 연결 완료")
        return self.page

    def navigate_to(self, url: str) -> None:
        """
        URL로 이동

        Args:
            url: 이동할 URL
        """
        if not self.page:
            raise RuntimeError("브라우저가 연결되지 않았습니다")

        logger.info(f"페이지 이동: {url}")
        self.page.goto(url, wait_until='networkidle')

    def get_current_url(self) -> str:
        """현재 페이지 URL 반환"""
        if not self.page:
            raise RuntimeError("브라우저가 연결되지 않았습니다")
        return self.page.url

    def wait_for_selector(self, selector: str, timeout: int = 30000) -> None:
        """
        특정 selector가 나타날 때까지 대기

        Args:
            selector: CSS selector
            timeout: 타임아웃 (ms)
        """
        if not self.page:
            raise RuntimeError("브라우저가 연결되지 않았습니다")
        self.page.wait_for_selector(selector, timeout=timeout)

    def execute_script(self, script: str):
        """
        JavaScript 실행

        Args:
            script: 실행할 JavaScript 코드

        Returns:
            스크립트 실행 결과
        """
        if not self.page:
            raise RuntimeError("브라우저가 연결되지 않았습니다")
        return self.page.evaluate(script)

    def take_screenshot(self, path: str) -> None:
        """
        스크린샷 저장

        Args:
            path: 저장할 파일 경로
        """
        if not self.page:
            raise RuntimeError("브라우저가 연결되지 않았습니다")
        self.page.screenshot(path=path, full_page=True)
        logger.info(f"스크린샷 저장: {path}")

    def close(self) -> None:
        """브라우저 연결 종료"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("브라우저 연결 종료")
