"""
실시간 차트 Custom Component
브라우저에서 직접 WebSocket 연결하여 깜빡임 없는 실시간 업데이트
"""
import os
import streamlit.components.v1 as components

# 개발 모드 확인
_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "realtime_chart",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("realtime_chart", path=build_dir)


def realtime_chart(
    stock_code,
    stock_name,
    avg_price,
    initial_data=None,
    websocket_url=None,
    height=400,
    key=None
):
    """
    실시간 차트 컴포넌트

    Args:
        stock_code: 종목 코드
        stock_name: 종목명
        avg_price: 평균 매수가
        initial_data: 초기 차트 데이터 (리스트)
        websocket_url: WebSocket URL (없으면 REST API만 사용)
        height: 차트 높이
        key: 컴포넌트 키
    """
    component_value = _component_func(
        stock_code=stock_code,
        stock_name=stock_name,
        avg_price=avg_price,
        initial_data=initial_data or [],
        websocket_url=websocket_url,
        height=height,
        key=key,
        default=None
    )

    return component_value
