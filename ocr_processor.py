import easyocr
import re
from typing import List, Dict, Optional
import numpy as np
from PIL import Image

class StockImageOCR:
    """주식 화면 이미지에서 종목 정보를 추출하는 OCR 클래스"""

    def __init__(self):
        # EasyOCR Reader 초기화 (한글 + 영어)
        self.reader = None

    def initialize_reader(self):
        """OCR Reader 초기화 (처음 사용 시에만)"""
        if self.reader is None:
            print("OCR 모델 로딩 중... (최초 1회, 30초-1분 소요)")
            self.reader = easyocr.Reader(['ko', 'en'], gpu=True)
            print("OCR 모델 로딩 완료!")

    def extract_text_from_image(self, image) -> List[tuple]:
        """이미지에서 텍스트 추출"""
        self.initialize_reader()

        # PIL Image를 numpy array로 변환
        if isinstance(image, Image.Image):
            image = np.array(image)

        # OCR 실행
        results = self.reader.readtext(image)
        return results

    def parse_stock_info(self, ocr_results: List[tuple]) -> List[Dict]:
        """OCR 결과에서 종목 정보 파싱"""
        stocks = []

        # OCR 결과를 텍스트만 추출
        texts = [result[1] for result in ocr_results]

        print("=== OCR 인식 결과 ===")
        for i, text in enumerate(texts):
            print(f"{i}: {text}")
        print("=" * 50)

        # 종목 정보 패턴 찾기
        for i, text in enumerate(texts):
            # 종목명 후보 찾기 (한글 포함)
            if self._is_stock_name(text):
                stock_info = self._extract_stock_details(texts, i)
                if stock_info:
                    stocks.append(stock_info)

        return stocks

    def _is_stock_name(self, text: str) -> bool:
        """종목명인지 판단"""
        # 한글이 포함되어 있고, 숫자가 아니고, 특수문자가 많지 않으면 종목명으로 간주
        has_korean = bool(re.search('[가-힣]', text))
        not_only_numbers = not text.replace(',', '').replace('.', '').isdigit()
        return has_korean and not_only_numbers and len(text) >= 2

    def _extract_stock_details(self, texts: List[str], start_idx: int) -> Optional[Dict]:
        """종목명 근처에서 상세 정보 추출"""
        stock_name = texts[start_idx]

        # 주변 텍스트에서 정보 찾기
        stock_code = None
        quantity = None
        avg_price = None
        current_price = None
        investment_amount = None

        # 종목명 이후 10개 항목 내에서 찾기
        search_range = texts[start_idx:start_idx + 15]

        for text in search_range:
            # 종목코드 (6자리 숫자)
            if not stock_code:
                code_match = re.search(r'\b(\d{6})\b', text)
                if code_match:
                    stock_code = code_match.group(1)

            # 수량 (주 단위)
            if not quantity:
                quantity_match = re.search(r'(\d[\d,]*)\s*주', text)
                if quantity_match:
                    quantity = int(quantity_match.group(1).replace(',', ''))

            # 가격 (원 단위, 쉼표 포함)
            prices = re.findall(r'(\d[\d,]+)\s*원', text)
            if prices:
                # 숫자 변환
                price_values = [int(p.replace(',', '')) for p in prices]

                # 평균단가는 보통 가장 작은 값
                if not avg_price and price_values:
                    avg_price = min(price_values)

                # 투자금액은 보통 가장 큰 값
                if not investment_amount and price_values:
                    investment_amount = max(price_values)

        # 최소한 종목명과 하나의 정보는 있어야 함
        if stock_name and (stock_code or quantity or avg_price):
            result = {
                'name': stock_name,
                'code': stock_code,
                'quantity': quantity,
                'avg_price': avg_price,
                'investment_amount': investment_amount
            }

            # 투자금액이 없으면 계산
            if not investment_amount and avg_price and quantity:
                result['investment_amount'] = avg_price * quantity

            return result

        return None

    def process_image(self, image) -> List[Dict]:
        """이미지 전체 처리 (OCR + 파싱)"""
        try:
            # OCR 실행
            ocr_results = self.extract_text_from_image(image)

            # 파싱
            stocks = self.parse_stock_info(ocr_results)

            return stocks

        except Exception as e:
            print(f"이미지 처리 오류: {e}")
            return []


# 전역 인스턴스
_ocr_instance = None

def get_ocr_instance():
    """싱글톤 OCR 인스턴스 반환"""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = StockImageOCR()
    return _ocr_instance
