"""
데이터 추출 모듈
LLM이 생성한 전략을 바탕으로 실제 데이터 추출
"""

from playwright.sync_api import Page
from typing import Dict, List, Optional
import time
import logging

logger = logging.getLogger(__name__)


class DataExtractor:
    """데이터 추출 및 페이지네이션 처리 클래스"""

    def __init__(self, page: Page, item_delay: float = 0.0):
        """
        Args:
            page: Playwright Page 객체
            item_delay: 각 아이템 추출 사이의 대기 시간 (초)
        """
        self.page = page
        self.item_delay = item_delay

    def extract_data(self, strategy: Dict, max_items: Optional[int] = None) -> List[Dict]:
        """
        크롤링 전략에 따라 데이터 추출

        Args:
            strategy: LLM이 생성한 크롤링 전략
            max_items: 최대 아이템 수 (None이면 제한 없음)

        Returns:
            추출된 데이터 리스트
        """
        all_data = []
        container_selector = strategy.get('container_selector')
        fields = strategy.get('fields', [])

        if not container_selector:
            logger.error("container_selector가 없습니다")
            return []

        logger.info(f"데이터 추출 시작: {container_selector}")

        # 컨테이너 요소들 찾기
        try:
            # 요소가 로드될 때까지 대기
            self.page.wait_for_selector(container_selector, timeout=10000)
        except Exception as e:
            logger.warning(f"컨테이너 대기 중 오류: {e}")

        containers = self.page.query_selector_all(container_selector)
        logger.info(f"컨테이너 {len(containers)}개 발견")

        for idx, container in enumerate(containers):
            if max_items and idx >= max_items:
                break

            item_data = {}

            # 각 필드 추출
            for field in fields:
                field_name = field.get('name')
                field_selector = field.get('selector')
                field_attribute = field.get('attribute')

                try:
                    # 컨테이너 내부에서 요소 찾기
                    element = container.query_selector(field_selector)

                    if element:
                        if field_attribute and field_attribute != 'null':
                            # 속성 추출 (href, src 등)
                            value = element.get_attribute(field_attribute)
                        else:
                            # 텍스트 추출
                            value = element.inner_text().strip()

                        if value:
                            item_data[field_name] = value
                    else:
                        item_data[field_name] = None

                except Exception as e:
                    logger.warning(f"필드 '{field_name}' 추출 실패: {e}")
                    item_data[field_name] = None

            if item_data:
                all_data.append(item_data)

                # 속도 조절: 각 아이템 추출 후 대기
                if self.item_delay > 0 and idx < len(containers) - 1:
                    time.sleep(self.item_delay)

        logger.info(f"총 {len(all_data)}개 아이템 추출 완료")
        return all_data

    def extract_with_pagination(
        self,
        strategy: Dict,
        max_pages: int = 10,
        delay: float = 1.0
    ) -> List[Dict]:
        """
        페이지네이션을 고려하여 데이터 추출

        Args:
            strategy: 크롤링 전략
            max_pages: 최대 페이지 수
            delay: 페이지 간 대기 시간 (초)

        Returns:
            전체 추출된 데이터
        """
        all_data = []
        current_page = 1

        pagination = strategy.get('pagination', {})
        next_button_selector = pagination.get('next_button_selector')

        logger.info(f"페이지네이션 추출 시작 (최대 {max_pages}페이지)")

        while current_page <= max_pages:
            logger.info(f"페이지 {current_page} 추출 중...")

            # 현재 페이지 데이터 추출
            page_data = self.extract_data(strategy)
            all_data.extend(page_data)

            if not page_data:
                logger.warning(f"페이지 {current_page}에서 데이터를 찾을 수 없습니다")
                break

            # 다음 페이지로 이동
            if next_button_selector and current_page < max_pages:
                try:
                    next_button = self.page.query_selector(next_button_selector)

                    if next_button and next_button.is_visible():
                        # 버튼 클릭 전 URL 저장
                        old_url = self.page.url

                        # 클릭
                        next_button.click()

                        # 페이지 로딩 대기 (URL 변경 또는 네트워크 idle)
                        try:
                            self.page.wait_for_load_state('networkidle', timeout=5000)
                        except:
                            pass

                        # URL이 변경되었는지 확인
                        new_url = self.page.url
                        if old_url == new_url:
                            # URL이 변경되지 않았으면 잠시 대기
                            time.sleep(delay)

                        time.sleep(delay)  # 추가 대기
                        current_page += 1
                    else:
                        logger.info("다음 페이지 버튼을 찾을 수 없거나 비활성화됨")
                        break

                except Exception as e:
                    logger.warning(f"페이지네이션 오류: {e}")
                    break
            else:
                break

        logger.info(f"총 {len(all_data)}개 아이템 추출 완료 ({current_page}페이지)")
        return all_data

    def extract_single_page_data(
        self,
        container_selector: str,
        field_selectors: Dict[str, str]
    ) -> List[Dict]:
        """
        단순한 단일 페이지 데이터 추출 (전략 없이)

        Args:
            container_selector: 컨테이너 selector
            field_selectors: {필드명: selector} 딕셔너리

        Returns:
            추출된 데이터 리스트
        """
        results = []

        try:
            self.page.wait_for_selector(container_selector, timeout=10000)
            containers = self.page.query_selector_all(container_selector)

            for container in containers:
                item = {}
                for field_name, selector in field_selectors.items():
                    try:
                        element = container.query_selector(selector)
                        if element:
                            item[field_name] = element.inner_text().strip()
                    except:
                        item[field_name] = None

                if item:
                    results.append(item)

        except Exception as e:
            logger.error(f"데이터 추출 실패: {e}")

        return results

    def wait_and_extract(
        self,
        strategy: Dict,
        wait_selector: Optional[str] = None,
        wait_time: float = 2.0
    ) -> List[Dict]:
        """
        특정 요소가 로드될 때까지 대기 후 추출

        Args:
            strategy: 크롤링 전략
            wait_selector: 대기할 selector (None이면 container_selector 사용)
            wait_time: 추가 대기 시간 (초)

        Returns:
            추출된 데이터
        """
        selector = wait_selector or strategy.get('container_selector')

        if selector:
            try:
                self.page.wait_for_selector(selector, timeout=15000)
                time.sleep(wait_time)
            except Exception as e:
                logger.warning(f"요소 대기 중 오류: {e}")

        return self.extract_data(strategy)

    def extract_table_data(self, table_selector: str = 'table') -> List[Dict]:
        """
        테이블 데이터 추출

        Args:
            table_selector: 테이블 selector

        Returns:
            테이블 데이터 (각 행이 딕셔너리)
        """
        results = []

        try:
            tables = self.page.query_selector_all(table_selector)

            for table in tables:
                # 헤더 추출
                headers = []
                header_cells = table.query_selector_all('thead th, thead td')

                if not header_cells:
                    # thead가 없으면 첫 번째 tr 사용
                    header_cells = table.query_selector_all('tr:first-child th, tr:first-child td')

                for cell in header_cells:
                    headers.append(cell.inner_text().strip())

                # 데이터 행 추출
                rows = table.query_selector_all('tbody tr')

                if not rows:
                    # tbody가 없으면 모든 tr 사용 (헤더 제외)
                    all_rows = table.query_selector_all('tr')
                    rows = all_rows[1:] if len(all_rows) > 1 else []

                for row in rows:
                    cells = row.query_selector_all('td, th')
                    row_data = {}

                    for idx, cell in enumerate(cells):
                        header = headers[idx] if idx < len(headers) else f'column_{idx}'
                        row_data[header] = cell.inner_text().strip()

                    if row_data:
                        results.append(row_data)

        except Exception as e:
            logger.error(f"테이블 데이터 추출 실패: {e}")

        return results
