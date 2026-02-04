"""
Chart Research Agent
실시간 차트 구현을 위한 최적 솔루션을 연구하는 에이전트
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class ChartResearchAgent(BaseAgent):
    """차트 라이브러리 및 실시간 업데이트 전략 연구 전문 에이전트"""

    def __init__(self):
        super().__init__(
            name="Chart Research Specialist",
            description="실시간 차트 라이브러리와 구현 전략을 연구합니다."
        )

    async def analyze(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """차트 솔루션 연구"""

        result = {
            'recommended_libraries': self._get_recommended_libraries(),
            'update_strategies': self._get_update_strategies(),
            'performance_comparison': self._compare_performance(),
            'implementation_guide': self._get_implementation_guide()
        }

        return result

    def _get_recommended_libraries(self) -> list:
        """추천 차트 라이브러리"""
        return [
            {
                'name': 'streamlit-lightweight-charts-pro',
                'rank': 1,
                'pros': [
                    '금융 차트 전문 라이브러리',
                    '매우 가벼운 렌더링',
                    'TradingView 통합',
                    '멀티 패널 동기화'
                ],
                'cons': [
                    '추가 설치 필요',
                    '커뮤니티가 상대적으로 작음'
                ],
                'install': 'pip install streamlit-lightweight-charts-pro',
                'use_case': '실시간 금융 차트 (최고 성능)'
            },
            {
                'name': 'Plotly',
                'rank': 2,
                'pros': [
                    '이미 설치됨 (requirements.txt)',
                    '강력한 커스터마이징',
                    '좋은 문서화',
                    '다양한 차트 타입'
                ],
                'cons': [
                    'lightweight-charts보다 무거움',
                    '금융 차트 최적화는 약함'
                ],
                'install': 'Already installed',
                'use_case': '범용 차트, 커스터마이징 필요시'
            },
            {
                'name': 'TradingView Widgets',
                'rank': 3,
                'pros': [
                    '프로페셔널한 외관',
                    '설정 불필요',
                    '기술적 지표 내장'
                ],
                'cons': [
                    'KIS API 데이터 사용 불가',
                    '외부 의존성',
                    '인터넷 연결 필요'
                ],
                'install': 'chart_widget.py에 이미 구현됨',
                'use_case': '빠른 프로토타입, 외부 데이터 사용'
            }
        ]

    def _get_update_strategies(self) -> Dict[str, Any]:
        """업데이트 전략 비교"""
        return {
            'polling': {
                'method': 'Polling (현재 방식)',
                'latency': '30초',
                'pros': ['구현 간단', '안정적'],
                'cons': ['지연 시간', '서버 부하'],
                'recommendation': '초기 구현에만 사용'
            },
            'fragments': {
                'method': '@st.fragment (추천)',
                'latency': '5-10초',
                'pros': ['부분 업데이트', '낮은 서버 부하', 'Streamlit 1.37+'],
                'cons': ['여전히 폴링 기반'],
                'recommendation': '즉시 구현 가능한 최적 방법'
            },
            'websocket': {
                'method': 'WebSocket Streaming (최고)',
                'latency': '<100ms',
                'pros': ['진정한 실시간', '낮은 오버헤드'],
                'cons': ['구현 복잡도', 'KIS HTS ID 필요'],
                'recommendation': '프로덕션 환경 필수'
            }
        }

    def _compare_performance(self) -> list:
        """성능 비교표"""
        return [
            {
                'scenario': '5개 종목',
                'polling': '2-3초 전체 리로드',
                'fragments': '0.1초/차트',
                'websocket': '<0.05초'
            },
            {
                'scenario': '20개 종목',
                'polling': '8-10초 전체 리로드',
                'fragments': '0.1초/차트',
                'websocket': '<0.05초'
            },
            {
                'scenario': '메모리 사용량',
                'polling': 'High',
                'fragments': 'Medium',
                'websocket': 'Low'
            }
        ]

    def _get_implementation_guide(self) -> Dict[str, Any]:
        """구현 가이드"""
        return {
            'phase1': {
                'title': '즉시 구현 (1주)',
                'tasks': [
                    '@st.fragment 데코레이터 적용',
                    'Plotly 차트 통합',
                    '10초 자동 업데이트'
                ],
                'files': ['app.py', 'chart_widget.py']
            },
            'phase2': {
                'title': 'WebSocket 구현 (2-3주)',
                'tasks': [
                    'KIS WebSocket 클라이언트 생성',
                    'Rate Limiter 구현',
                    '멀티 레이어 캐싱'
                ],
                'files': [
                    'realtime_client.py',
                    'stream_manager.py',
                    'cache_manager.py'
                ]
            },
            'phase3': {
                'title': '최적화 (4주)',
                'tasks': [
                    'lightweight-charts 통합',
                    '멀티 계정 WebSocket',
                    '성능 모니터링'
                ],
                'files': ['realtime_chart_manager.py', 'metrics.py']
            }
        }
