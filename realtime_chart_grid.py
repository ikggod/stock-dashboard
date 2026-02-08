"""
실시간 차트 그리드 컴포넌트
모든 보유 종목을 한 화면에 실시간으로 표시
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, time, timedelta
from stock_data import StockDataCollector
from typing import Dict, List
import numpy as np
from scipy.signal import find_peaks


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

    def _create_chart(self, stock: Dict, current_price: float, change_info: Dict, intraday_data, height: int = 300, interval: str = '1d', enable_trendline: bool = False) -> go.Figure:
        """실제 주식 차트 생성 (일중 시세)"""
        fig = go.Figure()

        # interval에 따라 X축 포맷 결정
        if interval in ['1m', '5m']:
            xaxis_tickformat = '%H:%M'  # 시간 표시
        elif interval == '1d':
            xaxis_tickformat = '%m/%d'  # 월/일 표시
        elif interval == '1wk':
            xaxis_tickformat = '%y/%m/%d'  # 년/월/일 표시 (주봉)
        else:  # 월봉 등
            xaxis_tickformat = '%Y-%m'  # 년-월 표시

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
                increasing_line_color='#FF4444',  # 상승 테두리
                increasing_fillcolor='#FF4444',   # 상승 채우기
                decreasing_line_color='#4444FF',  # 하락 테두리
                decreasing_fillcolor='#4444FF',   # 하락 채우기
                line=dict(width=1),               # 테두리 두께
                name='가격',
                hovertemplate='<b>시가</b>: %{open:,.0f}원<br>' +
                              '<b>고가</b>: %{high:,.0f}원<br>' +
                              '<b>저가</b>: %{low:,.0f}원<br>' +
                              '<b>종가</b>: %{close:,.0f}원<br>' +
                              '<extra></extra>'
            ))

            # AI 추세선 예측 (enable_trendline=True일 때)
            if enable_trendline and len(df) >= 10:
                try:
                    low_prices = df['Low'].values
                    high_prices = df['High'].values
                    price_range = high_prices.max() - low_prices.min()
                    prominence = price_range * 0.05  # 전체 범위의 5%

                    # 시간을 숫자로 변환 (선형 회귀용)
                    time_numeric = np.arange(len(df))

                    # 미래 시간 계산
                    if interval == '1wk':
                        time_delta = timedelta(weeks=1)
                    elif interval == '1mo':
                        time_delta = timedelta(days=30)
                    elif interval == '1d':
                        time_delta = timedelta(days=1)
                    else:
                        time_delta = timedelta(minutes=1)

                    last_time = df[time_col].iloc[-1]
                    future_extension = int(len(df) * 0.2)
                    future_times = [last_time + time_delta * (i+1) for i in range(future_extension)]
                    extended_times = list(df[time_col]) + future_times
                    extended_time_numeric = np.arange(len(df) + future_extension)

                    # 1. 지지선 (저점 연결) - 파란색
                    trough_indices, _ = find_peaks(-low_prices, prominence=prominence, distance=5)
                    if len(trough_indices) >= 2:
                        trough_times = df[time_col].iloc[trough_indices]
                        trough_prices = low_prices[trough_indices]
                        trough_time_numeric = time_numeric[trough_indices]

                        # 선형 회귀
                        coefficients = np.polyfit(trough_time_numeric, trough_prices, 1)
                        slope, intercept = coefficients
                        support_line = slope * extended_time_numeric + intercept

                        # 지지선 그리기 (파란색)
                        fig.add_trace(go.Scatter(
                            x=extended_times,
                            y=support_line,
                            mode='lines',
                            line=dict(color='#4444FF', width=2, dash='solid'),
                            name='지지선 (매수)',
                            hovertemplate='지지: %{y:,.0f}원<extra></extra>',
                            showlegend=True
                        ))

                        # 저점 마커
                        fig.add_trace(go.Scatter(
                            x=trough_times,
                            y=trough_prices,
                            mode='markers',
                            marker=dict(symbol='circle', size=8, color='#4444FF', line=dict(color='white', width=2)),
                            name='저점',
                            hovertemplate='저점: %{y:,.0f}원<extra></extra>',
                            showlegend=False
                        ))

                    # 2. 저항선 (고점 연결) - 빨간색
                    peak_indices, _ = find_peaks(high_prices, prominence=prominence, distance=5)
                    if len(peak_indices) >= 2:
                        peak_times = df[time_col].iloc[peak_indices]
                        peak_prices = high_prices[peak_indices]
                        peak_time_numeric = time_numeric[peak_indices]

                        # 선형 회귀
                        coefficients = np.polyfit(peak_time_numeric, peak_prices, 1)
                        slope, intercept = coefficients
                        resistance_line = slope * extended_time_numeric + intercept

                        # 저항선 그리기 (빨간색)
                        fig.add_trace(go.Scatter(
                            x=extended_times,
                            y=resistance_line,
                            mode='lines',
                            line=dict(color='#FF4444', width=2, dash='solid'),
                            name='저항선 (매도)',
                            hovertemplate='저항: %{y:,.0f}원<extra></extra>',
                            showlegend=True
                        ))

                        # 고점 마커
                        fig.add_trace(go.Scatter(
                            x=peak_times,
                            y=peak_prices,
                            mode='markers',
                            marker=dict(symbol='circle', size=8, color='#FF4444', line=dict(color='white', width=2)),
                            name='고점',
                            hovertemplate='고점: %{y:,.0f}원<extra></extra>',
                            showlegend=False
                        ))
                except Exception as e:
                    # 추세선 그리기 실패 시 무시
                    pass
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
                tickformat=xaxis_tickformat,  # 동적 포맷
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
            st.session_state[timeframe_key] = '주봉'

        # 시장 상태 확인
        is_market_open = self._is_market_open()

        # 타임프레임 선택 (zoom out 가능하도록 충분한 기간)
        timeframe_options = {
            '1분': ('1m', '1d'),
            '5분': ('5m', '1d'),
            '일봉': ('1d', '2y'),      # 3mo → 2년
            '주봉': ('1wk', '5y'),     # 1y → 5년
            '월봉': ('1mo', 'max')     # 2y → 전체 기간
        }

        selected_timeframe = st.session_state[timeframe_key]
        interval, period = timeframe_options[selected_timeframe]
        chart_data = self._get_stock_data(stock_code, interval, period)

        # 현재가 결정 로직
        current_price = 0

        if is_market_open:
            # 장중: 실시간 현재가 우선
            current_price = self._get_current_price(stock_code)
            if current_price > 0:
                self._update_price_history(stock_code, current_price)

        # 현재가가 없거나 장 마감 시: 차트 데이터의 최신 종가 사용
        if current_price == 0 and chart_data is not None and not chart_data.empty:
            current_price = float(chart_data['Close'].iloc[-1])

        # 그래도 없으면: 히스토리에서 가져오기
        if current_price == 0 and history_key in st.session_state and len(st.session_state[history_key]) > 0:
            current_price = st.session_state[history_key][-1]['price']

        # 최종 fallback: 평단가 (이 경우만 손익 0)
        if current_price == 0:
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

                # 타임프레임 선택 UI
                timeframe_list = ['1분', '5분', '일봉', '주봉', '월봉']

                selected_timeframe = st.radio(
                    "기간",
                    options=timeframe_list,
                    index=timeframe_list.index(st.session_state[timeframe_key]),
                    horizontal=True,
                    key=f"radio_{stock_code}",
                    label_visibility="collapsed"
                )

                # 변경 감지 플래그
                timeframe_changed = st.session_state[timeframe_key] != selected_timeframe

                # 타임프레임이 변경되면 모든 모달 닫기
                if timeframe_changed:
                    # 모든 종목의 크게 보기 모달 닫기
                    for key in list(st.session_state.keys()):
                        if key.startswith('show_large_'):
                            st.session_state[key] = False
                    st.session_state[timeframe_key] = selected_timeframe
                    st.rerun()  # 새 데이터로 차트 갱신
                    return  # rerun 전 즉시 종료

                # AI 추세선 예측 체크박스
                trendline_key = f'trendline_{stock_code}'
                if trendline_key not in st.session_state:
                    st.session_state[trendline_key] = False

                enable_trendline = st.checkbox(
                    "🤖 AI 추세선 예측",
                    value=st.session_state[trendline_key],
                    key=f"trendline_check_{stock_code}",
                    help="과거 저점을 분석하여 미래 추세선을 예측합니다"
                )

                # 체크박스 상태 변경 시 모든 모달 닫기
                trendline_changed = st.session_state[trendline_key] != enable_trendline
                if trendline_changed:
                    for key in list(st.session_state.keys()):
                        if key.startswith('show_large_'):
                            st.session_state[key] = False
                    st.session_state[trendline_key] = enable_trendline
                    st.rerun()  # 즉시 리프레시
                    return  # rerun 전 즉시 종료

                st.session_state[trendline_key] = enable_trendline

                # 차트 (작게)
                fig_small = self._create_chart(stock, current_price, change_info, chart_data, height=250, interval=interval, enable_trendline=enable_trendline)
                st.plotly_chart(fig_small, width='stretch', key=f"chart_{stock_code}")

                # 크게 보기 버튼
                if st.button("🔍 크게 보기", key=f"expand_{stock_code}", width='stretch'):
                    st.session_state[f'show_large_{stock_code}'] = True

                # 추가 정보 (컴팩트하게)
                info_col1, info_col2, info_col3 = st.columns(3)
                with info_col1:
                    st.markdown(f"**보유**")
                    st.markdown(f"<span style='font-size: 1.1rem;'>{stock['quantity']:,}</span><span style='font-size: 0.85rem;'>주</span>", unsafe_allow_html=True)
                with info_col2:
                    st.markdown(f"**평단가**")
                    st.markdown(f"<span style='font-size: 1.1rem;'>{stock['avg_price']:,.0f}</span><span style='font-size: 0.85rem;'>원</span>", unsafe_allow_html=True)
                with info_col3:
                    profit_loss = (current_price - stock['avg_price']) * stock['quantity']
                    profit_color = '#FF4444' if profit_loss > 0 else '#4444FF' if profit_loss < 0 else '#666666'
                    st.markdown(f"**평가손익**")
                    st.markdown(f"<span style='font-size: 1.1rem; color: {profit_color};'>{profit_loss:+,.0f}</span><span style='font-size: 0.85rem;'>원</span>", unsafe_allow_html=True)

                # 마지막 업데이트 시간
                update_time = datetime.now().strftime('%H:%M:%S')
                st.caption(f"업데이트: {update_time} | {'실시간 수집 중' if is_market_open else '마지막 가격 표시'}")

            # 크게 보기 데이터 저장 (dialog는 나중에 호출)
            if st.session_state.get(f'show_large_{stock_code}', False):
                st.session_state[f'dialog_data_{stock_code}'] = {
                    'stock': stock,
                    'current_price': current_price,
                    'change_info': change_info,
                    'chart_data': chart_data,
                    'timeframe': selected_timeframe,
                    'is_market_open': is_market_open
                }
        else:
            # 가격 조회 실패
            st.warning(f"{stock_name} ({stock_code}): 현재가 조회 실패")

    @st.dialog("📈 차트 크게 보기", width="large")
    def _show_large_chart_dialog(self, stock: Dict, current_price: float, change_info: Dict, chart_data, timeframe: str, is_market_open: bool):
        """큰 화면 차트 다이얼로그"""
        stock_code = stock['code']
        stock_name = stock['name']

        # timeframe을 interval로 변환
        timeframe_to_interval = {
            '1분': '1m', '5분': '5m',
            '일봉': '1d', '주봉': '1wk', '월봉': '1mo'
        }
        interval = timeframe_to_interval.get(timeframe, '1d')

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

        # AI 추세선 예측 체크박스 (작은 화면 상태 유지)
        trendline_key = f'trendline_{stock_code}'
        current_trendline_state = st.session_state.get(trendline_key, False)

        enable_trendline_large = st.checkbox(
            "🤖 AI 추세선 예측",
            value=current_trendline_state,
            key=f"trendline_check_large_{stock_code}",
            help="과거 저점을 분석하여 미래 추세선을 예측합니다"
        )

        # 큰 화면에서 변경한 상태를 세션에 저장 (작은 화면과 동기화)
        st.session_state[trendline_key] = enable_trendline_large

        # 큰 차트
        fig_large = self._create_chart(stock, current_price, change_info, chart_data, height=600, interval=interval, enable_trendline=enable_trendline_large)
        st.plotly_chart(fig_large, width='stretch', key=f"chart_large_{stock_code}")

        # 상세 정보
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        with info_col1:
            st.markdown(f"**보유 수량**")
            st.markdown(f"<span style='font-size: 1.3rem;'>{stock['quantity']:,}</span><span style='font-size: 0.9rem;'>주</span>", unsafe_allow_html=True)
        with info_col2:
            st.markdown(f"**평균 단가**")
            st.markdown(f"<span style='font-size: 1.3rem;'>{stock['avg_price']:,.0f}</span><span style='font-size: 0.9rem;'>원</span>", unsafe_allow_html=True)
        with info_col3:
            profit_loss = (current_price - stock['avg_price']) * stock['quantity']
            profit_color = '#FF4444' if profit_loss > 0 else '#4444FF' if profit_loss < 0 else '#666666'
            st.markdown(f"**평가 손익**")
            st.markdown(f"<span style='font-size: 1.3rem; color: {profit_color};'>{profit_loss:+,.0f}</span><span style='font-size: 0.9rem;'>원</span>", unsafe_allow_html=True)
        with info_col4:
            profit_rate = change_info['percent']
            rate_color = '#FF4444' if profit_rate > 0 else '#4444FF' if profit_rate < 0 else '#666666'
            st.markdown(f"**수익률**")
            st.markdown(f"<span style='font-size: 1.3rem; color: {rate_color};'>{profit_rate:+.2f}</span><span style='font-size: 0.9rem;'>%</span>", unsafe_allow_html=True)

        # 닫기 버튼
        if st.button("닫기", width='stretch'):
            st.session_state[f'show_large_{stock_code}'] = False
            st.rerun()

    def render_grid(self, stocks: List[Dict], columns: int = 3):
        """
        전체 종목을 그리드로 렌더링

        Args:
            stocks: 종목 리스트 (이미 정렬된 상태)
            columns: 열 개수 (기본 3열)
        """
        # 1단계: 모든 종목의 UI 상태 변경 감지 (차트 렌더링 전)
        any_change = False
        for stock in stocks:
            stock_code = stock['code']
            timeframe_key = f'timeframe_{stock_code}'
            trendline_key = f'trendline_{stock_code}'

            # 초기화
            if timeframe_key not in st.session_state:
                st.session_state[timeframe_key] = '주봉'
            if trendline_key not in st.session_state:
                st.session_state[trendline_key] = False

        # 2단계: 실제 차트 렌더링
        # 그리드 레이아웃
        for i in range(0, len(stocks), columns):
            cols = st.columns(columns)

            for j, col in enumerate(cols):
                stock_idx = i + j
                if stock_idx < len(stocks):
                    with col:
                        self.render_stock_chart(stocks[stock_idx])
                        st.divider()

        # 3단계: 마지막에 열려있는 dialog만 호출 (깜빡임 방지)
        for stock in stocks:
            stock_code = stock['code']
            if st.session_state.get(f'show_large_{stock_code}', False):
                dialog_data = st.session_state.get(f'dialog_data_{stock_code}')
                if dialog_data:
                    self._show_large_chart_dialog(
                        dialog_data['stock'],
                        dialog_data['current_price'],
                        dialog_data['change_info'],
                        dialog_data['chart_data'],
                        dialog_data['timeframe'],
                        dialog_data['is_market_open']
                    )
