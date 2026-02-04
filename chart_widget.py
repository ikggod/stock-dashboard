"""
TradingView 차트 위젯을 Streamlit에 임베드하는 모듈

이 모듈은 TradingView의 차트 위젯을 Streamlit 애플리케이션에 통합하여
실시간 주식 차트를 표시하는 기능을 제공합니다.
"""

import streamlit.components.v1 as components
from typing import List, Optional


def convert_to_tradingview_symbol(korean_code: str) -> str:
    """
    한국 주식 종목코드를 TradingView 형식으로 변환

    Args:
        korean_code (str): 한국 주식 종목코드 (예: "005930")

    Returns:
        str: TradingView 형식의 심볼 (예: "KRX:005930")
    """
    # 종목코드가 이미 KRX: 접두사를 가지고 있는지 확인
    if korean_code.startswith("KRX:"):
        return korean_code

    # 종목코드 앞의 공백 제거 및 6자리 패딩
    code = korean_code.strip()

    # 숫자만 있는 경우 6자리로 패딩
    if code.isdigit():
        code = code.zfill(6)

    return f"KRX:{code}"


def render_tradingview_chart(
    symbol: str,
    interval: str = "D",
    width: str = "100%",
    height: int = 500,
    theme: str = "light",
    style: str = "1",
    locale: str = "kr",
    toolbar_bg: str = "#f1f3f6",
    enable_publishing: bool = False,
    allow_symbol_change: bool = True,
    container_id: Optional[str] = None
) -> None:
    """
    단일 종목의 TradingView 차트 위젯을 렌더링

    Args:
        symbol (str): TradingView 형식의 심볼 (예: "KRX:005930")
        interval (str): 차트 간격 (예: "D" - 일봉, "W" - 주봉, "M" - 월봉)
        width (str): 차트 너비 (예: "100%", "800px")
        height (int): 차트 높이 (픽셀)
        theme (str): 테마 ("light" 또는 "dark")
        style (str): 차트 스타일 ("1" - 캔들스틱, "2" - 바, "3" - 라인 등)
        locale (str): 언어 설정 ("kr" - 한국어)
        toolbar_bg (str): 툴바 배경색
        enable_publishing (bool): 차트 공유 기능 활성화
        allow_symbol_change (bool): 심볼 변경 허용
        container_id (str): 차트 컨테이너 고유 ID (다중 차트 표시시 필요)
    """
    # 한국 종목코드인 경우 변환
    if not symbol.startswith("KRX:") and symbol.replace(".", "").isdigit():
        symbol = convert_to_tradingview_symbol(symbol)

    # 컨테이너 ID가 없으면 심볼 기반으로 생성
    if container_id is None:
        container_id = f"tradingview_{symbol.replace(':', '_')}"

    # TradingView 위젯 HTML 생성
    tradingview_html = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container" style="width: {width}; height: {height}px;">
        <div id="{container_id}" style="width: 100%; height: 100%;"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
            "width": "{width}",
            "height": {height},
            "symbol": "{symbol}",
            "interval": "{interval}",
            "timezone": "Asia/Seoul",
            "theme": "{theme}",
            "style": "{style}",
            "locale": "{locale}",
            "toolbar_bg": "{toolbar_bg}",
            "enable_publishing": {str(enable_publishing).lower()},
            "allow_symbol_change": {str(allow_symbol_change).lower()},
            "container_id": "{container_id}",
            "hide_side_toolbar": false,
            "studies": [
                "STD;SMA"
            ],
            "show_popup_button": true,
            "popup_width": "1000",
            "popup_height": "650"
        }});
        </script>
    </div>
    <!-- TradingView Widget END -->
    """

    # Streamlit에 HTML 렌더링
    components.html(tradingview_html, height=height + 10, scrolling=False)


def render_multiple_charts(
    symbols: List[str],
    interval: str = "D",
    columns: int = 2,
    height: int = 400,
    theme: str = "light",
    style: str = "1"
) -> None:
    """
    다중 종목 차트를 동시에 표시

    Args:
        symbols (List[str]): 종목코드 리스트
        interval (str): 차트 간격
        columns (int): 열 개수 (한 행에 표시할 차트 수)
        height (int): 각 차트의 높이
        theme (str): 테마
        style (str): 차트 스타일
    """
    import streamlit as st

    if not symbols:
        st.warning("표시할 종목이 없습니다.")
        return

    # 종목코드를 TradingView 형식으로 변환
    tv_symbols = [convert_to_tradingview_symbol(s) for s in symbols]

    # 컬럼으로 차트 배치
    for i in range(0, len(tv_symbols), columns):
        cols = st.columns(columns)

        for j in range(columns):
            idx = i + j
            if idx < len(tv_symbols):
                with cols[j]:
                    # 종목명 표시
                    st.markdown(f"**{tv_symbols[idx]}**")

                    # 고유 컨테이너 ID 생성
                    container_id = f"tradingview_chart_{idx}"

                    # 차트 렌더링
                    render_tradingview_chart(
                        symbol=tv_symbols[idx],
                        interval=interval,
                        width="100%",
                        height=height,
                        theme=theme,
                        style=style,
                        container_id=container_id
                    )


def render_mini_chart(
    symbol: str,
    width: str = "100%",
    height: int = 200,
    theme: str = "light"
) -> None:
    """
    간단한 미니 차트 위젯 렌더링 (더 가벼운 버전)

    Args:
        symbol (str): TradingView 형식의 심볼
        width (str): 차트 너비
        height (int): 차트 높이
        theme (str): 테마
    """
    # 한국 종목코드인 경우 변환
    if not symbol.startswith("KRX:") and symbol.replace(".", "").isdigit():
        symbol = convert_to_tradingview_symbol(symbol)

    container_id = f"tradingview_mini_{symbol.replace(':', '_')}"

    # TradingView 미니 차트 HTML
    mini_chart_html = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container" style="width: {width}; height: {height}px;">
        <div id="{container_id}"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
        {{
            "symbol": "{symbol}",
            "width": "{width}",
            "height": "{height}",
            "locale": "kr",
            "dateRange": "1M",
            "colorTheme": "{theme}",
            "trendLineColor": "rgba(41, 98, 255, 1)",
            "underLineColor": "rgba(41, 98, 255, 0.3)",
            "underLineBottomColor": "rgba(41, 98, 255, 0)",
            "isTransparent": false,
            "autosize": false,
            "largeChartUrl": "",
            "container_id": "{container_id}"
        }}
        </script>
    </div>
    <!-- TradingView Widget END -->
    """

    components.html(mini_chart_html, height=height + 10, scrolling=False)


def render_ticker_tape(
    symbols: Optional[List[str]] = None,
    theme: str = "light",
    show_symbol_logo: bool = True
) -> None:
    """
    TradingView 티커 테이프 위젯 렌더링 (상단에 흐르는 종목 정보)

    Args:
        symbols (List[str]): 표시할 종목 리스트 (None이면 기본 한국 주요 종목)
        theme (str): 테마
        show_symbol_logo (bool): 종목 로고 표시 여부
    """
    # 기본 한국 주요 종목
    if symbols is None:
        symbols = ["005930", "000660", "035420", "051910", "035720",
                   "006400", "005380", "068270", "207940", "005490"]

    # TradingView 형식으로 변환
    tv_symbols = [{"proName": convert_to_tradingview_symbol(s), "title": s}
                  for s in symbols]

    # JSON 문자열로 변환
    import json
    symbols_json = json.dumps(tv_symbols)

    ticker_tape_html = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
        {{
            "symbols": {symbols_json},
            "showSymbolLogo": {str(show_symbol_logo).lower()},
            "colorTheme": "{theme}",
            "isTransparent": false,
            "displayMode": "adaptive",
            "locale": "kr"
        }}
        </script>
    </div>
    <!-- TradingView Widget END -->
    """

    components.html(ticker_tape_html, height=80, scrolling=False)


# 사용 예시
if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(layout="wide", page_title="TradingView 차트 예시")

    st.title("TradingView 차트 위젯 예시")

    # 티커 테이프
    st.subheader("실시간 주요 종목 현황")
    render_ticker_tape()

    st.markdown("---")

    # 단일 차트
    st.subheader("삼성전자 차트")
    render_tradingview_chart("005930", interval="D", height=500)

    st.markdown("---")

    # 다중 차트
    st.subheader("주요 종목 차트")
    render_multiple_charts(
        symbols=["005930", "000660", "035420", "051910"],
        columns=2,
        height=400
    )

    st.markdown("---")

    # 미니 차트
    st.subheader("미니 차트")
    cols = st.columns(3)
    with cols[0]:
        render_mini_chart("005930")
    with cols[1]:
        render_mini_chart("000660")
    with cols[2]:
        render_mini_chart("035420")
