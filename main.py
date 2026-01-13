"""
AI-Powered Universal Web Crawler
메인 진입점
"""

import sys
import argparse
import logging
from pathlib import Path

# GUI 모드
def run_gui_mode(advanced=False):
    """GUI 모드 실행"""
    if advanced:
        # 고급 모드: 5-탭 인터페이스
        from gui.app import run_gui
        run_gui()
    else:
        # 기본 모드: 단계별 위저드 인터페이스
        from gui.wizard_app import run_wizard_gui
        run_wizard_gui()


# CLI 모드
def run_cli_mode(args):
    """CLI 모드 실행"""
    from src.browser_connector import BrowserConnector
    from src.dom_extractor import DOMExtractor
    from src.llm_analyzer import LLMAnalyzer
    from src.data_extractor import DataExtractor
    from src.exporter import DataExporter
    import json

    # 설정 로드
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json 파일이 없습니다. 먼저 설정을 완료하세요.")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    api_key = config.get('openai_api_key')
    if not api_key:
        print("❌ OpenAI API Key가 설정되지 않았습니다.")
        return

    print("🕷️  AI-Powered Universal Web Crawler")
    print("=" * 50)

    # 브라우저 연결
    print("\n[1] 브라우저 연결 중...")
    browser = BrowserConnector(config)

    if args.cdp_url:
        browser.connect_to_existing_browser(args.cdp_url)
        print(f"✓ 기존 브라우저 연결 완료: {args.cdp_url}")
    else:
        browser.start_new_browser(headless=args.headless)
        print("✓ 새 브라우저 시작 완료")

    try:
        # URL 이동
        if args.url:
            print(f"\n[2] 페이지 이동: {args.url}")
            browser.navigate_to(args.url)
            print("✓ 페이지 로드 완료")

        # 크롤링 요청
        if args.request:
            print(f"\n[3] 크롤링 요청: {args.request}")

            # DOM 추출
            print("   페이지 분석 중...")
            extractor = DOMExtractor(browser.page)
            html = extractor.get_full_html()

            # LLM 분석
            print("   LLM 분석 중...")
            model = args.model or config.get('default_model', 'gpt-4-turbo-preview')
            analyzer = LLMAnalyzer(api_key, model)
            strategy = analyzer.generate_selectors_from_html(html, args.request)

            print("✓ 크롤링 전략 생성 완료")
            print(f"   Container: {strategy.get('container_selector')}")
            print(f"   Fields: {len(strategy.get('fields', []))}개")

            # 데이터 추출
            print("\n[4] 데이터 추출 중...")
            data_extractor = DataExtractor(browser.page)

            if args.max_pages > 1:
                data = data_extractor.extract_with_pagination(
                    strategy,
                    max_pages=args.max_pages
                )
            else:
                data = data_extractor.extract_data(strategy)

            print(f"✓ {len(data)}개 아이템 추출 완료")

            # 데이터 내보내기
            if data:
                print("\n[5] 데이터 저장 중...")
                exporter = DataExporter()

                if args.output:
                    # 지정된 형식으로 저장
                    if args.format == 'json':
                        filepath = exporter.export_to_json(data, args.output)
                    elif args.format == 'csv':
                        filepath = exporter.export_to_csv(data, args.output)
                    elif args.format == 'excel':
                        filepath = exporter.export_to_excel(data, args.output)

                    print(f"✓ 저장 완료: {filepath}")
                else:
                    # 모든 형식으로 저장
                    results = exporter.export_to_all_formats(data)
                    print("✓ 저장 완료:")
                    for fmt, path in results.items():
                        print(f"   - {fmt}: {path}")

                # 미리보기
                if not args.no_preview:
                    print("\n" + "=" * 50)
                    print("데이터 미리보기:")
                    print("=" * 50)
                    preview = exporter.preview_data(data, max_items=3)
                    print(preview)

    finally:
        # 브라우저 종료
        if not args.keep_open:
            print("\n브라우저 연결 해제...")
            browser.close()
            print("✓ 완료")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="AI-Powered Universal Web Crawler - LLM 기반 범용 웹 크롤러"
    )

    parser.add_argument(
        '--cli',
        action='store_true',
        help='CLI 모드 실행 (기본: GUI 모드)'
    )

    parser.add_argument(
        '--advanced',
        action='store_true',
        help='고급 GUI 모드 (5-탭 인터페이스, 기본: 단계별 위저드)'
    )

    # CLI 모드 옵션
    parser.add_argument(
        '--url',
        type=str,
        help='크롤링할 URL'
    )

    parser.add_argument(
        '--request',
        type=str,
        help='크롤링 요청 (자연어)'
    )

    parser.add_argument(
        '--cdp-url',
        type=str,
        help='기존 브라우저 CDP URL (예: http://localhost:9222)'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='헤드리스 모드로 실행'
    )

    parser.add_argument(
        '--model',
        type=str,
        help='사용할 OpenAI 모델 (예: gpt-4-turbo-preview)'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        default=1,
        help='최대 페이지 수 (기본: 1)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='출력 파일명'
    )

    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'csv', 'excel'],
        default='json',
        help='출력 형식 (기본: json)'
    )

    parser.add_argument(
        '--no-preview',
        action='store_true',
        help='데이터 미리보기 비활성화'
    )

    parser.add_argument(
        '--keep-open',
        action='store_true',
        help='브라우저 연결 유지'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='상세 로그 출력'
    )

    args = parser.parse_args()

    # 로깅 설정
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 모드 선택
    if args.cli:
        run_cli_mode(args)
    else:
        run_gui_mode(advanced=args.advanced)


if __name__ == "__main__":
    main()
