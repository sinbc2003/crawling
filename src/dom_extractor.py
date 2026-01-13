"""
DOM 추출 및 단순화 모듈
페이지의 DOM 구조를 추출하고 LLM이 이해하기 쉽게 단순화
"""

from playwright.sync_api import Page
from bs4 import BeautifulSoup, Tag
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class DOMExtractor:
    """DOM 추출 및 분석 클래스"""

    def __init__(self, page: Page):
        self.page = page

    def get_full_html(self) -> str:
        """전체 HTML 가져오기"""
        return self.page.content()

    def get_simplified_dom(self, max_depth: int = 5) -> Dict:
        """
        단순화된 DOM 구조 추출
        LLM이 분석하기 쉽도록 중요한 정보만 추출

        Args:
            max_depth: DOM 트리 최대 깊이

        Returns:
            단순화된 DOM 구조 (딕셔너리)
        """
        html = self.get_full_html()
        soup = BeautifulSoup(html, 'lxml')

        # 불필요한 태그 제거
        for tag in soup(['script', 'style', 'meta', 'link', 'noscript']):
            tag.decompose()

        # DOM 트리 단순화
        simplified = self._simplify_element(soup.body if soup.body else soup, max_depth)

        return simplified

    def _simplify_element(self, element: Tag, max_depth: int, current_depth: int = 0) -> Dict:
        """
        요소를 재귀적으로 단순화

        Args:
            element: BeautifulSoup Tag 객체
            max_depth: 최대 깊이
            current_depth: 현재 깊이

        Returns:
            단순화된 요소 정보
        """
        if current_depth >= max_depth:
            return {"tag": "...", "text": "..."}

        # 기본 정보 추출
        result = {
            "tag": element.name if hasattr(element, 'name') else 'text',
            "attributes": {}
        }

        # 중요한 속성만 추출
        if hasattr(element, 'attrs'):
            important_attrs = ['id', 'class', 'href', 'src', 'alt', 'title', 'data-*', 'name', 'type', 'value']
            for attr, value in element.attrs.items():
                if attr in important_attrs or attr.startswith('data-'):
                    if isinstance(value, list):
                        result['attributes'][attr] = ' '.join(value)
                    else:
                        result['attributes'][attr] = str(value)

        # 텍스트 내용 추출 (직접 자식의 텍스트만)
        if hasattr(element, 'strings'):
            direct_text = ''.join([
                text.strip() for text in element.strings
                if text.strip() and text.parent == element
            ])
            if direct_text:
                result['text'] = direct_text[:200]  # 최대 200자

        # 자식 요소 처리
        if hasattr(element, 'children'):
            children = []
            for child in element.children:
                if isinstance(child, Tag):
                    # 중요한 태그만 포함
                    if child.name in ['div', 'section', 'article', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th',
                                      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'span', 'button', 'input']:
                        simplified_child = self._simplify_element(child, max_depth, current_depth + 1)
                        if simplified_child:
                            children.append(simplified_child)

            if children:
                result['children'] = children

        return result

    def get_element_info(self, selector: str) -> List[Dict]:
        """
        특정 selector의 요소 정보 추출

        Args:
            selector: CSS selector

        Returns:
            요소 정보 리스트
        """
        elements = self.page.query_selector_all(selector)
        results = []

        for element in elements:
            info = {
                'tag': element.evaluate('el => el.tagName.toLowerCase()'),
                'text': element.inner_text()[:200] if element.is_visible() else '',
                'attributes': element.evaluate('''el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }'''),
                'html': element.evaluate('el => el.outerHTML')[:500]
            }
            results.append(info)

        return results

    def get_page_structure_summary(self) -> str:
        """
        페이지 구조 요약 (LLM에게 제공할 컨텍스트)

        Returns:
            페이지 구조 요약 텍스트
        """
        html = self.get_full_html()
        soup = BeautifulSoup(html, 'lxml')

        # 불필요한 태그 제거
        for tag in soup(['script', 'style', 'meta', 'link', 'noscript']):
            tag.decompose()

        summary = []
        summary.append(f"Title: {soup.title.string if soup.title else 'No title'}\n")

        # 주요 구조 요소 찾기
        summary.append("Main Structure:")
        for tag_name in ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']:
            elements = soup.find_all(tag_name)
            if elements:
                summary.append(f"  - {tag_name}: {len(elements)} found")

        # 목록 구조 찾기
        summary.append("\nLists:")
        ul_count = len(soup.find_all('ul'))
        ol_count = len(soup.find_all('ol'))
        summary.append(f"  - ul: {ul_count}, ol: {ol_count}")

        # 테이블 찾기
        tables = soup.find_all('table')
        if tables:
            summary.append(f"\nTables: {len(tables)} found")

        # 링크와 이미지
        links = soup.find_all('a')
        images = soup.find_all('img')
        summary.append(f"\nLinks: {len(links)}, Images: {len(images)}")

        # 반복되는 구조 패턴 찾기 (게시판 등)
        summary.append("\nRepeating Patterns:")
        for class_name in self._find_repeating_classes(soup):
            summary.append(f"  - class='{class_name}'")

        return '\n'.join(summary)

    def _find_repeating_classes(self, soup: BeautifulSoup, min_count: int = 3) -> List[str]:
        """
        반복되는 클래스 이름 찾기 (게시판 아이템 등)

        Args:
            soup: BeautifulSoup 객체
            min_count: 최소 반복 횟수

        Returns:
            반복되는 클래스 이름 리스트
        """
        class_counts = {}

        for element in soup.find_all(class_=True):
            classes = element.get('class', [])
            for class_name in classes:
                if class_name not in class_counts:
                    class_counts[class_name] = 0
                class_counts[class_name] += 1

        # 반복되는 클래스만 필터링
        repeating = [
            class_name for class_name, count in class_counts.items()
            if count >= min_count
        ]

        # 상위 5개만 반환
        return sorted(repeating, key=lambda x: class_counts[x], reverse=True)[:5]

    def extract_data_by_selector(self, selector: str, attributes: List[str] = None) -> List[Dict]:
        """
        Selector로 데이터 추출

        Args:
            selector: CSS selector
            attributes: 추출할 속성 리스트 (없으면 텍스트만)

        Returns:
            추출된 데이터 리스트
        """
        elements = self.page.query_selector_all(selector)
        results = []

        for element in elements:
            data = {}

            # 텍스트 추출
            if element.is_visible():
                data['text'] = element.inner_text().strip()

            # 속성 추출
            if attributes:
                for attr in attributes:
                    value = element.get_attribute(attr)
                    if value:
                        data[attr] = value

            if data:
                results.append(data)

        return results
