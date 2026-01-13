"""
상세 페이지 자동 추출 모듈
게시판 목록에서 각 게시글을 자동으로 클릭하여 상세 내용 추출
모달 및 SPA 페이지 지원
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from typing import Dict, List, Optional, Callable
import time
import logging

logger = logging.getLogger(__name__)


class DetailExtractor:
    """상세 페이지 자동 추출 클래스"""

    def __init__(self, page: Page, item_delay: float = 0.5, page_delay: float = 1.0):
        """
        Args:
            page: Playwright Page 객체
            item_delay: 각 아이템 클릭 사이의 대기 시간 (초)
            page_delay: 페이지 전환 후 대기 시간 (초)
        """
        self.page = page
        self.item_delay = item_delay
        self.page_delay = page_delay

    def extract_list_with_details(
        self,
        list_strategy: Dict,
        detail_strategy: Optional[Dict] = None,
        max_items: Optional[int] = None,
        detail_link_field: str = "link",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """
        목록 페이지에서 각 아이템을 클릭하여 상세 내용 추출

        Args:
            list_strategy: 목록 페이지 추출 전략 (링크 포함)
            detail_strategy: 상세 페이지 추출 전략 (None이면 자동 감지)
            max_items: 최대 아이템 수
            detail_link_field: 상세 페이지 링크 필드명
            progress_callback: 진행률 콜백 함수(current, total)

        Returns:
            목록 데이터 + 상세 데이터가 합쳐진 리스트
        """
        all_data = []

        # 1단계: 목록 페이지에서 기본 정보 + 링크 추출
        logger.info("목록 페이지에서 링크 추출 중...")
        list_items = self._extract_list_items(list_strategy, max_items)

        if not list_items:
            logger.warning("목록에서 아이템을 찾을 수 없습니다")
            return []

        total_items = len(list_items)
        logger.info(f"총 {total_items}개 아이템 발견")

        # 원본 URL 저장 (되돌아오기 위해)
        original_url = self.page.url

        # 2단계: 각 아이템의 상세 페이지 방문 및 데이터 추출
        for idx, list_item in enumerate(list_items):
            logger.info(f"[{idx+1}/{total_items}] 상세 페이지 추출 중...")

            if progress_callback:
                progress_callback(idx + 1, total_items)

            # 상세 페이지 링크 확인
            detail_link = list_item.get(detail_link_field)

            if not detail_link:
                logger.warning(f"아이템 {idx+1}에 링크가 없습니다")
                all_data.append(list_item)
                continue

            # 상세 페이지 방문 및 데이터 추출
            try:
                detail_data = self._visit_and_extract_detail(
                    detail_link,
                    detail_strategy,
                    original_url
                )

                # 목록 데이터 + 상세 데이터 합치기
                combined_item = {**list_item, **detail_data}
                all_data.append(combined_item)

            except Exception as e:
                logger.error(f"아이템 {idx+1} 상세 추출 실패: {e}")
                # 실패해도 목록 데이터는 추가
                all_data.append(list_item)

            # 속도 조절
            if self.item_delay > 0 and idx < total_items - 1:
                time.sleep(self.item_delay)

        logger.info(f"총 {len(all_data)}개 아이템 추출 완료")
        return all_data

    def _extract_list_items(self, strategy: Dict, max_items: Optional[int] = None) -> List[Dict]:
        """목록 페이지에서 아이템 추출"""
        items = []
        container_selector = strategy.get('container_selector')
        fields = strategy.get('fields', [])

        if not container_selector:
            logger.error("container_selector가 없습니다")
            return []

        try:
            self.page.wait_for_selector(container_selector, timeout=10000)
        except Exception as e:
            logger.warning(f"컨테이너 대기 중 오류: {e}")
            return []

        containers = self.page.query_selector_all(container_selector)

        for idx, container in enumerate(containers):
            if max_items and idx >= max_items:
                break

            item_data = {}

            for field in fields:
                field_name = field.get('name')
                field_selector = field.get('selector')
                field_attribute = field.get('attribute')

                try:
                    element = container.query_selector(field_selector)

                    if element:
                        if field_attribute and field_attribute != 'null':
                            value = element.get_attribute(field_attribute)
                        else:
                            value = element.inner_text().strip()

                        if value:
                            item_data[field_name] = value
                    else:
                        item_data[field_name] = None

                except Exception as e:
                    logger.warning(f"필드 '{field_name}' 추출 실패: {e}")
                    item_data[field_name] = None

            if item_data:
                items.append(item_data)

        return items

    def _visit_and_extract_detail(
        self,
        link: str,
        detail_strategy: Optional[Dict],
        original_url: str
    ) -> Dict:
        """
        상세 페이지 방문 및 데이터 추출
        모달과 일반 페이지 모두 지원
        """
        detail_data = {}

        # 링크가 상대 경로인 경우 절대 경로로 변환
        if link.startswith('/'):
            from urllib.parse import urljoin
            base_url = self.page.url
            link = urljoin(base_url, link)
        elif not link.startswith('http'):
            from urllib.parse import urljoin
            base_url = self.page.url
            link = urljoin(base_url, link)

        # 현재 URL 저장
        current_url = self.page.url

        # 클릭 방식 선택: 링크 클릭 vs 직접 이동
        navigation_method = self._determine_navigation_method(link)

        if navigation_method == 'click':
            # 클릭으로 이동 (모달이 뜰 가능성 있음)
            detail_data = self._click_and_extract(link, detail_strategy, original_url)
        else:
            # 직접 이동 (일반 페이지)
            detail_data = self._navigate_and_extract(link, detail_strategy, original_url)

        return detail_data

    def _determine_navigation_method(self, link: str) -> str:
        """
        링크 클릭 방식 결정: 'click' vs 'navigate'

        - 같은 도메인이면서 JavaScript 링크 패턴이면 click
        - 그 외에는 navigate
        """
        current_url = self.page.url

        # JavaScript 링크 패턴
        if link.startswith('javascript:') or '#' in link:
            return 'click'

        # 같은 도메인 확인
        from urllib.parse import urlparse
        current_domain = urlparse(current_url).netloc
        link_domain = urlparse(link).netloc

        if current_domain == link_domain or not link_domain:
            # 같은 도메인이면 클릭 시도 (모달 가능성)
            return 'click'

        return 'navigate'

    def _click_and_extract(
        self,
        link: str,
        detail_strategy: Optional[Dict],
        original_url: str
    ) -> Dict:
        """
        링크를 클릭하여 상세 내용 추출 (모달 지원)
        """
        detail_data = {}

        try:
            # 링크 엘리먼트 찾기
            link_element = self.page.query_selector(f'a[href="{link}"], a[href*="{link.split("/")[-1]}"]')

            if not link_element:
                # selector로 찾을 수 없으면 직접 이동
                return self._navigate_and_extract(link, detail_strategy, original_url)

            # 현재 URL 저장
            current_url = self.page.url

            # 클릭
            link_element.click()

            # 페이지 로딩 대기
            time.sleep(self.page_delay)

            # URL이 변경되었는지 확인
            new_url = self.page.url
            is_modal = (current_url == new_url)

            if is_modal:
                logger.info("모달 페이지 감지됨")

                # 모달 컨텐츠 추출
                detail_data = self._extract_modal_content(detail_strategy)

                # 모달 닫기
                self._close_modal()

            else:
                logger.info("일반 페이지로 이동됨")

                # 일반 페이지 추출
                detail_data = self._extract_page_content(detail_strategy)

                # 원래 목록 페이지로 돌아가기
                self.page.goto(original_url)
                time.sleep(self.page_delay)

        except Exception as e:
            logger.error(f"클릭 추출 실패: {e}")

        return detail_data

    def _navigate_and_extract(
        self,
        link: str,
        detail_strategy: Optional[Dict],
        original_url: str
    ) -> Dict:
        """
        직접 페이지 이동하여 상세 내용 추출
        """
        detail_data = {}

        try:
            # 상세 페이지로 이동
            self.page.goto(link, wait_until='domcontentloaded', timeout=15000)
            time.sleep(self.page_delay)

            # 데이터 추출
            detail_data = self._extract_page_content(detail_strategy)

            # 원래 목록 페이지로 돌아가기
            self.page.goto(original_url)
            time.sleep(self.page_delay)

        except Exception as e:
            logger.error(f"페이지 이동 추출 실패: {e}")

        return detail_data

    def _extract_modal_content(self, strategy: Optional[Dict]) -> Dict:
        """
        모달에서 컨텐츠 추출
        """
        detail_data = {}

        # 모달 컨테이너 찾기
        modal_selectors = [
            '.modal.show',
            '.modal-dialog',
            '[role="dialog"]',
            '.popup',
            '.overlay'
        ]

        modal_container = None
        for selector in modal_selectors:
            try:
                modal_container = self.page.query_selector(selector)
                if modal_container and modal_container.is_visible():
                    logger.info(f"모달 컨테이너 발견: {selector}")
                    break
            except:
                continue

        if not modal_container:
            logger.warning("모달 컨테이너를 찾을 수 없습니다")
            # 전체 페이지에서 추출 시도
            return self._extract_page_content(strategy)

        # 전략이 있으면 전략대로 추출
        if strategy and strategy.get('fields'):
            for field in strategy['fields']:
                field_name = field.get('name')
                field_selector = field.get('selector')
                field_attribute = field.get('attribute')

                try:
                    element = modal_container.query_selector(field_selector)

                    if element:
                        if field_attribute and field_attribute != 'null':
                            value = element.get_attribute(field_attribute)
                        else:
                            value = element.inner_text().strip()

                        if value:
                            detail_data[field_name] = value

                except Exception as e:
                    logger.warning(f"모달 필드 '{field_name}' 추출 실패: {e}")

        else:
            # 전략이 없으면 주요 컨텐츠 자동 추출
            detail_data = self._auto_extract_content(modal_container)

        return detail_data

    def _extract_page_content(self, strategy: Optional[Dict]) -> Dict:
        """
        일반 페이지에서 컨텐츠 추출
        """
        detail_data = {}

        if strategy and strategy.get('fields'):
            # 전략이 있으면 전략대로 추출
            for field in strategy['fields']:
                field_name = field.get('name')
                field_selector = field.get('selector')
                field_attribute = field.get('attribute')

                try:
                    element = self.page.query_selector(field_selector)

                    if element:
                        if field_attribute and field_attribute != 'null':
                            value = element.get_attribute(field_attribute)
                        else:
                            value = element.inner_text().strip()

                        if value:
                            detail_data[field_name] = value

                except Exception as e:
                    logger.warning(f"필드 '{field_name}' 추출 실패: {e}")

        else:
            # 전략이 없으면 주요 컨텐츠 자동 추출
            detail_data = self._auto_extract_content(self.page)

        return detail_data

    def _auto_extract_content(self, container) -> Dict:
        """
        전략 없이 자동으로 주요 컨텐츠 추출
        제목, 본문, 작성자, 날짜 등 일반적인 필드 탐색
        """
        data = {}

        # 제목 추출 시도
        title_selectors = ['h1', 'h2', '.title', '.subject', '[class*="title"]']
        for selector in title_selectors:
            try:
                element = container.query_selector(selector)
                if element:
                    text = element.inner_text().strip()
                    if text and len(text) > 0:
                        data['detail_title'] = text
                        break
            except:
                continue

        # 본문 추출 시도
        content_selectors = [
            '.content', '.body', 'article', '.post-content',
            '[class*="content"]', '.detail', '.description'
        ]
        for selector in content_selectors:
            try:
                element = container.query_selector(selector)
                if element:
                    text = element.inner_text().strip()
                    if text and len(text) > 20:  # 충분히 긴 텍스트만
                        data['detail_content'] = text
                        break
            except:
                continue

        # 작성자 추출 시도
        author_selectors = ['.author', '.writer', '[class*="author"]', '[class*="writer"]']
        for selector in author_selectors:
            try:
                element = container.query_selector(selector)
                if element:
                    text = element.inner_text().strip()
                    if text:
                        data['detail_author'] = text
                        break
            except:
                continue

        # 날짜 추출 시도
        date_selectors = ['.date', '.time', '[class*="date"]', '[class*="time"]']
        for selector in date_selectors:
            try:
                element = container.query_selector(selector)
                if element:
                    text = element.inner_text().strip()
                    if text:
                        data['detail_date'] = text
                        break
            except:
                continue

        return data

    def _close_modal(self):
        """
        모달 닫기 시도
        """
        # 닫기 버튼 selector 리스트
        close_selectors = [
            '.modal .close',
            '.modal button.close',
            '[data-dismiss="modal"]',
            '.modal-close',
            '.popup-close',
            'button[aria-label="Close"]',
            '.modal .btn-close'
        ]

        for selector in close_selectors:
            try:
                close_button = self.page.query_selector(selector)
                if close_button and close_button.is_visible():
                    close_button.click()
                    time.sleep(0.5)
                    logger.info(f"모달 닫기 성공: {selector}")
                    return
            except:
                continue

        # 버튼으로 닫기 실패하면 ESC 키 시도
        try:
            self.page.keyboard.press('Escape')
            time.sleep(0.5)
            logger.info("ESC 키로 모달 닫기 시도")
        except:
            pass

        # 모달 배경 클릭 시도
        try:
            backdrop = self.page.query_selector('.modal-backdrop, .overlay')
            if backdrop:
                backdrop.click()
                time.sleep(0.5)
                logger.info("배경 클릭으로 모달 닫기 시도")
        except:
            pass

    def extract_with_pagination_and_details(
        self,
        list_strategy: Dict,
        detail_strategy: Optional[Dict] = None,
        max_pages: int = 10,
        max_items_per_page: Optional[int] = None,
        detail_link_field: str = "link",
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> List[Dict]:
        """
        페이지네이션 + 상세 페이지 추출 통합

        Args:
            list_strategy: 목록 페이지 전략
            detail_strategy: 상세 페이지 전략
            max_pages: 최대 페이지 수
            max_items_per_page: 페이지당 최대 아이템 수
            detail_link_field: 상세 링크 필드명
            progress_callback: 진행률 콜백(page, current_item, total_items)

        Returns:
            전체 추출된 데이터
        """
        all_data = []
        current_page = 1

        pagination = list_strategy.get('pagination', {})
        next_button_selector = pagination.get('next_button_selector')

        logger.info(f"페이지네이션 + 상세 추출 시작 (최대 {max_pages}페이지)")

        while current_page <= max_pages:
            logger.info(f"=== 페이지 {current_page} 처리 중 ===")

            # 현재 페이지에서 목록 + 상세 추출
            page_data = self.extract_list_with_details(
                list_strategy=list_strategy,
                detail_strategy=detail_strategy,
                max_items=max_items_per_page,
                detail_link_field=detail_link_field,
                progress_callback=lambda cur, tot: progress_callback(current_page, cur, tot) if progress_callback else None
            )

            all_data.extend(page_data)

            if not page_data:
                logger.warning(f"페이지 {current_page}에서 데이터를 찾을 수 없습니다")
                break

            # 다음 페이지로 이동
            if next_button_selector and current_page < max_pages:
                try:
                    next_button = self.page.query_selector(next_button_selector)

                    if next_button and next_button.is_visible():
                        next_button.click()
                        time.sleep(self.page_delay)

                        # 페이지 로딩 대기
                        try:
                            self.page.wait_for_load_state('networkidle', timeout=5000)
                        except:
                            pass

                        current_page += 1
                    else:
                        logger.info("다음 페이지 버튼을 찾을 수 없거나 비활성화됨")
                        break

                except Exception as e:
                    logger.warning(f"페이지네이션 오류: {e}")
                    break
            else:
                break

        logger.info(f"=== 총 {len(all_data)}개 아이템 추출 완료 ({current_page}페이지) ===")
        return all_data
