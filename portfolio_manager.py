import json
import os
from typing import List, Dict, Optional
from datetime import datetime

class PortfolioManager:
    """포트폴리오 데이터를 관리하는 클래스"""

    def __init__(self, file_path: str = "portfolio.json"):
        self.file_path = file_path
        self.portfolio = self.load_portfolio()

    def load_portfolio(self) -> Dict:
        """포트폴리오 데이터 로드"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"포트폴리오 로드 오류: {e}")
                return {"stocks": [], "last_updated": None}
        return {"stocks": [], "last_updated": None}

    def save_portfolio(self) -> bool:
        """포트폴리오 데이터 저장"""
        try:
            self.portfolio["last_updated"] = datetime.now().isoformat()
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.portfolio, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"포트폴리오 저장 오류: {e}")
            return False

    def add_stock(self, stock_name: str, stock_code: str,
                  avg_price: float, quantity: int,
                  investment_amount: float) -> bool:
        """종목 추가"""
        stock_data = {
            "name": stock_name,
            "code": stock_code,
            "avg_price": avg_price,
            "quantity": quantity,
            "investment_amount": investment_amount,
            "added_date": datetime.now().isoformat()
        }

        # 중복 체크
        for stock in self.portfolio["stocks"]:
            if stock["code"] == stock_code:
                print(f"종목 코드 {stock_code}는 이미 존재합니다.")
                return False

        self.portfolio["stocks"].append(stock_data)
        return self.save_portfolio()

    def update_stock(self, stock_code: str, **kwargs) -> bool:
        """종목 정보 수정"""
        for stock in self.portfolio["stocks"]:
            if stock["code"] == stock_code:
                for key, value in kwargs.items():
                    if key in stock:
                        stock[key] = value
                stock["updated_date"] = datetime.now().isoformat()
                return self.save_portfolio()
        return False

    def delete_stock(self, stock_code: str) -> bool:
        """종목 삭제"""
        original_length = len(self.portfolio["stocks"])
        self.portfolio["stocks"] = [
            stock for stock in self.portfolio["stocks"]
            if stock["code"] != stock_code
        ]

        if len(self.portfolio["stocks"]) < original_length:
            return self.save_portfolio()
        return False

    def get_stock(self, stock_code: str) -> Optional[Dict]:
        """특정 종목 정보 조회"""
        for stock in self.portfolio["stocks"]:
            if stock["code"] == stock_code:
                return stock
        return None

    def get_all_stocks(self) -> List[Dict]:
        """모든 종목 조회"""
        return self.portfolio["stocks"]

    def get_total_investment(self) -> float:
        """총 투자금액 계산"""
        return sum(stock["investment_amount"] for stock in self.portfolio["stocks"])

    def clear_portfolio(self) -> bool:
        """전체 포트폴리오 초기화"""
        self.portfolio = {"stocks": [], "last_updated": None}
        return self.save_portfolio()
