"""
한국투자증권 API 연동 모듈
실시간 주식 시세 조회
"""
import mojito
from typing import Optional, Dict
import os
import json

class KISStockAPI:
    """한국투자증권 API 클래스"""

    def __init__(self, app_key: str = None, app_secret: str = None, account_no: str = None, is_real: bool = False):
        """
        초기화

        Args:
            app_key: API 앱 키
            app_secret: API 앱 시크릿
            account_no: 계좌번호 (선택사항)
            is_real: 실전투자 여부 (False=모의투자)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no
        self.is_real = is_real
        self.broker = None

        # 설정 파일에서 로드
        if not app_key:
            self.load_config()

    def load_config(self):
        """설정 파일에서 API 키 로드"""
        config_path = "kis_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.app_key = config.get('app_key')
                    self.app_secret = config.get('app_secret')
                    self.account_no = config.get('account_no')
                    self.is_real = config.get('is_real', False)
            except Exception as e:
                print(f"설정 파일 로드 오류: {e}")

    def save_config(self):
        """설정을 파일에 저장"""
        config = {
            'app_key': self.app_key,
            'app_secret': self.app_secret,
            'account_no': self.account_no,
            'is_real': self.is_real
        }
        with open('kis_config.json', 'w') as f:
            json.dump(config, f, indent=2)

    def initialize(self) -> bool:
        """API 초기화"""
        if not self.app_key or not self.app_secret:
            return False

        try:
            # mojito 브로커 초기화
            self.broker = mojito.KoreaInvestment(
                api_key=self.app_key,
                api_secret=self.app_secret,
                acc_no=self.account_no or "",
                mock=not self.is_real  # mock=True이면 모의투자
            )
            return True
        except Exception as e:
            print(f"API 초기화 오류: {e}")
            return False

    def get_current_price(self, stock_code: str) -> Optional[float]:
        """
        실시간 현재가 조회

        Args:
            stock_code: 종목코드 (6자리)

        Returns:
            현재가 (원)
        """
        if not self.broker:
            if not self.initialize():
                return None

        try:
            # 종목코드 6자리로 맞춤
            stock_code = str(stock_code).zfill(6)

            # 현재가 조회
            resp = self.broker.fetch_price(stock_code)

            if resp and 'output' in resp:
                current_price = float(resp['output']['stck_prpr'])  # 주식 현재가
                return current_price

            return None

        except Exception as e:
            print(f"현재가 조회 오류 ({stock_code}): {e}")
            return None

    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """
        종목 상세 정보 조회

        Returns:
            {
                'name': 종목명,
                'code': 종목코드,
                'current_price': 현재가,
                'change': 전일대비,
                'change_rate': 등락률,
                'volume': 거래량
            }
        """
        if not self.broker:
            if not self.initialize():
                return None

        try:
            stock_code = str(stock_code).zfill(6)
            resp = self.broker.fetch_price(stock_code)

            if resp and 'output' in resp:
                output = resp['output']
                return {
                    'name': output.get('prdt_name', ''),  # 상품명
                    'code': stock_code,
                    'current_price': float(output.get('stck_prpr', 0)),  # 주식 현재가
                    'change': int(output.get('prdy_vrss', 0)),  # 전일 대비
                    'change_rate': float(output.get('prdy_ctrt', 0)),  # 전일 대비율
                    'volume': int(output.get('acml_vol', 0))  # 누적 거래량
                }

            return None

        except Exception as e:
            print(f"종목 정보 조회 오류 ({stock_code}): {e}")
            return None

    def test_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            # 삼성전자로 테스트
            price = self.get_current_price('005930')
            return price is not None
        except:
            return False


# 전역 인스턴스
_kis_instance = None

def get_kis_instance():
    """싱글톤 KIS API 인스턴스 반환"""
    global _kis_instance
    if _kis_instance is None:
        _kis_instance = KISStockAPI()
    return _kis_instance


def set_kis_credentials(app_key: str, app_secret: str, account_no: str = "", is_real: bool = False):
    """API 키 설정"""
    global _kis_instance
    _kis_instance = KISStockAPI(app_key, app_secret, account_no, is_real)
    _kis_instance.save_config()
    return _kis_instance.initialize()
