"""
UI Design Agent
실시간 차트 UI/UX를 설계하는 에이전트
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class UIDesignAgent(BaseAgent):
    """차트 UI/UX 설계 전문 에이전트"""

    def __init__(self):
        super().__init__(
            name="UI/UX Designer",
            description="실시간 차트의 사용자 인터페이스를 설계합니다."
        )

    async def analyze(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """UI/UX 설계"""

        result = {
            'layout_design': self._design_layout(),
            'realtime_indicators': self._design_indicators(),
            'interactive_features': self._design_interactions(),
            'view_modes': self._design_view_modes(),
            'streamlit_components': self._recommend_components(),
            'color_scheme': self._design_colors()
        }

        return result

    def _design_layout(self) -> Dict[str, Any]:
        """레이아웃 설계"""
        return {
            'structure': 'Three-Panel Layout',
            'panels': [
                {
                    'name': 'Sidebar',
                    'width': '25%',
                    'content': [
                        '포트폴리오 요약',
                        '종목 선택',
                        '설정 및 필터',
                        '시스템 상태'
                    ]
                },
                {
                    'name': 'Main Chart Area',
                    'width': '55%',
                    'content': [
                        '실시간 차트',
                        '볼륨 차트',
                        '타임프레임 선택',
                        '기술적 지표'
                    ]
                },
                {
                    'name': 'Metrics Panel',
                    'width': '20%',
                    'content': [
                        '현재가',
                        '등락률',
                        '거래량',
                        '수익/손실'
                    ]
                }
            ],
            'responsive': {
                'desktop': '≥1024px - 3단 레이아웃',
                'tablet': '768-1023px - 2단 레이아웃',
                'mobile': '<768px - 단일 컬럼'
            }
        }

    def _design_indicators(self) -> list:
        """실시간 지표 설계"""
        return [
            {
                'name': '현재가 표시',
                'size': '48px',
                'font': 'Monospace',
                'color': 'Dynamic (Red/Green)',
                'update': 'Real-time',
                'format': '₩123,456'
            },
            {
                'name': '등락 지표',
                'elements': [
                    'Arrow (▲/▼)',
                    'Change Amount (±1,234원)',
                    'Change Percentage (±2.34%)'
                ],
                'color_scheme': {
                    'up': '#26a69a (Green)',
                    'down': '#ef5350 (Red)',
                    'neutral': '#78909c (Gray)'
                }
            },
            {
                'name': '연결 상태',
                'indicator_types': [
                    '🟢 Live - WebSocket 연결됨',
                    '🟡 Delayed - REST 폴링',
                    '🔴 Offline - 연결 끊김'
                ],
                'position': 'Top-right corner'
            },
            {
                'name': '업데이트 타임스탬프',
                'format': 'Updated: Xs ago',
                'animation': 'Pulse on update',
                'position': 'Below chart'
            },
            {
                'name': '성능 메트릭',
                'metrics': [
                    'Latency: 50ms',
                    'Cache Hit: 85%',
                    'FPS: 60'
                ],
                'display': 'Collapsible in sidebar'
            }
        ]

    def _design_interactions(self) -> Dict[str, Any]:
        """상호작용 기능 설계"""
        return {
            'zoom': {
                'methods': ['Scroll wheel', 'Pinch gesture', '+/- buttons'],
                'levels': ['1분', '5분', '30분', '1시간', '일봉']
            },
            'pan': {
                'method': 'Click and drag',
                'direction': 'Horizontal (time axis)',
                'reset': 'Double-click'
            },
            'timeframe_selector': {
                'options': ['1D', '5D', '1M', '3M', '6M', '1Y', '5Y', 'MAX'],
                'style': 'Button group',
                'position': 'Above chart'
            },
            'crosshair': {
                'enabled': True,
                'shows': ['Date/Time', 'OHLC', 'Volume'],
                'style': 'Dotted line',
                'tooltip': 'Floating box'
            },
            'range_selector': {
                'type': 'Miniature chart',
                'position': 'Below main chart',
                'draggable': True
            }
        }

    def _design_view_modes(self) -> list:
        """뷰 모드 설계"""
        return [
            {
                'mode': 'Grid View',
                'description': '여러 차트를 동시에 표시',
                'layouts': ['2x2', '3x2', '4x2'],
                'chart_height': '300px',
                'use_case': '포트폴리오 전체 모니터링'
            },
            {
                'mode': 'Tab View',
                'description': '탭으로 차트 전환',
                'max_tabs': 10,
                'shortcuts': 'Ctrl+1~9',
                'use_case': '종목별 상세 분석'
            },
            {
                'mode': 'Focus Mode',
                'description': '단일 차트 전체 화면',
                'chart_height': '70vh',
                'features': [
                    'Technical indicators',
                    'Drawing tools',
                    'Advanced analysis'
                ],
                'use_case': '심층 기술적 분석'
            },
            {
                'mode': 'Compact Tickers',
                'description': '빠른 가격 업데이트',
                'layout': '4-column grid',
                'height': '80px per ticker',
                'update_frequency': '5초',
                'use_case': '시장 감시'
            }
        ]

    def _recommend_components(self) -> list:
        """Streamlit 컴포넌트 추천"""
        return [
            {
                'component': 'st.columns()',
                'usage': '그리드 레이아웃 생성',
                'example': 'cols = st.columns([3, 1])'
            },
            {
                'component': 'st.tabs()',
                'usage': '탭 뷰 구현',
                'example': 'tab1, tab2 = st.tabs(["Chart 1", "Chart 2"])'
            },
            {
                'component': 'st.metric()',
                'usage': '가격/등락 표시',
                'example': 'st.metric("Price", "123,456", delta="+2.34%")'
            },
            {
                'component': '@st.fragment(run_every="5s")',
                'usage': '실시간 자동 업데이트',
                'example': '@st.fragment(run_every="5s")\ndef live_chart():'
            },
            {
                'component': 'st.plotly_chart()',
                'usage': 'Plotly 차트 렌더링',
                'example': 'st.plotly_chart(fig, use_container_width=True)'
            },
            {
                'component': 'streamlit-lightweight-charts',
                'usage': '고성능 금융 차트',
                'example': 'renderChart([chart_config])'
            },
            {
                'component': 'st.status()',
                'usage': '연결 상태 표시',
                'example': 'with st.status("🟢 Connected"):'
            }
        ]

    def _design_colors(self) -> Dict[str, Any]:
        """색상 스킴 설계"""
        return {
            'theme': 'Dark (금융 차트 표준)',
            'colors': {
                'background': '#0e1117',
                'surface': '#1e293b',
                'primary': '#2962ff',
                'up': '#26a69a',
                'down': '#ef5350',
                'text': '#ffffff',
                'text_secondary': '#94a3b8',
                'border': '#334155'
            },
            'chart_colors': {
                'candlestick_up': '#26a69a',
                'candlestick_down': '#ef5350',
                'volume_up': 'rgba(38, 166, 154, 0.5)',
                'volume_down': 'rgba(239, 83, 80, 0.5)',
                'line': '#2962ff',
                'grid': 'rgba(255, 255, 255, 0.1)'
            }
        }
