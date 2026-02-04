"""
KIS API Analysis Agent
한국투자증권 API 기능을 분석하는 에이전트
"""

from typing import Dict, Any, Optional
from pathlib import Path
from .base_agent import BaseAgent


class KISAPIAnalysisAgent(BaseAgent):
    """KIS API 분석 및 통합 전략 수립 전문 에이전트"""

    def __init__(self):
        super().__init__(
            name="KIS API Specialist",
            description="한국투자증권 API의 기능과 제약사항을 분석합니다."
        )
        self.project_root = Path(__file__).parent.parent

    async def analyze(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """KIS API 분석"""

        result = {
            'api_capabilities': self._analyze_capabilities(),
            'websocket_support': self._analyze_websocket(),
            'rate_limits': self._analyze_rate_limits(),
            'authentication': self._analyze_auth(),
            'realtime_endpoints': self._list_realtime_endpoints(),
            'limitations': self._identify_limitations(),
            'integration_recommendations': self._get_recommendations()
        }

        return result

    def _analyze_capabilities(self) -> Dict[str, Any]:
        """API 기능 분석"""
        return {
            'rest_api': {
                'available': True,
                'library': 'mojito (한국투자증권 Python 래퍼)',
                'endpoints': [
                    'fetch_price() - 현재가 조회',
                    'fetch_balance() - 잔고 조회',
                    'fetch_ohlcv() - OHLCV 데이터',
                    'buy/sell() - 주문 실행'
                ]
            },
            'websocket_api': {
                'available': True,
                'class': 'mojito.KoreaInvestmentWS',
                'transaction_types': [
                    'H0STCNT0 - 실시간 체결가',
                    'H0STASP0 - 실시간 호가',
                    'H0STCNI0 - 실시간 체결 통보'
                ]
            },
            'current_implementation': {
                'file': 'kis_api.py',
                'status': 'REST API만 구현됨',
                'needs': 'WebSocket 통합 필요'
            }
        }

    def _analyze_websocket(self) -> Dict[str, Any]:
        """WebSocket 지원 분석"""
        return {
            'protocol': 'WebSocket Secure (WSS)',
            'endpoint': 'wss://ops.koreainvestment.com:21000',
            'max_subscriptions': 41,
            'transaction_ids': {
                'H0STCNT0': {
                    'name': '실시간 체결가',
                    'data': ['체결가', '체결량', '시간'],
                    'latency': '<100ms'
                },
                'H0STASP0': {
                    'name': '실시간 호가',
                    'data': ['매수호가', '매도호가', '잔량'],
                    'latency': '<100ms'
                }
            },
            'requirements': [
                'HTS ID 필요',
                'App Key/Secret',
                'PingPong 응답 필수'
            ],
            'example_code': '''
broker_ws = mojito.KoreaInvestmentWS(
    key, secret,
    ["H0STCNT0"],  # Transaction types
    ["005930"],    # Stock codes
    user_id="hts_id"
)
broker_ws.start()
data = broker_ws.get()  # Non-blocking
            '''
        }

    def _analyze_rate_limits(self) -> Dict[str, Any]:
        """Rate Limit 분석"""
        return {
            'rest_api': {
                'real_account': {
                    'limit': '초당 20회',
                    'algorithm': 'Sliding Window',
                    'error_code': 'EGW00201',
                    'recommended': '초당 15회 (안전 마진)'
                },
                'mock_account': {
                    'limit': '초당 5회',
                    'recommended': '초당 4회'
                }
            },
            'websocket': {
                'subscriptions': '세션당 41개 종목',
                'messages': '초당 5개 메시지',
                'solution': '멀티 계정 전략 (41개 초과시)'
            },
            'token': {
                'validity': '24시간',
                'issuance_limit': '분당 1회',
                'best_practice': '일 1회 발급 후 캐싱'
            },
            'daily_quota': {
                'total': '일 10,000회',
                'recommended': '일 8,000회 (안전 마진)'
            }
        }

    def _analyze_auth(self) -> Dict[str, Any]:
        """인증 메커니즘 분석"""
        return {
            'credentials': {
                'app_key': 'REST API 앱 키',
                'app_secret': 'REST API 시크릿',
                'hts_id': 'WebSocket 필수 (HTS ID)'
            },
            'token_lifecycle': {
                'duration': '24시간',
                'auto_refresh': True,
                'storage': 'kis_config.json에 저장됨'
            },
            'current_implementation': {
                'file': 'kis_api.py',
                'method': 'Singleton pattern',
                'storage': 'JSON file configuration'
            },
            'recommendations': [
                'Token 캐싱 강화 (분당 1회 제한)',
                'HTS ID 설정 UI 추가',
                'Credential 암호화 고려'
            ]
        }

    def _list_realtime_endpoints(self) -> list:
        """실시간 엔드포인트 목록"""
        return [
            {
                'type': 'WebSocket',
                'tr_id': 'H0STCNT0',
                'name': '실시간 체결가',
                'fields': [
                    'stck_prpr - 현재가',
                    'prdy_vrss - 전일 대비',
                    'prdy_ctrt - 등락률',
                    'acml_vol - 누적 거래량',
                    'stck_cntg_hour - 체결 시간'
                ],
                'use_case': '실시간 가격 차트'
            },
            {
                'type': 'WebSocket',
                'tr_id': 'H0STASP0',
                'name': '실시간 호가',
                'fields': [
                    'askp1~10 - 매도호가 1~10',
                    'bidp1~10 - 매수호가 1~10',
                    'askp_rsqn1~10 - 매도잔량',
                    'bidp_rsqn1~10 - 매수잔량'
                ],
                'use_case': '오더북 차트'
            },
            {
                'type': 'REST',
                'method': 'fetch_price()',
                'name': '현재가 조회',
                'latency': '500-1000ms',
                'use_case': 'Fallback when WebSocket fails'
            }
        ]

    def _identify_limitations(self) -> list:
        """제약사항 파악"""
        return [
            {
                'limitation': 'WebSocket 종목 수 제한',
                'detail': '세션당 최대 41개 종목',
                'impact': '대규모 포트폴리오 모니터링 제한',
                'solution': '멀티 계정 WebSocket 매니저 구현'
            },
            {
                'limitation': 'Rate Limiting',
                'detail': '초당 20회 (REST), 초당 5회 (WS)',
                'impact': 'API 차단 위험',
                'solution': 'Token Bucket Rate Limiter 구현'
            },
            {
                'limitation': 'Token 재발급 제한',
                'detail': '분당 1회만 가능',
                'impact': '빈번한 재시작시 인증 실패',
                'solution': 'Token 캐싱 및 만료 5분 전 갱신'
            },
            {
                'limitation': 'HTS ID 필수',
                'detail': 'WebSocket 연결시 올바른 HTS ID 필요',
                'impact': '잘못된 ID시 연결 실패',
                'solution': 'kis_config.json에 HTS ID 설정 추가'
            },
            {
                'limitation': '시장 시간 외 제한',
                'detail': '장 시간(8:55-15:30) 외 WebSocket 불안정',
                'impact': '장 마감 후 데이터 수신 불가',
                'solution': '시장 시간 감지 및 REST 폴백'
            }
        ]

    def _get_recommendations(self) -> Dict[str, Any]:
        """통합 권장사항"""
        return {
            'immediate': {
                'priority': 'HIGH',
                'tasks': [
                    {
                        'task': 'Rate Limiter 구현',
                        'file': 'rate_limiter.py',
                        'benefit': 'API 차단 방지'
                    },
                    {
                        'task': 'Token Manager 강화',
                        'file': 'kis_api.py',
                        'benefit': '안정적인 인증'
                    },
                    {
                        'task': 'WebSocket 클라이언트 추가',
                        'file': 'realtime_client.py',
                        'benefit': '실시간 데이터 스트리밍'
                    }
                ]
            },
            'short_term': {
                'priority': 'MEDIUM',
                'tasks': [
                    {
                        'task': '멀티 계정 WebSocket',
                        'benefit': '41개 이상 종목 지원'
                    },
                    {
                        'task': 'Hybrid 데이터 소스',
                        'benefit': 'WebSocket 실패시 REST 폴백'
                    },
                    {
                        'task': '시장 시간 검증',
                        'benefit': '불필요한 연결 시도 방지'
                    }
                ]
            },
            'code_examples': {
                'rate_limiter': '''
class RateLimiter:
    def __init__(self, calls_per_second=15):
        self.calls_per_second = calls_per_second
        self.last_call_times = []

    def wait_if_needed(self):
        # Token bucket implementation
        pass
''',
                'websocket_client': '''
ws = mojito.KoreaInvestmentWS(
    app_key, app_secret,
    ["H0STCNT0"],
    ["005930", "000660"],
    user_id=hts_id
)
ws.start()
'''
            }
        }
