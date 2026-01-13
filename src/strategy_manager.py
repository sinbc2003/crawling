"""
크롤링 전략 저장 및 관리 모듈
사이트별 전략을 저장하여 재사용 가능
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class StrategyManager:
    """크롤링 전략 저장/불러오기 관리 클래스"""

    def __init__(self, storage_dir: str = "strategies"):
        """
        Args:
            storage_dir: 전략 파일들을 저장할 디렉토리
        """
        self.storage_dir = storage_dir
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """저장 디렉토리가 없으면 생성"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            logger.info(f"전략 저장 디렉토리 생성: {self.storage_dir}")

    def save_strategy(
        self,
        url: str,
        strategy: Dict,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        크롤링 전략 저장

        Args:
            url: 대상 URL
            strategy: 크롤링 전략 딕셔너리
            name: 전략 이름 (선택, 없으면 도메인 사용)
            description: 전략 설명 (선택)
            tags: 태그 리스트 (선택)

        Returns:
            저장된 파일 경로
        """
        # URL에서 도메인 추출
        domain = self._extract_domain(url)

        # 전략 이름 결정
        if not name:
            name = domain

        # 파일명 생성 (도메인_타임스탬프.json)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{domain}_{timestamp}.json"
        filepath = os.path.join(self.storage_dir, filename)

        # 저장할 데이터 구성
        strategy_data = {
            "name": name,
            "url": url,
            "domain": domain,
            "description": description or f"{domain} 크롤링 전략",
            "tags": tags or [],
            "notes": notes or "",
            "created_at": datetime.now().isoformat(),
            "strategy": strategy
        }

        # JSON 파일로 저장
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(strategy_data, f, ensure_ascii=False, indent=2)

            logger.info(f"전략 저장 완료: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"전략 저장 실패: {e}")
            raise

    def load_strategy(self, filepath: str) -> Dict:
        """
        저장된 전략 불러오기

        Args:
            filepath: 전략 파일 경로

        Returns:
            전략 데이터
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                strategy_data = json.load(f)

            logger.info(f"전략 불러오기 완료: {filepath}")
            return strategy_data

        except Exception as e:
            logger.error(f"전략 불러오기 실패: {e}")
            raise

    def list_strategies(
        self,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        저장된 전략 목록 조회

        Args:
            domain: 특정 도메인으로 필터링 (선택)
            tags: 특정 태그로 필터링 (선택)

        Returns:
            전략 메타데이터 리스트 (strategy는 제외, 경로만)
        """
        strategies = []

        try:
            # 모든 JSON 파일 읽기
            for filename in os.listdir(self.storage_dir):
                if not filename.endswith('.json'):
                    continue

                filepath = os.path.join(self.storage_dir, filename)

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        strategy_data = json.load(f)

                    # 필터링
                    if domain and strategy_data.get('domain') != domain:
                        continue

                    if tags:
                        strategy_tags = strategy_data.get('tags', [])
                        if not any(tag in strategy_tags for tag in tags):
                            continue

                    # 메타데이터만 추가 (strategy 내용은 제외)
                    metadata = {
                        "filepath": filepath,
                        "name": strategy_data.get('name'),
                        "url": strategy_data.get('url'),
                        "domain": strategy_data.get('domain'),
                        "description": strategy_data.get('description'),
                        "tags": strategy_data.get('tags', []),
                        "notes": strategy_data.get('notes', ''),
                        "created_at": strategy_data.get('created_at')
                    }
                    strategies.append(metadata)

                except Exception as e:
                    logger.warning(f"파일 읽기 실패 ({filename}): {e}")
                    continue

            # 생성일 기준 내림차순 정렬
            strategies.sort(key=lambda x: x['created_at'], reverse=True)

            logger.info(f"{len(strategies)}개 전략 발견")
            return strategies

        except Exception as e:
            logger.error(f"전략 목록 조회 실패: {e}")
            return []

    def find_strategy_by_url(self, url: str) -> Optional[Dict]:
        """
        URL로 가장 최근 전략 찾기

        Args:
            url: 대상 URL

        Returns:
            전략 데이터 (없으면 None)
        """
        domain = self._extract_domain(url)
        strategies = self.list_strategies(domain=domain)

        if strategies:
            # 가장 최근 전략 불러오기
            latest_strategy = strategies[0]
            return self.load_strategy(latest_strategy['filepath'])

        return None

    def delete_strategy(self, filepath: str) -> bool:
        """
        전략 삭제

        Args:
            filepath: 삭제할 전략 파일 경로

        Returns:
            성공 여부
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"전략 삭제 완료: {filepath}")
                return True
            else:
                logger.warning(f"파일이 존재하지 않습니다: {filepath}")
                return False

        except Exception as e:
            logger.error(f"전략 삭제 실패: {e}")
            return False

    def update_strategy(
        self,
        filepath: str,
        strategy: Optional[Dict] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        기존 전략 업데이트

        Args:
            filepath: 업데이트할 전략 파일 경로
            strategy: 새로운 전략 (선택)
            name: 새로운 이름 (선택)
            description: 새로운 설명 (선택)
            tags: 새로운 태그 (선택)

        Returns:
            성공 여부
        """
        try:
            # 기존 전략 읽기
            strategy_data = self.load_strategy(filepath)

            # 업데이트
            if strategy is not None:
                strategy_data['strategy'] = strategy

            if name is not None:
                strategy_data['name'] = name

            if description is not None:
                strategy_data['description'] = description

            if tags is not None:
                strategy_data['tags'] = tags

            if notes is not None:
                strategy_data['notes'] = notes

            strategy_data['updated_at'] = datetime.now().isoformat()

            # 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(strategy_data, f, ensure_ascii=False, indent=2)

            logger.info(f"전략 업데이트 완료: {filepath}")
            return True

        except Exception as e:
            logger.error(f"전략 업데이트 실패: {e}")
            return False

    def export_strategy(self, filepath: str, export_path: str) -> bool:
        """
        전략을 다른 위치로 내보내기

        Args:
            filepath: 소스 전략 파일
            export_path: 내보낼 경로

        Returns:
            성공 여부
        """
        try:
            strategy_data = self.load_strategy(filepath)

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(strategy_data, f, ensure_ascii=False, indent=2)

            logger.info(f"전략 내보내기 완료: {export_path}")
            return True

        except Exception as e:
            logger.error(f"전략 내보내기 실패: {e}")
            return False

    def import_strategy(self, import_path: str) -> str:
        """
        외부 전략 파일 가져오기

        Args:
            import_path: 가져올 전략 파일 경로

        Returns:
            저장된 파일 경로
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                strategy_data = json.load(f)

            # 기존 save_strategy 사용
            url = strategy_data.get('url', '')
            name = strategy_data.get('name')
            description = strategy_data.get('description')
            tags = strategy_data.get('tags', [])
            strategy = strategy_data.get('strategy', {})

            filepath = self.save_strategy(
                url=url,
                strategy=strategy,
                name=name,
                description=description,
                tags=tags
            )

            logger.info(f"전략 가져오기 완료: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"전략 가져오기 실패: {e}")
            raise

    def search_strategies(self, keyword: str) -> List[Dict]:
        """
        키워드로 전략 검색 (이름, 설명, 태그, 도메인에서 검색)

        Args:
            keyword: 검색 키워드

        Returns:
            매칭되는 전략 메타데이터 리스트
        """
        all_strategies = self.list_strategies()
        keyword_lower = keyword.lower()

        results = []
        for strategy in all_strategies:
            # 이름, 설명, 도메인, 태그에서 키워드 검색
            searchable_text = " ".join([
                strategy.get('name', ''),
                strategy.get('description', ''),
                strategy.get('domain', ''),
                " ".join(strategy.get('tags', []))
            ]).lower()

            if keyword_lower in searchable_text:
                results.append(strategy)

        logger.info(f"'{keyword}' 검색 결과: {len(results)}개")
        return results

    def _extract_domain(self, url: str) -> str:
        """
        URL에서 도메인 추출

        Args:
            url: URL

        Returns:
            도메인 (예: example.com)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            # www. 제거
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain or "unknown"

        except Exception as e:
            logger.warning(f"도메인 추출 실패: {e}")
            return "unknown"

    def get_strategy_stats(self) -> Dict:
        """
        전략 저장소 통계 조회

        Returns:
            통계 딕셔너리 (총 개수, 도메인별 개수 등)
        """
        all_strategies = self.list_strategies()

        # 도메인별 개수
        domain_counts = {}
        for strategy in all_strategies:
            domain = strategy.get('domain', 'unknown')
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # 태그별 개수
        tag_counts = {}
        for strategy in all_strategies:
            for tag in strategy.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        stats = {
            "total_strategies": len(all_strategies),
            "domain_counts": domain_counts,
            "tag_counts": tag_counts,
            "storage_dir": self.storage_dir
        }

        return stats
