import yfinance as yf
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import time
from kis_api import get_kis_instance

class StockDataCollector:
    """주식 현재가 및 데이터를 수집하는 클래스"""

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 30  # 30초 캐시
        self.kis_api = get_kis_instance()  # 한국투자증권 API

    def get_current_price_yfinance(self, stock_code: str) -> Optional[float]:
        """yfinance를 사용한 현재가 조회"""
        try:
            # 한국 주식은 .KS 또는 .KQ 접미사 필요
            ticker_symbol = self._format_ticker(stock_code)
            stock = yf.Ticker(ticker_symbol)
            data = stock.history(period="1d")

            if not data.empty:
                return float(data['Close'].iloc[-1])
            return None
        except Exception as e:
            print(f"yfinance 조회 오류 ({stock_code}): {e}")
            return None

    def get_current_price_naver(self, stock_code: str) -> Optional[float]:
        """네이버 금융을 사용한 현재가 조회"""
        try:
            url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            price_element = soup.select_one('.no_today .blind')

            if price_element:
                price_text = price_element.text.strip().replace(',', '')
                return float(price_text)
            return None
        except Exception as e:
            print(f"네이버 금융 조회 오류 ({stock_code}): {e}")
            return None

    def get_current_price(self, stock_code: str, method: str = "auto") -> Optional[float]:
        """
        현재가 조회 (캐시 포함)

        Args:
            stock_code: 종목코드
            method: "auto" (자동: KIS → naver), "kis", "naver", "yfinance"
        """
        # 캐시 확인
        cache_key = f"{stock_code}_{method}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_timeout:
                return cached_data

        # 데이터 수집
        price = None

        if method == "auto":
            # 1순위: 한국투자증권 API (실시간, 정확)
            price = self.get_current_price_kis(stock_code)
            # 2순위: 네이버 금융 (무료, 지연)
            if price is None:
                price = self.get_current_price_naver(stock_code)
        elif method == "kis":
            price = self.get_current_price_kis(stock_code)
        elif method == "naver":
            price = self.get_current_price_naver(stock_code)
        elif method == "yfinance":
            price = self.get_current_price_yfinance(stock_code)

        # 캐시 저장
        if price is not None:
            self.cache[cache_key] = (price, time.time())

        return price

    def get_current_price_kis(self, stock_code: str) -> Optional[float]:
        """한국투자증권 API로 현재가 조회 (실시간)"""
        try:
            if self.kis_api and self.kis_api.broker:
                return self.kis_api.get_current_price(stock_code)
            return None
        except Exception as e:
            print(f"KIS API 조회 오류 ({stock_code}): {e}")
            return None

    def get_stock_info_naver(self, stock_code: str) -> Optional[Dict]:
        """네이버 금융에서 주식 상세 정보 조회"""
        try:
            url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 현재가
            price_element = soup.select_one('.no_today .blind')
            current_price = float(price_element.text.strip().replace(',', '')) if price_element else None

            # 전일 대비
            change_element = soup.select_one('.no_exday .blind')
            change = change_element.text.strip() if change_element else None

            # 등락률
            rate_element = soup.select_one('.no_exday .blind')
            rate = None
            if rate_element:
                rate_elements = soup.select('.no_exday .blind')
                if len(rate_elements) > 1:
                    rate = rate_elements[1].text.strip()

            # 종목명
            name_element = soup.select_one('.wrap_company h2 a')
            stock_name = name_element.text.strip() if name_element else None

            return {
                "name": stock_name,
                "code": stock_code,
                "current_price": current_price,
                "change": change,
                "rate": rate
            }
        except Exception as e:
            print(f"네이버 금융 상세 정보 조회 오류 ({stock_code}): {e}")
            return None

    def _format_ticker(self, stock_code: str) -> str:
        """한국 주식 코드를 yfinance 형식으로 변환"""
        # 코스피: .KS, 코스닥: .KQ
        if len(stock_code) == 6 and stock_code.isdigit():
            # 간단한 구분 (완벽하지 않음)
            # 코스닥 종목은 보통 더 높은 번호
            if stock_code.startswith(('0', '1', '2', '3')):
                return f"{stock_code}.KS"  # 코스피
            else:
                return f"{stock_code}.KQ"  # 코스닥
        return stock_code

    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
