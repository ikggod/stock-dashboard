"""
Data Streaming Agent
실시간 데이터 스트리밍 아키텍처를 설계하는 에이전트
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class DataStreamingAgent(BaseAgent):
    """실시간 데이터 스트리밍 아키텍처 설계 전문 에이전트"""

    def __init__(self):
        super().__init__(
            name="Data Streaming Architect",
            description="실시간 데이터 스트리밍 시스템을 설계합니다."
        )

    async def analyze(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """스트리밍 아키텍처 설계"""

        result = {
            'architecture': self._design_architecture(),
            'components': self._define_components(),
            'data_flow': self._design_data_flow(),
            'performance_targets': self._set_performance_targets(),
            'implementation_priority': self._prioritize_implementation()
        }

        return result

    def _design_architecture(self) -> Dict[str, Any]:
        """시스템 아키텍처 설계"""
        return {
            'pattern': 'Event-Driven Streaming',
            'layers': [
                {
                    'name': 'Presentation Layer',
                    'component': 'Streamlit UI (app.py)',
                    'responsibility': '사용자 인터페이스, 차트 렌더링'
                },
                {
                    'name': 'Stream Management Layer',
                    'component': 'StreamManager',
                    'responsibility': 'WebSocket 연결 관리, 메시지 라우팅'
                },
                {
                    'name': 'Data Layer',
                    'component': 'Multi-Layer Cache + Queue',
                    'responsibility': '데이터 버퍼링, 캐싱, 영속성'
                },
                {
                    'name': 'Integration Layer',
                    'component': 'KIS API Client',
                    'responsibility': 'API 통신, 인증, Rate Limiting'
                }
            ],
            'communication': 'Async/Await with asyncio.Queue'
        }

    def _define_components(self) -> list:
        """핵심 컴포넌트 정의"""
        return [
            {
                'name': 'KISRealtimeClient',
                'file': 'realtime_client.py',
                'purpose': 'KIS WebSocket 연결 관리',
                'key_methods': [
                    'connect()',
                    'subscribe(stock_codes)',
                    'unsubscribe(stock_codes)',
                    '_message_handler()',
                    '_heartbeat()'
                ],
                'dependencies': ['mojito', 'websockets', 'asyncio']
            },
            {
                'name': 'StreamManager',
                'file': 'stream_manager.py',
                'purpose': '다중 WebSocket 연결 관리',
                'key_methods': [
                    'start(stock_codes)',
                    'add_stock(code)',
                    'remove_stock(code)',
                    'get_price(code)',
                    'stop()'
                ],
                'max_connections': 5,
                'stocks_per_connection': 41
            },
            {
                'name': 'RateLimiter',
                'file': 'rate_limiter.py',
                'purpose': 'Token Bucket 기반 Rate Limiting',
                'algorithm': 'Token Bucket',
                'limits': {
                    'rest_per_second': 15,
                    'websocket_per_second': 4,
                    'daily_quota': 8000
                }
            },
            {
                'name': 'MultiLayerCache',
                'file': 'cache_manager.py',
                'purpose': '2단계 캐싱 (메모리 + 디스크)',
                'layers': {
                    'L1': 'In-Memory (60초 TTL)',
                    'L2': 'SQLite (24시간 TTL)'
                },
                'max_size': 10000
            },
            {
                'name': 'MessageBuffer',
                'file': 'stream_manager.py',
                'purpose': '메시지 큐잉 및 배치 처리',
                'queue_size': 5000,
                'batch_size': 50,
                'overflow_protection': True
            }
        ]

    def _design_data_flow(self) -> Dict[str, Any]:
        """데이터 흐름 설계"""
        return {
            'realtime_flow': [
                '1. KIS WebSocket → 실시간 가격 수신',
                '2. MessageBuffer → 큐에 저장',
                '3. StreamManager → 배치 처리',
                '4. MultiLayerCache → L1/L2 캐싱',
                '5. Streamlit UI → 차트 업데이트'
            ],
            'fallback_flow': [
                '1. WebSocket 실패 감지',
                '2. REST API 폴링 시작',
                '3. RateLimiter → 속도 제한',
                '4. MultiLayerCache → 캐싱',
                '5. 자동 재연결 시도'
            ],
            'cache_flow': [
                '1. 가격 요청 수신',
                '2. L1 Cache 조회 (메모리)',
                '3. L1 Miss → L2 Cache 조회 (SQLite)',
                '4. L2 Miss → API 호출',
                '5. 결과를 L1, L2에 저장'
            ]
        }

    def _set_performance_targets(self) -> Dict[str, Any]:
        """성능 목표 설정"""
        return {
            'latency': {
                'websocket_update': '<100ms',
                'cache_hit_l1': '<1ms',
                'cache_hit_l2': '<10ms',
                'rest_fallback': '500-1000ms'
            },
            'throughput': {
                'messages_per_second': 200,
                'concurrent_stocks': 200,
                'concurrent_users': 20
            },
            'reliability': {
                'uptime': '99.9%',
                'reconnect_success_rate': '>95%',
                'cache_hit_rate': '>80%'
            },
            'resources': {
                'memory_base': '50MB',
                'memory_per_50_stocks': '1MB',
                'cpu_idle': '<5%',
                'cpu_active': '<20%',
                'network': '~10KB/s per connection'
            }
        }

    def _prioritize_implementation(self) -> Dict[str, Any]:
        """구현 우선순위"""
        return {
            'phase1_critical': {
                'duration': '1주',
                'components': [
                    'RateLimiter (rate_limiter.py)',
                    'InMemoryCache (cache_manager.py)',
                    'KISRealtimeClient 기본 구현 (realtime_client.py)'
                ],
                'reason': 'API 차단 방지 및 기본 실시간 기능'
            },
            'phase2_core': {
                'duration': '2주',
                'components': [
                    'StreamManager (stream_manager.py)',
                    'MessageBuffer',
                    'PersistentCache (SQLite)'
                ],
                'reason': '완전한 스트리밍 시스템'
            },
            'phase3_advanced': {
                'duration': '3-4주',
                'components': [
                    'Multi-Account WebSocket Manager',
                    'Circuit Breaker',
                    'Metrics & Monitoring'
                ],
                'reason': '프로덕션 안정성 및 확장성'
            }
        }
