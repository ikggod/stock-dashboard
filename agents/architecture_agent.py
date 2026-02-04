"""
Architecture Analysis Agent
현재 코드베이스 아키텍처를 분석하는 에이전트
"""

from typing import Dict, Any, Optional
from pathlib import Path
import os
from .base_agent import BaseAgent


class ArchitectureAnalysisAgent(BaseAgent):
    """코드베이스 아키텍처 분석 전문 에이전트"""

    def __init__(self):
        super().__init__(
            name="Architecture Analyzer",
            description="현재 시스템 아키텍처를 분석하고 개선점을 제안합니다."
        )
        self.project_root = Path(__file__).parent.parent

    async def analyze(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """아키텍처 분석 수행"""

        result = {
            'components': self._analyze_components(),
            'dependencies': self._analyze_dependencies(),
            'data_flow': self._analyze_data_flow(),
            'recommendations': self._get_recommendations()
        }

        return result

    def _analyze_components(self) -> Dict[str, Any]:
        """시스템 컴포넌트 분석"""
        components = {}

        files = [
            'app.py',
            'portfolio_manager.py',
            'calculator.py',
            'chart_widget.py',
            'stock_data.py',
            'kis_api.py',
            'excel_template.py',
            'ocr_processor.py',
            'stock_list_fetcher.py'
        ]

        for file in files:
            filepath = self.project_root / file
            if filepath.exists():
                components[file] = {
                    'exists': True,
                    'size': os.path.getsize(filepath),
                    'role': self._get_component_role(file)
                }

        return components

    def _get_component_role(self, filename: str) -> str:
        """컴포넌트 역할 정의"""
        roles = {
            'app.py': 'Main UI Application (Streamlit)',
            'portfolio_manager.py': 'Portfolio CRUD Operations',
            'calculator.py': 'Profit/Loss Calculations',
            'chart_widget.py': 'TradingView Chart Integration',
            'stock_data.py': 'Multi-source Data Collector',
            'kis_api.py': 'Korea Investment Securities API',
            'excel_template.py': 'Excel Import/Export',
            'ocr_processor.py': 'Image Recognition for Bulk Import',
            'stock_list_fetcher.py': 'KRX Stock List Fetcher'
        }
        return roles.get(filename, 'Unknown Component')

    def _analyze_dependencies(self) -> Dict[str, Any]:
        """의존성 분석"""
        req_file = self.project_root / 'requirements.txt'

        if req_file.exists():
            with open(req_file, 'r') as f:
                deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            return {
                'count': len(deps),
                'libraries': deps,
                'critical': ['streamlit', 'yfinance', 'plotly']
            }

        return {'count': 0, 'libraries': []}

    def _analyze_data_flow(self) -> Dict[str, Any]:
        """데이터 흐름 분석"""
        return {
            'pattern': 'Multi-tier with fallback',
            'sources': [
                '1. KIS API (Real-time)',
                '2. Naver Finance (15-min delay)',
                '3. yfinance (Yahoo Finance)'
            ],
            'caching': '30-second TTL cache',
            'storage': 'JSON file (portfolio.json)'
        }

    def _get_recommendations(self) -> list:
        """개선 권장사항"""
        return [
            {
                'priority': 'HIGH',
                'item': 'WebSocket 실시간 스트리밍 구현',
                'benefit': '30초 폴링에서 실시간 업데이트로 개선'
            },
            {
                'priority': 'HIGH',
                'item': 'Rate Limiting 추가',
                'benefit': 'API 제한 초과 방지'
            },
            {
                'priority': 'MEDIUM',
                'item': 'SQLite로 데이터베이스 마이그레이션',
                'benefit': 'JSON보다 빠른 성능과 히스토리 관리'
            },
            {
                'priority': 'MEDIUM',
                'item': '멀티 레이어 캐싱',
                'benefit': '메모리 + 디스크 캐싱으로 성능 향상'
            }
        ]
