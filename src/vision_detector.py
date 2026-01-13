"""
GPT-4 Vision 기반 요소 감지 모듈
스크린샷을 분석하여 클릭해야 할 요소의 위치와 selector 자동 생성
"""

from openai import OpenAI
from playwright.sync_api import Page
from typing import Dict, List, Optional, Tuple
import base64
import json
import logging
import io

logger = logging.getLogger(__name__)


class VisionDetector:
    """GPT-4 Vision을 사용한 웹 요소 감지 클래스"""

    def __init__(self, api_key: str, model: str = "gpt-4-vision-preview"):
        """
        Args:
            api_key: OpenAI API 키
            model: Vision 모델 (gpt-4-vision-preview, gpt-4-turbo 등)
        """
        self.client = OpenAI(api_key=api_key)
        # gpt-4-turbo가 vision도 지원하면서 더 빠름
        self.model = "gpt-4-turbo" if "turbo" in model else model

    def analyze_page_screenshot(
        self,
        page: Page,
        user_request: str,
        full_page: bool = False
    ) -> Dict:
        """
        페이지 스크린샷을 분석하여 크롤링 전략 생성

        Args:
            page: Playwright Page 객체
            user_request: 사용자 요청 (예: "모든 게시글 클릭", "다음 페이지 버튼 찾기")
            full_page: 전체 페이지 스크린샷 여부

        Returns:
            분석 결과 및 selector 정보
        """
        logger.info("페이지 스크린샷 촬영 중...")

        # 스크린샷 촬영
        screenshot_bytes = page.screenshot(full_page=full_page)

        # base64 인코딩
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        # Vision API로 분석
        logger.info("GPT-4 Vision으로 분석 중...")
        result = self._analyze_screenshot_with_vision(
            screenshot_base64,
            user_request
        )

        return result

    def _analyze_screenshot_with_vision(
        self,
        image_base64: str,
        user_request: str
    ) -> Dict:
        """
        GPT-4 Vision으로 스크린샷 분석

        Args:
            image_base64: base64 인코딩된 이미지
            user_request: 사용자 요청

        Returns:
            분석 결과 (selector, 위치, 설명 등)
        """
        system_prompt = """당신은 웹 크롤링 전문가입니다.
웹 페이지 스크린샷을 보고 사용자가 원하는 요소들을 식별하세요.

응답은 반드시 다음 JSON 형식으로 제공하세요:
{
  "elements_found": [
    {
      "type": "요소 타입 (button, link, input, container 등)",
      "description": "요소 설명",
      "visual_location": "화면상 위치 (예: 상단 좌측, 중앙, 하단 우측)",
      "suggested_selector": "추천 CSS selector",
      "action": "수행할 작업 (click, extract, input 등)",
      "confidence": "신뢰도 (0-100)"
    }
  ],
  "analysis": "전체 페이지 분석 결과",
  "recommendations": "크롤링 전략 추천사항"
}

중요:
1. 반복되는 패턴(게시글 목록 등)을 식별하세요
2. 클릭 가능한 요소(버튼, 링크)를 명확히 표시하세요
3. 페이지네이션 요소(다음, 이전 버튼)를 찾으세요
4. 가능한 한 안정적인 selector를 제안하세요
"""

        user_prompt = f"""이 웹 페이지 스크린샷을 분석해주세요.

사용자 요청: {user_request}

위 요청을 달성하기 위해 필요한 요소들을 찾아 JSON 형식으로 정리해주세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )

            # JSON 파싱
            content = response.choices[0].message.content

            # JSON 추출 (마크다운 코드 블록 제거)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            logger.info(f"Vision 분석 완료: {len(result.get('elements_found', []))}개 요소 발견")

            return result

        except Exception as e:
            logger.error(f"Vision 분석 실패: {e}")
            return {
                "elements_found": [],
                "analysis": f"분석 실패: {str(e)}",
                "recommendations": "직접 selector를 입력해주세요."
            }

    def find_clickable_elements(
        self,
        page: Page,
        target_description: str = "게시글 링크"
    ) -> List[Dict]:
        """
        클릭 가능한 요소들을 자동으로 찾기

        Args:
            page: Playwright Page 객체
            target_description: 찾고자 하는 요소 설명

        Returns:
            발견된 요소 리스트
        """
        screenshot_bytes = page.screenshot()
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        user_request = f"페이지에서 '{target_description}'에 해당하는 모든 클릭 가능한 요소를 찾아주세요."

        result = self._analyze_screenshot_with_vision(screenshot_base64, user_request)

        # 클릭 가능한 요소만 필터링
        clickable_elements = [
            elem for elem in result.get('elements_found', [])
            if elem.get('action') in ['click', 'navigate']
        ]

        return clickable_elements

    def identify_pagination_controls(self, page: Page) -> Dict:
        """
        페이지네이션 컨트롤(다음/이전 버튼) 자동 감지

        Args:
            page: Playwright Page 객체

        Returns:
            페이지네이션 정보
        """
        screenshot_bytes = page.screenshot()
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        user_request = "페이지네이션 컨트롤(다음 페이지, 이전 페이지, 페이지 번호 버튼)을 찾아주세요."

        result = self._analyze_screenshot_with_vision(screenshot_base64, user_request)

        # 페이지네이션 관련 요소 추출
        pagination_info = {
            "next_button": None,
            "prev_button": None,
            "page_numbers": []
        }

        for elem in result.get('elements_found', []):
            description = elem.get('description', '').lower()

            if 'next' in description or '다음' in description:
                pagination_info['next_button'] = elem
            elif 'prev' in description or '이전' in description:
                pagination_info['prev_button'] = elem
            elif 'page' in description or '페이지' in description:
                pagination_info['page_numbers'].append(elem)

        return pagination_info

    def compare_screenshots_for_changes(
        self,
        page: Page,
        action_description: str
    ) -> Tuple[str, str, Dict]:
        """
        액션 전후 스크린샷을 비교하여 변경사항 감지

        Args:
            page: Playwright Page 객체
            action_description: 수행할 액션 설명

        Returns:
            (before_base64, after_base64, changes_dict)
        """
        # 액션 전 스크린샷
        before_screenshot = page.screenshot()
        before_base64 = base64.b64encode(before_screenshot).decode('utf-8')

        logger.info(f"액션 수행: {action_description}")
        # 여기서 실제 액션을 수행해야 함 (호출자가 수행)

        # 액션 후 스크린샷
        after_screenshot = page.screenshot()
        after_base64 = base64.b64encode(after_screenshot).decode('utf-8')

        # 두 스크린샷 비교 분석
        changes = self._compare_screenshots(
            before_base64,
            after_base64,
            action_description
        )

        return before_base64, after_base64, changes

    def _compare_screenshots(
        self,
        before_base64: str,
        after_base64: str,
        action_description: str
    ) -> Dict:
        """
        두 스크린샷 비교 분석

        Args:
            before_base64: 이전 스크린샷 (base64)
            after_base64: 이후 스크린샷 (base64)
            action_description: 수행된 액션 설명

        Returns:
            변경사항 분석 결과
        """
        system_prompt = """두 개의 스크린샷(이전, 이후)을 비교하여 변경사항을 분석하세요.

응답 형식:
{
  "has_changes": true/false,
  "change_type": "navigation | modal | content_update | no_change",
  "description": "변경사항 상세 설명",
  "new_elements": ["새로 나타난 요소들"],
  "removed_elements": ["사라진 요소들"],
  "modal_detected": true/false,
  "url_changed": "추정 (확인 필요)"
}
"""

        user_prompt = f"""액션: {action_description}

위 액션을 수행하기 전후의 스크린샷입니다. 변경사항을 분석해주세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "이전 스크린샷:"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{before_base64}",
                                    "detail": "high"
                                }
                            },
                            {"type": "text", "text": "이후 스크린샷:"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{after_base64}",
                                    "detail": "high"
                                }
                            },
                            {"type": "text", "text": user_prompt}
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )

            content = response.choices[0].message.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            return result

        except Exception as e:
            logger.error(f"스크린샷 비교 실패: {e}")
            return {
                "has_changes": False,
                "change_type": "unknown",
                "description": f"비교 실패: {str(e)}"
            }

    def generate_extraction_strategy_from_screenshot(
        self,
        page: Page,
        user_request: str
    ) -> Dict:
        """
        스크린샷 기반으로 완전한 크롤링 전략 생성
        (기존 HTML 분석 방식보다 더 직관적)

        Args:
            page: Playwright Page 객체
            user_request: 사용자 요청

        Returns:
            크롤링 전략 (LLMAnalyzer와 동일한 형식)
        """
        screenshot_bytes = page.screenshot(full_page=True)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        system_prompt = """웹 페이지 스크린샷을 보고 크롤링 전략을 생성하세요.

응답은 반드시 다음 JSON 형식으로 제공하세요:
{
  "container_selector": "반복되는 아이템 컨테이너 selector",
  "fields": [
    {
      "name": "필드명",
      "selector": "상대 selector",
      "attribute": "속성 또는 null",
      "description": "설명"
    }
  ],
  "pagination": {
    "next_button_selector": "다음 버튼 selector 또는 null",
    "page_links_selector": "페이지 링크 selector 또는 null"
  },
  "detail_page": {
    "has_detail": true/false,
    "link_field": "링크가 있는 필드명",
    "detail_strategy": "상세 페이지 전략 (선택)"
  },
  "notes": "추가 참고사항"
}

중요:
1. 스크린샷에서 반복되는 패턴을 찾아 container_selector를 제안하세요
2. 각 필드의 위치와 내용을 보고 적절한 selector를 생성하세요
3. 클릭해서 상세 페이지로 이동하는 링크가 있는지 확인하세요
"""

        user_prompt = f"""사용자 요청: {user_request}

이 페이지에서 위 요청을 달성하기 위한 완전한 크롤링 전략을 생성해주세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )

            content = response.choices[0].message.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            strategy = json.loads(content)
            logger.info("스크린샷 기반 전략 생성 완료")

            return strategy

        except Exception as e:
            logger.error(f"전략 생성 실패: {e}")
            raise

    def verify_selector_with_screenshot(
        self,
        page: Page,
        selector: str,
        expected_description: str
    ) -> Dict:
        """
        생성된 selector가 올바른지 스크린샷으로 확인

        Args:
            page: Playwright Page 객체
            selector: 확인할 CSS selector
            expected_description: 기대하는 요소 설명

        Returns:
            검증 결과
        """
        try:
            # selector로 요소 찾기
            elements = page.query_selector_all(selector)

            if not elements:
                return {
                    "is_valid": False,
                    "message": "selector로 요소를 찾을 수 없습니다"
                }

            # 첫 번째 요소 하이라이트
            first_element = elements[0]

            # 요소를 하이라이트하고 스크린샷
            page.evaluate("""
                (selector) => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        el.style.outline = '3px solid red';
                    });
                }
            """, selector)

            screenshot_bytes = page.screenshot()
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            # 하이라이트 제거
            page.evaluate("""
                (selector) => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        el.style.outline = '';
                    });
                }
            """, selector)

            # Vision으로 확인
            result = self._verify_highlighted_elements(
                screenshot_base64,
                expected_description,
                len(elements)
            )

            return result

        except Exception as e:
            logger.error(f"Selector 검증 실패: {e}")
            return {
                "is_valid": False,
                "message": f"검증 오류: {str(e)}"
            }

    def _verify_highlighted_elements(
        self,
        screenshot_base64: str,
        expected_description: str,
        element_count: int
    ) -> Dict:
        """
        하이라이트된 요소가 올바른지 Vision으로 검증
        """
        system_prompt = """스크린샷에 빨간색 테두리로 하이라이트된 요소들을 확인하세요.

응답 형식:
{
  "is_valid": true/false,
  "confidence": 0-100,
  "message": "검증 결과 설명",
  "element_count_matches": true/false,
  "suggestions": "개선 제안 (있다면)"
}
"""

        user_prompt = f"""빨간색으로 하이라이트된 요소들이 '{expected_description}'에 해당하는지 확인해주세요.
예상 요소 개수: {element_count}개

올바른 요소가 선택되었나요?"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )

            content = response.choices[0].message.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            return result

        except Exception as e:
            logger.error(f"하이라이트 검증 실패: {e}")
            return {
                "is_valid": False,
                "confidence": 0,
                "message": f"검증 실패: {str(e)}"
            }
