from typing import Dict, List, Optional

class PortfolioCalculator:
    """포트폴리오 수익률 및 통계 계산 클래스"""

    @staticmethod
    def calculate_profit_loss(investment_amount: float, current_value: float) -> float:
        """평가손익 계산"""
        return current_value - investment_amount

    @staticmethod
    def calculate_return_rate(investment_amount: float, current_value: float) -> float:
        """수익률 계산 (%)"""
        if investment_amount == 0:
            return 0.0
        return ((current_value - investment_amount) / investment_amount) * 100

    @staticmethod
    def calculate_stock_value(quantity: int, current_price: float) -> float:
        """현재 평가금액 계산"""
        return quantity * current_price

    @staticmethod
    def calculate_portfolio_summary(stocks: List[Dict], current_prices: Dict[str, float]) -> Dict:
        """포트폴리오 전체 요약 계산"""
        total_investment = 0
        total_current_value = 0

        stock_details = []

        for stock in stocks:
            stock_code = stock["code"]
            investment = stock["investment_amount"]
            quantity = stock["quantity"]
            avg_price = stock["avg_price"]

            # 현재가 조회
            current_price = current_prices.get(stock_code, 0)

            # 현재 평가금액
            current_value = PortfolioCalculator.calculate_stock_value(quantity, current_price)

            # 손익
            profit_loss = PortfolioCalculator.calculate_profit_loss(investment, current_value)

            # 수익률
            return_rate = PortfolioCalculator.calculate_return_rate(investment, current_value)

            stock_details.append({
                "name": stock["name"],
                "code": stock_code,
                "quantity": quantity,
                "avg_price": avg_price,
                "current_price": current_price,
                "investment_amount": investment,
                "current_value": current_value,
                "profit_loss": profit_loss,
                "return_rate": return_rate
            })

            total_investment += investment
            total_current_value += current_value

        # 전체 포트폴리오 손익 및 수익률
        total_profit_loss = PortfolioCalculator.calculate_profit_loss(total_investment, total_current_value)
        total_return_rate = PortfolioCalculator.calculate_return_rate(total_investment, total_current_value)

        return {
            "total_investment": total_investment,
            "total_current_value": total_current_value,
            "total_profit_loss": total_profit_loss,
            "total_return_rate": total_return_rate,
            "stock_details": stock_details
        }

    @staticmethod
    def format_currency(amount: float) -> str:
        """금액 포맷팅 (원화)"""
        return f"{amount:,.0f}원"

    @staticmethod
    def format_percentage(rate: float) -> str:
        """퍼센트 포맷팅"""
        return f"{rate:+.2f}%"
