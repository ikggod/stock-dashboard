"""
실시간 차트 그리드 컴포넌트
모든 보유 종목을 한 화면에 실시간으로 표시
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, time
from stock_data import StockDataCollector
from typing import Dict, List


class RealtimeChartGrid:
    """실시간 차트 그리드 관리"""

    def __init__(self, stock_collector: StockDataCollector):
        self.stock_collector = stock_collector

    def _is_market_open(self) -> bool:
        """주식 시장이 열려있는지 확인 (평일 9:00-15:30)"""
        now = datetime.now()

        # 주말 체크
        if now.weekday() >= 5:  # 5=토요일, 6=일요일
            return False

        # 시간 체크 (9:00 ~ 15:30)
        current_time = now.time()
        market_open = time(9, 0)
        market_close = time(15, 30)

        return market_open <= current_time <= market_close

    def _get_current_price(self, stock_code: str) -> float:
        """현재가 조회"""
        code_fixed = str(stock_code).zfill(6)
        price = self.stock_collector.get_current_price(code_fixed, method="auto")
        return price if price else 0

    def _get_stock_data(self, stock_code: str, interval: str = "1m", period: str = "1d"):
        """주식 시세 데이터 가져오기 (yfinance)

        Args:
            stock_code: 종목 코드
            interval: 간격 (1m, 5m, 30m, 1h, 1d, 1wk, 1mo)
            period: 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
        """
        import yfinance as yf

        try:
            # 한국 주식 티커 형식
            ticker = f"{stock_code}.KS"
            stock = yf.Ticker(ticker)

            # 데이터 가져오기
            df = stock.history(period=period, interval=interval)

            if df.empty:
                # KOSDAQ 시도
                ticker = f"{stock_code}.KQ"
                stock = yf.Ticker(ticker)
                df = stock.history(period=period, interval=interval)

            return df if not df.empty else None
        except:
            return None

    def _calculate_change(self, stock: Dict, current_price: float) -> Dict:
        """등락 계산"""
        if current_price <= 0:
            return {
                'amount': 0,
                'percent': 0,
                'color': 'gray'
            }

        avg_price = stock['avg_price']
        change_amount = current_price - avg_price
        change_percent = (change_amount / avg_price) * 100

        if change_percent > 0:
            color = '#FF4444'  # 빨간색 (상승)
        elif change_percent < 0:
            color = '#4444FF'  # 파란색 (하락)
        else:
            color = '#666666'  # 회색 (보합)

        return {
            'amount': change_amount,
            'percent': change_percent,
            'color': color
        }

    def _update_price_history(self, stock_code: str, current_price: float):
        """가격 히스토리 업데이트 (실시간 데이터만 쌓기)"""
        history_key = f'chart_history_{stock_code}'

        # 히스토리가 없으면 생성
        if history_key not in st.session_state:
            st.session_state[history_key] = []

        # 새 데이터 포인트 추가
        history = st.session_state[history_key]
        history.append({
            'time': datetime.now(),
            'price': current_price
        })

        # 최근 100개만 유지
        if len(history) > 100:
            st.session_state[history_key] = history[-100:]
        else:
            st.session_state[history_key] = history

    def _create_chart(self, stock: Dict, current_price: float, change_info: Dict, intraday_data, height: int = 300) -> go.Figure:
        """실제 주식 차트 생성 (일중 시세)"""
        fig = go.Figure()

        if intraday_data is not None and not intraday_data.empty:
            # 시세 데이터가 있으면 캔들스틱 차트
            df = intraday_data.reset_index()

            # 시간 컬럼 이름 확인 (Datetime 또는 Date)
            time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'

            fig.add_trace(go.Candlestick(
                x=df[time_col],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color='#FF4444',
                decreasing_line_color='#4444FF',
                name='가격'
            ))
        else:
            # 데이터가 없으면 현재가만 표시
            fig.add_trace(go.Scatter(
                x=[datetime.now()],
                y=[current_price],
                mode='markers',
                marker=dict(size=10, color=change_info['color']),
                name='현재가',
                hovertemplate='%{y:,.0f}원<extra></extra>'
            ))

        # 평균 매수가 라인 (점선)
        avg_price = stock['avg_price']
        fig.add_hline(
            y=avg_price,
            line_dash="dash",
            line_color="orange",
            line_width=1,
            annotation_text=f"평단: {avg_price:,.0f}원",
            annotation_position="right",
            annotation_font_size=10
        )

        # 레이아웃 설정 (실제 차트처럼)
        fig.update_layout(
            height=height,  # 동적 높이
            margin=dict(l=10, r=10, t=10, b=40),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.1)',
                showticklabels=True,
                tickformat='%H:%M',
                zeroline=False
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                zeroline=False,
                tickformat=',.0f',
                side='right'  # Y축을 오른쪽으로
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            hovermode='x',
            xaxis_rangeslider_visible=False  # 하단 슬라이더 제거
        )

        return fig

    def render_stock_chart(self, stock: Dict):
        """개별 종목 차트 렌더링"""
        stock_code = stock['code']
        stock_name = stock['name']
        history_key = f'chart_history_{stock_code}'

        # 타임프레임 선택
        timeframe_key = f'timeframe_{stock_code}'
        if timeframe_key not in st.session_state:
            st.session_state[timeframe_key] = '1분'

        # 시장 상태 확인
        is_market_open = self._is_market_open()

        # 현재가 조회 (시장 열려있을 때만)
        if is_market_open:
            current_price = self._get_current_price(stock_code)

            if current_price > 0:
                # 실시간 데이터 추가
                self._update_price_history(stock_code, current_price)
        else:
            # 시장 닫혔을 때: 마지막 가격 사용 또는 평단가
            if history_key in st.session_state and len(st.session_state[history_key]) > 0:
                current_price = st.session_state[history_key][-1]['price']
            else:
                current_price = stock['avg_price']

        if current_price > 0:
            # 등락 계산
            change_info = self._calculate_change(stock, current_price)

            # 컨테이너
            with st.container():
                # 헤더: 종목명 + 시장 상태
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**{stock_name}**")
                    market_status = "🟢 장중" if is_market_open else "🔴 장마감"
                    st.caption(f"{stock_code} | {market_status}")

                with col2:
                    # 현재가
                    st.markdown(
                        f"<div style='text-align: right; font-size: 1.2rem; font-weight: bold; color: {change_info['color']};'>"
                        f"{current_price:,.0f}원"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    # 등락
                    arrow = "▲" if change_info['percent'] > 0 else "▼" if change_info['percent'] < 0 else "-"
                    st.markdown(
                        f"<div style='text-align: right; font-size: 0.9rem; color: {change_info['color']};'>"
                        f"{arrow} {change_info['amount']:+,.0f} ({change_info['percent']:+.2f}%)"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # 타임프레임 선택
                timeframe_options = {
                    '1분': ('1m', '1d'),
                    '5분': ('5m', '1d'),
                    '30분': ('30m', '5d'),
                    '1시간': ('1h', '5d'),
                    '일봉': ('1d', '3mo'),
                    '주봉': ('1wk', '1y'),
                    '월봉': ('1mo', '2y')
                }

                selected_timeframe = st.radio(
                    "기간",
                    options=list(timeframe_options.keys()),
                    index=list(timeframe_options.keys()).index(st.session_state[timeframe_key]),
                    horizontal=True,
                    key=f"radio_{stock_code}",
                    label_visibility="collapsed"
                )
                st.session_state[timeframe_key] = selected_timeframe

                # 선택된 타임프레임으로 데이터 가져오기
                interval, period = timeframe_options[selected_timeframe]
                chart_data = self._get_stock_data(stock_code, interval, period)

                # 차트 (작게)
                fig_small = self._create_chart(stock, current_price, change_info, chart_data, height=250)
                st.plotly_chart(fig_small, use_container_width=True, key=f"chart_{stock_code}")

                # 크게 보기 버튼
                if st.button("🔍 크게 보기", key=f"expand_{stock_code}", use_container_width=True):
                    st.session_state[f'show_large_{stock_code}'] = True

                # 추가 정보
                info_col1, info_col2, info_col3 = st.columns(3)
                with info_col1:
                    st.metric("보유", f"{stock['quantity']}주", label_visibility="visible")
                with info_col2:
                    st.metric("평단가", f"{stock['avg_price']:,.0f}원", label_visibility="visible")
                with info_col3:
                    profit_loss = (current_price - stock['avg_price']) * stock['quantity']
                    st.metric("평가손익", f"{profit_loss:+,.0f}원", label_visibility="visible")

                # 마지막 업데이트 시간
                update_time = datetime.now().strftime('%H:%M:%S')
                st.caption(f"업데이트: {update_time} | {'실시간 수집 중' if is_market_open else '마지막 가격 표시'}")

            # 큰 화면 다이얼로그
            if st.session_state.get(f'show_large_{stock_code}', False):
                self._show_large_chart_dialog(stock, current_price, change_info, chart_data, selected_timeframe, is_market_open)
        else:
            # 가격 조회 실패
            st.warning(f"{stock_name} ({stock_code}): 현재가 조회 실패")

    @st.dialog("📈 차트 크게 보기", width="large")
    def _show_large_chart_dialog(self, stock: Dict, current_price: float, change_info: Dict, chart_data, timeframe: str, is_market_open: bool):
        """큰 화면 차트 다이얼로그"""
        stock_code = stock['code']
        stock_name = stock['name']

        # 헤더
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"## {stock_name} ({stock_code})")
            market_status = "🟢 장중" if is_market_open else "🔴 장마감"
            st.caption(f"{market_status} | {timeframe}")

        with col2:
            st.markdown(f"### {current_price:,.0f}원")

        with col3:
            arrow = "▲" if change_info['percent'] > 0 else "▼" if change_info['percent'] < 0 else "-"
            st.markdown(
                f"<div style='font-size: 1.5rem; color: {change_info['color']};'>"
                f"{arrow} {change_info['amount']:+,.0f} ({change_info['percent']:+.2f}%)"
                f"</div>",
                unsafe_allow_html=True
            )

        st.divider()

        # 큰 차트
        fig_large = self._create_chart(stock, current_price, change_info, chart_data, height=600)
        st.plotly_chart(fig_large, use_container_width=True, key=f"chart_large_{stock_code}")

        # 상세 정보
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        with info_col1:
            st.metric("보유 수량", f"{stock['quantity']}주")
        with info_col2:
            st.metric("평균 단가", f"{stock['avg_price']:,.0f}원")
        with info_col3:
            profit_loss = (current_price - stock['avg_price']) * stock['quantity']
            st.metric("평가 손익", f"{profit_loss:+,.0f}원")
        with info_col4:
            profit_rate = change_info['percent']
            st.metric("수익률", f"{profit_rate:+.2f}%")

        # 닫기 버튼
        if st.button("닫기", use_container_width=True):
            st.session_state[f'show_large_{stock_code}'] = False
            st.rerun()

    def render_grid(self, stocks: List[Dict], columns: int = 3):
        """
        전체 종목을 그리드로 렌더링

        Args:
            stocks: 종목 리스트 (이미 정렬된 상태)
            columns: 열 개수 (기본 3열)
        """
        # 그리드 레이아웃
        for i in range(0, len(stocks), columns):
            cols = st.columns(columns)

            for j, col in enumerate(cols):
                stock_idx = i + j
                if stock_idx < len(stocks):
                    with col:
                        self.render_stock_chart(stocks[stock_idx])
                        st.divider()
