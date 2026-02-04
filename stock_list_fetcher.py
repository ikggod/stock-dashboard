import requests
import pandas as pd
from bs4 import BeautifulSoup
import json

def fetch_all_krx_stocks():
    """한국거래소 전체 상장 종목 가져오기"""
    try:
        # 네이버 금융 API 사용
        url = "https://api.stock.naver.com/stock/exchange/KOSPI/marketValue"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        all_stocks = []

        # KOSPI
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for stock in data.get('stocks', []):
                    all_stocks.append({
                        'name': stock.get('stockName', ''),
                        'code': stock.get('stockCode', '')
                    })
        except:
            pass

        # KOSDAQ
        url_kosdaq = "https://api.stock.naver.com/stock/exchange/KOSDAQ/marketValue"
        try:
            response = requests.get(url_kosdaq, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for stock in data.get('stocks', []):
                    all_stocks.append({
                        'name': stock.get('stockName', ''),
                        'code': stock.get('stockCode', '')
                    })
        except:
            pass

        if all_stocks:
            return all_stocks

    except Exception as e:
        print(f"API 조회 오류: {e}")

    # API 실패 시 대체 방법: 웹 크롤링
    return fetch_from_web_fallback()


def fetch_from_web_fallback():
    """웹 크롤링으로 종목 리스트 가져오기 (대체 방법)"""
    all_stocks = []

    try:
        # 네이버 금융 국내증시 페이지
        url = "https://finance.naver.com/sise/sise_market_sum.naver"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for page in range(1, 50):  # 50페이지 정도면 대부분 종목 커버
            try:
                params = {'sosok': '0', 'page': page}  # 0: KOSPI
                response = requests.get(url, params=params, headers=headers, timeout=5)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    table = soup.select_one('table.type_2')

                    if table:
                        rows = table.select('tr')
                        for row in rows:
                            cols = row.select('td')
                            if len(cols) >= 2:
                                link = row.select_one('a')
                                if link:
                                    name = link.text.strip()
                                    href = link.get('href', '')
                                    if 'code=' in href:
                                        code = href.split('code=')[1].split('&')[0]
                                        all_stocks.append({'name': name, 'code': code})
            except:
                continue

        # KOSDAQ
        for page in range(1, 50):
            try:
                params = {'sosok': '1', 'page': page}  # 1: KOSDAQ
                response = requests.get(url, params=params, headers=headers, timeout=5)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    table = soup.select_one('table.type_2')

                    if table:
                        rows = table.select('tr')
                        for row in rows:
                            cols = row.select('td')
                            if len(cols) >= 2:
                                link = row.select_one('a')
                                if link:
                                    name = link.text.strip()
                                    href = link.get('href', '')
                                    if 'code=' in href:
                                        code = href.split('code=')[1].split('&')[0]
                                        all_stocks.append({'name': name, 'code': code})
            except:
                continue

    except Exception as e:
        print(f"웹 크롤링 오류: {e}")

    return all_stocks


def get_stock_list_with_fallback():
    """전체 종목 리스트 가져오기 (여러 방법 시도)"""

    # 방법 1: API 시도
    stocks = fetch_all_krx_stocks()

    if stocks and len(stocks) > 100:
        print(f"[OK] {len(stocks)} stocks loaded")
        return stocks

    # 방법 2: 기본 리스트 사용 (최후의 수단)
    print("[WARNING] Online fetch failed, using default list")
    return get_default_stock_list()


def get_default_stock_list():
    """기본 종목 리스트 (2000개 이상)"""
    # 실제로는 여기에 미리 준비된 전체 종목 리스트를 넣어야 합니다
    # 임시로 주요 종목들만 포함

    stocks = [
        {'name': '삼성전자', 'code': '005930'},
        {'name': 'SK하이닉스', 'code': '000660'},
        {'name': '대한전선', 'code': '001440'},
        {'name': '디아이', 'code': '003160'},
        # ... 더 많은 종목 추가 필요
    ]

    # TODO: 전체 종목 리스트를 파일에서 로드하도록 개선
    return stocks


if __name__ == "__main__":
    stocks = get_stock_list_with_fallback()
    print(f"총 {len(stocks)}개 종목")
    if stocks:
        print("샘플:", stocks[:5])
