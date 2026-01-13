"""
데이터 내보내기 모듈
추출된 데이터를 다양한 형식으로 저장
"""

import json
import csv
import pandas as pd
from typing import List, Dict
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataExporter:
    """데이터 내보내기 클래스"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export_to_json(self, data: List[Dict], filename: str = None) -> str:
        """
        JSON 형식으로 내보내기

        Args:
            data: 내보낼 데이터
            filename: 파일명 (없으면 자동 생성)

        Returns:
            저장된 파일 경로
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crawled_data_{timestamp}.json"

        filepath = self.output_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"JSON 내보내기 완료: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"JSON 내보내기 실패: {e}")
            raise

    def export_to_csv(self, data: List[Dict], filename: str = None) -> str:
        """
        CSV 형식으로 내보내기

        Args:
            data: 내보낼 데이터
            filename: 파일명 (없으면 자동 생성)

        Returns:
            저장된 파일 경로
        """
        if not data:
            raise ValueError("내보낼 데이터가 없습니다")

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crawled_data_{timestamp}.csv"

        filepath = self.output_dir / filename

        try:
            # 모든 필드명 수집
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            fieldnames = sorted(fieldnames)

            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"CSV 내보내기 완료: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"CSV 내보내기 실패: {e}")
            raise

    def export_to_excel(self, data: List[Dict], filename: str = None) -> str:
        """
        Excel 형식으로 내보내기

        Args:
            data: 내보낼 데이터
            filename: 파일명 (없으면 자동 생성)

        Returns:
            저장된 파일 경로
        """
        if not data:
            raise ValueError("내보낼 데이터가 없습니다")

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crawled_data_{timestamp}.xlsx"

        filepath = self.output_dir / filename

        try:
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine='openpyxl')

            logger.info(f"Excel 내보내기 완료: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Excel 내보내기 실패: {e}")
            raise

    def export_to_all_formats(self, data: List[Dict], base_filename: str = None) -> Dict[str, str]:
        """
        모든 형식으로 내보내기

        Args:
            data: 내보낼 데이터
            base_filename: 기본 파일명 (확장자 제외)

        Returns:
            {형식: 파일경로} 딕셔너리
        """
        if not base_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"crawled_data_{timestamp}"

        results = {}

        # JSON
        try:
            json_file = self.export_to_json(data, f"{base_filename}.json")
            results['json'] = json_file
        except Exception as e:
            logger.error(f"JSON 내보내기 실패: {e}")

        # CSV
        try:
            csv_file = self.export_to_csv(data, f"{base_filename}.csv")
            results['csv'] = csv_file
        except Exception as e:
            logger.error(f"CSV 내보내기 실패: {e}")

        # Excel
        try:
            excel_file = self.export_to_excel(data, f"{base_filename}.xlsx")
            results['excel'] = excel_file
        except Exception as e:
            logger.error(f"Excel 내보내기 실패: {e}")

        return results

    def preview_data(self, data: List[Dict], max_items: int = 5) -> str:
        """
        데이터 미리보기 (텍스트 형식)

        Args:
            data: 미리볼 데이터
            max_items: 최대 표시 아이템 수

        Returns:
            미리보기 텍스트
        """
        if not data:
            return "데이터가 없습니다"

        preview_lines = []
        preview_lines.append(f"총 {len(data)}개 아이템\n")

        for idx, item in enumerate(data[:max_items]):
            preview_lines.append(f"--- 아이템 {idx + 1} ---")
            for key, value in item.items():
                # 값이 너무 길면 자르기
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:100] + "..."
                preview_lines.append(f"  {key}: {str_value}")
            preview_lines.append("")

        if len(data) > max_items:
            preview_lines.append(f"... 외 {len(data) - max_items}개 아이템")

        return "\n".join(preview_lines)

    def get_statistics(self, data: List[Dict]) -> Dict:
        """
        데이터 통계 정보

        Args:
            data: 분석할 데이터

        Returns:
            통계 정보 딕셔너리
        """
        if not data:
            return {"total_items": 0, "fields": {}}

        stats = {
            "total_items": len(data),
            "fields": {}
        }

        # 각 필드별 통계
        all_fields = set()
        for item in data:
            all_fields.update(item.keys())

        for field in all_fields:
            values = [item.get(field) for item in data]
            non_null_values = [v for v in values if v is not None and v != '']

            stats["fields"][field] = {
                "total_count": len(values),
                "non_null_count": len(non_null_values),
                "null_count": len(values) - len(non_null_values),
                "coverage": len(non_null_values) / len(values) * 100 if values else 0
            }

        return stats
