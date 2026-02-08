"""
실시간 주식 데이터 WebSocket 클라이언트
한국투자증권 API WebSocket을 사용한 실시간 시세 수신
"""
import mojito
import threading
import time
from typing import Dict, List, Callable, Optional
from collections import deque
import streamlit as st


class RealtimeStockClient:
    """실시간 주식 데이터 수신 클라이언트"""

    def __init__(self, app_key: str, app_secret: str, hts_id: str, stock_codes: List[str]):
        """
        초기화

        Args:
            app_key: API 앱 키
            app_secret: API 앱 시크릿
            hts_id: HTS ID (WebSocket 필수)
            stock_codes: 실시간 구독할 종목 코드 리스트 (최대 41개)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.hts_id = hts_id
        self.stock_codes = stock_codes[:41]  # 최대 41개 제한

        self.ws = None
        self.running = False
        self.thread = None

        # 최신 데이터 저장 (종목코드 -> 데이터)
        self.latest_data = {}

        # 데이터 히스토리 (종목코드 -> deque)
        self.history = {}
        for code in self.stock_codes:
            self.history[code] = deque(maxlen=100)  # 최근 100개 데이터만 유지

    def start(self) -> bool:
        """WebSocket 연결 시작"""
        try:
            # WebSocket 생성 (HTS ID는 선택사항)
            ws_params = {
                'key': self.app_key,
                'secret': self.app_secret,
                'tr_type': ["H0STCNT0"],  # 실시간 체결가
                'tr_key': self.stock_codes
            }

            # HTS ID가 있으면 추가
            if self.hts_id:
                ws_params['user_id'] = self.hts_id

            self.ws = mojito.KoreaInvestmentWS(**ws_params)

            # WebSocket 시작
            self.ws.start()

            # 데이터 수신 스레드 시작
            self.running = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()

            return True

        except Exception as e:
            print(f"WebSocket 시작 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def stop(self):
        """WebSocket 연결 종료"""
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=1)

    def _receive_loop(self):
        """데이터 수신 루프 (백그라운드 스레드)"""
        while self.running:
            try:
                # 데이터 수신 (논블로킹)
                data = self.ws.get()

                if data:
                    # 종목코드 추출
                    stock_code = data.get('MKSC_SHRN_ISCD')  # 종목코드
                    if stock_code:
                        # 데이터 파싱
                        parsed = {
                            'code': stock_code,
                            'price': float(data.get('STCK_PRPR', 0)),  # 현재가
                            'change': int(data.get('PRDY_VRSS', 0)),  # 전일대비
                            'change_rate': float(data.get('PRDY_CTRT', 0)),  # 등락률
                            'volume': int(data.get('ACML_VOL', 0)),  # 누적거래량
                            'time': data.get('STCK_CNTG_HOUR', '')  # 체결시간
                        }

                        # 최신 데이터 저장
                        self.latest_data[stock_code] = parsed

                        # 히스토리 추가
                        if stock_code in self.history:
                            self.history[stock_code].append(parsed)

                time.sleep(0.01)  # CPU 사용률 조절

            except Exception as e:
                print(f"데이터 수신 오류: {e}")
                time.sleep(1)

    def get_latest_price(self, stock_code: str) -> Optional[float]:
        """최신 현재가 조회"""
        if stock_code in self.latest_data:
            return self.latest_data[stock_code]['price']
        return None

    def get_latest_data(self, stock_code: str) -> Optional[Dict]:
        """최신 데이터 조회"""
        return self.latest_data.get(stock_code)

    def get_history(self, stock_code: str) -> List[Dict]:
        """데이터 히스토리 조회"""
        if stock_code in self.history:
            return list(self.history[stock_code])
        return []


# 전역 WebSocket 클라이언트 (싱글톤)
_realtime_client = None


def get_realtime_client() -> Optional[RealtimeStockClient]:
    """실시간 클라이언트 인스턴스 반환"""
    global _realtime_client
    return _realtime_client


def init_realtime_client(app_key: str, app_secret: str, hts_id: str, stock_codes: List[str]) -> bool:
    """실시간 클라이언트 초기화"""
    global _realtime_client

    # 기존 클라이언트 종료
    if _realtime_client:
        _realtime_client.stop()

    # 새 클라이언트 생성 및 시작
    _realtime_client = RealtimeStockClient(app_key, app_secret, hts_id, stock_codes)
    return _realtime_client.start()


def stop_realtime_client():
    """실시간 클라이언트 종료"""
    global _realtime_client
    if _realtime_client:
        _realtime_client.stop()
        _realtime_client = None
