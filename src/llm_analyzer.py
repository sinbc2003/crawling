"""
LLM 분석 모듈
OpenAI API를 사용하여 DOM 구조를 분석하고 크롤링 전략 생성
"""

from openai import OpenAI
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """LLM 기반 DOM 분석 및 크롤링 전략 생성 클래스"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def list_available_models(self) -> List[str]:
        """
        사용 가능한 모델 목록 반환 (최신 모델만)

        Returns:
            모델 ID 리스트
        """
        # 최신 GPT 모델 목록 (수동으로 관리)
        recommended_models = [
            "gpt-4-turbo-preview",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-4-32k",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-1106",
            "gpt-4-1106-preview",
            "gpt-4-0125-preview",
        ]

        try:
            # API에서 사용 가능한 모델 목록 가져오기
            models = self.client.models.list()
            available_model_ids = [model.id for model in models.data]

            # 권장 모델 중 사용 가능한 것만 필터링
            available_recommended = [
                model for model in recommended_models
                if model in available_model_ids
            ]

            # 추가로 gpt-4로 시작하는 최신 모델 찾기
            additional_gpt4 = [
                model_id for model_id in available_model_ids
                if model_id.startswith('gpt-4') and model_id not in available_recommended
                and not any(old in model_id for old in ['vision', 'dalle', 'whisper'])
            ]

            # 추가로 gpt-3.5로 시작하는 최신 모델 찾기
            additional_gpt35 = [
                model_id for model_id in available_model_ids
                if model_id.startswith('gpt-3.5') and model_id not in available_recommended
            ]

            # 합치기 (gpt-4 우선, 최신순)
            all_models = available_recommended + sorted(additional_gpt4, reverse=True) + sorted(additional_gpt35, reverse=True)

            # 중복 제거
            seen = set()
            result = []
            for model in all_models:
                if model not in seen:
                    seen.add(model)
                    result.append(model)

            return result if result else recommended_models

        except Exception as e:
            logger.error(f"모델 목록 조회 실패: {e}")
            # 기본 모델 목록 반환
            return recommended_models[:5]

    def analyze_page_structure(self, page_summary: str, user_request: str) -> Dict:
        """
        페이지 구조 분석 및 크롤링 전략 생성

        Args:
            page_summary: 페이지 구조 요약
            user_request: 사용자 요청 (자연어)

        Returns:
            크롤링 전략 (selector, 필드 등)
        """
        system_prompt = """당신은 웹 크롤링 전문가입니다. 사용자의 요청과 페이지 구조를 분석하여 최적의 CSS selector를 생성하세요.

응답은 반드시 다음 JSON 형식으로 제공하세요:
{
  "container_selector": "반복되는 아이템을 포함하는 컨테이너 selector (예: .post-list > .post-item)",
  "fields": [
    {
      "name": "필드명 (예: title, author, date)",
      "selector": "컨테이너 내부의 상대 selector (예: .title, h2.post-title)",
      "attribute": "추출할 속성 (텍스트면 null, href/src 등)",
      "description": "필드 설명"
    }
  ],
  "pagination": {
    "next_button_selector": "다음 페이지 버튼 selector (없으면 null)",
    "page_links_selector": "페이지 링크들 selector (없으면 null)"
  },
  "notes": "추가 참고사항"
}

중요:
1. container_selector는 반복되는 아이템(게시글, 상품 등)을 감싸는 요소를 가리켜야 합니다
2. fields의 selector는 container 내부에서의 상대 경로입니다
3. attribute가 null이면 텍스트를 추출하고, href/src 등이면 해당 속성을 추출합니다
4. 가능한 한 명확하고 안정적인 selector를 사용하세요 (id > class > tag)
"""

        user_prompt = f"""페이지 구조:
{page_summary}

사용자 요청:
{user_request}

위 정보를 바탕으로 최적의 크롤링 전략을 JSON 형식으로 생성해주세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            strategy = json.loads(response.choices[0].message.content)
            logger.info(f"크롤링 전략 생성 완료: {strategy}")
            return strategy

        except Exception as e:
            logger.error(f"LLM 분석 실패: {e}")
            raise

    def refine_selectors(self, html_sample: str, current_strategy: Dict, user_feedback: str) -> Dict:
        """
        사용자 피드백을 바탕으로 selector 개선

        Args:
            html_sample: 샘플 HTML
            current_strategy: 현재 크롤링 전략
            user_feedback: 사용자 피드백

        Returns:
            개선된 크롤링 전략
        """
        system_prompt = """현재 크롤링 전략과 사용자 피드백을 바탕으로 selector를 개선하세요.
응답은 동일한 JSON 형식으로 제공하세요."""

        user_prompt = f"""HTML 샘플:
{html_sample[:3000]}

현재 전략:
{json.dumps(current_strategy, ensure_ascii=False, indent=2)}

사용자 피드백:
{user_feedback}

위 정보를 바탕으로 개선된 크롤링 전략을 생성해주세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            improved_strategy = json.loads(response.choices[0].message.content)
            logger.info(f"전략 개선 완료: {improved_strategy}")
            return improved_strategy

        except Exception as e:
            logger.error(f"전략 개선 실패: {e}")
            raise

    def generate_selectors_from_html(self, html: str, user_request: str) -> Dict:
        """
        HTML을 직접 분석하여 selector 생성 (더 정확한 방식)

        Args:
            html: 전체 HTML 또는 일부
            user_request: 사용자 요청

        Returns:
            크롤링 전략
        """
        # HTML이 너무 길면 자르기
        if len(html) > 10000:
            html = html[:10000] + "\n... (truncated)"

        system_prompt = """당신은 웹 크롤링 전문가입니다. HTML 구조를 분석하여 최적의 CSS selector를 생성하세요.

응답은 반드시 다음 JSON 형식으로 제공하세요:
{
  "container_selector": "반복되는 아이템 selector",
  "fields": [
    {
      "name": "필드명",
      "selector": "상대 selector",
      "attribute": "추출할 속성 또는 null",
      "description": "설명"
    }
  ],
  "pagination": {
    "next_button_selector": "다음 버튼 selector 또는 null",
    "page_links_selector": "페이지 링크 selector 또는 null"
  },
  "notes": "참고사항"
}
"""

        user_prompt = f"""HTML:
{html}

사용자 요청:
{user_request}

위 HTML에서 사용자가 요청한 데이터를 추출할 수 있는 최적의 selector를 생성해주세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            strategy = json.loads(response.choices[0].message.content)
            logger.info(f"HTML 기반 전략 생성 완료")
            return strategy

        except Exception as e:
            logger.error(f"HTML 분석 실패: {e}")
            raise

    def validate_extraction(self, sample_data: List[Dict], user_request: str) -> Dict:
        """
        추출된 데이터가 사용자 요청을 충족하는지 검증

        Args:
            sample_data: 샘플 데이터 (처음 몇 개 아이템)
            user_request: 원래 사용자 요청

        Returns:
            검증 결과 및 개선 제안
        """
        system_prompt = """추출된 샘플 데이터를 분석하여 사용자 요청을 충족하는지 평가하세요.

응답 형식:
{
  "is_valid": true/false,
  "quality_score": 0-100,
  "issues": ["문제점 1", "문제점 2"],
  "suggestions": ["개선 제안 1", "개선 제안 2"]
}
"""

        user_prompt = f"""사용자 요청:
{user_request}

추출된 샘플 데이터:
{json.dumps(sample_data[:3], ensure_ascii=False, indent=2)}

이 데이터가 사용자 요청을 충족하는지 평가해주세요."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            validation = json.loads(response.choices[0].message.content)
            return validation

        except Exception as e:
            logger.error(f"데이터 검증 실패: {e}")
            return {
                "is_valid": True,
                "quality_score": 50,
                "issues": [],
                "suggestions": []
            }
