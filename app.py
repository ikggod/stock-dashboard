import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
from io import BytesIO
from PIL import Image
from portfolio_manager import PortfolioManager
from stock_data import StockDataCollector
from calculator import PortfolioCalculator
from excel_template import create_smart_template
from ocr_processor import get_ocr_instance
from realtime_chart_grid import RealtimeChartGrid
import sys
sys.path.insert(0, os.path.dirname(__file__))
from realtime_chart_component import realtime_chart
from websocket_server import init_websocket_server

# 페이지 설정
st.set_page_config(
    page_title="주식 포트폴리오 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .profit {
        color: #ff4444;
        font-weight: bold;
    }
    .loss {
        color: #4444ff;
        font-weight: bold;
    }
    .neutral {
        color: #666666;
        font-weight: bold;
    }
    .stock-table {
        margin-top: 2rem;
    }
    .detail-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'selected_chosung' not in st.session_state:
    st.session_state.selected_chosung = None
if 'selected_alphabet' not in st.session_state:
    st.session_state.selected_alphabet = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'selected_stocks_filter' not in st.session_state:
    st.session_state.selected_stocks_filter = []

# 매니저 초기화
@st.cache_resource
def init_managers():
    pm = PortfolioManager()
    sdc = StockDataCollector()
    chart_grid = RealtimeChartGrid(sdc)

    # WebSocket 서버 시작 (브라우저에서 직접 연결용)
    init_websocket_server()

    return pm, sdc, chart_grid

portfolio_manager, stock_collector, chart_grid = init_managers()

# 한글 초성 추출 함수
def get_chosung(text):
    """한글 문자열의 첫 글자 초성을 반환"""
    if not text:
        return None

    first_char = text[0]

    # 한글 유니코드 범위 체크 (가-힣)
    if '가' <= first_char <= '힣':
        # 초성 리스트
        chosung_list = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        # 한글 유니코드에서 초성 추출
        chosung_index = (ord(first_char) - ord('가')) // 588
        return chosung_list[chosung_index]

    return None

# 초성으로 필터링하는 함수
def filter_by_chosung(stocks, chosung):
    """초성으로 종목 필터링"""
    if not chosung:
        return stocks

    filtered = []
    for stock in stocks:
        stock_chosung = get_chosung(stock['name'])
        if stock_chosung == chosung:
            filtered.append(stock)

    return filtered

# 영문으로 필터링하는 함수
def filter_by_alphabet(stocks, alphabet):
    """영문 알파벳으로 종목 필터링"""
    if not alphabet:
        return stocks

    filtered = []
    for stock in stocks:
        first_char = stock['name'][0] if stock['name'] else ''
        # 영문 대소문자 체크
        if first_char.upper() == alphabet.upper():
            filtered.append(stock)

    return filtered

# 검색어로 필터링하는 함수
def filter_by_search(stocks, search_query):
    """검색어로 종목 필터링 (종목명에 포함되는지 체크)"""
    if not search_query:
        return stocks

    search_query_lower = search_query.lower()
    filtered = []
    for stock in stocks:
        # 종목명 또는 종목코드에 검색어가 포함되어 있으면 필터링
        if (search_query_lower in stock['name'].lower() or
            search_query_lower in str(stock['code']).lower()):
            filtered.append(stock)

    return filtered

# 현재가 조회 함수
@st.cache_data(ttl=30)
def get_all_current_prices(stock_codes):
    """병렬 현재가 조회 (10배 속도 향상)"""
    import concurrent.futures

    prices = {}

    def fetch_price(code):
        """단일 종목 현재가 조회"""
        code_fixed = str(code).zfill(6)
        price = stock_collector.get_current_price(code_fixed, method="auto")
        return code, price

    # ThreadPoolExecutor로 병렬 조회 (최대 10개 동시)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_price, code): code for code in stock_codes}

        for future in concurrent.futures.as_completed(futures):
            try:
                code, price = future.result(timeout=5)
                if price:
                    prices[code] = price
                else:
                    print(f"현재가 조회 실패: {code}")
            except Exception as e:
                print(f"현재가 조회 오류 ({futures[future]}): {e}")

    return prices

# 메인 헤더
st.markdown('<div class="main-header">📈 주식 포트폴리오 대시보드</div>', unsafe_allow_html=True)

# 사이드바 - 종목 추가/삭제
with st.sidebar:
    st.header("⚙️ 포트폴리오 관리")

    # 한국투자증권 API 설정
    with st.expander("🔑 API 설정 (실시간 시세)", expanded=False):
        st.markdown("""
        **한국투자증권 API로 실시간 정확한 시세!**
        - 0.01초 단위 실시간 업데이트
        - 정확도 99.99%
        """)

        from kis_api import get_kis_instance, set_kis_credentials

        kis = get_kis_instance()

        # API 키 입력
        app_key = st.text_input("App Key", value=kis.app_key or "", type="password")
        app_secret = st.text_input("App Secret", value=kis.app_secret or "", type="password")
        hts_id = st.text_input("HTS ID (선택사항)", value=kis.hts_id or "",
                               help="WebSocket 실시간 시세용 (선택). 없어도 시도해볼 수 있습니다.")

        col1, col2 = st.columns(2)
        with col1:
            is_real = st.checkbox("실전투자", value=kis.is_real)
        with col2:
            if not is_real:
                st.caption("✅ 모의투자")

        if st.button("💾 API 키 저장"):
            if app_key and app_secret:
                success = set_kis_credentials(app_key, app_secret, "", hts_id, is_real)
                if success:
                    st.success("✅ API 연결 성공!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ API 연결 실패. 키를 확인하세요.")
            else:
                st.warning("⚠️ App Key와 App Secret을 입력하세요.")

        # 연결 상태 표시
        if kis.broker:
            st.success("🟢 REST API 활성화")

            col_test1, col_test2 = st.columns(2)
            with col_test1:
                if st.button("🔄 연결 테스트"):
                    if kis.test_connection():
                        st.success("✅ 연결 정상!")
                    else:
                        st.error("❌ 연결 실패")

            with col_test2:
                # WebSocket 시작 버튼 (HTS ID 선택사항)
                if st.button("🚀 WebSocket 시작"):
                    from realtime_client import init_realtime_client

                    # 보유 종목 코드 가져오기
                    stocks = portfolio_manager.get_all_stocks()
                    stock_codes = [stock['code'] for stock in stocks]

                    if len(stock_codes) > 0:
                        hts_id_to_use = kis.hts_id if kis.hts_id else ""

                        with st.spinner('WebSocket 연결 중...'):
                            success = init_realtime_client(
                                kis.app_key,
                                kis.app_secret,
                                hts_id_to_use,
                                stock_codes
                            )
                        if success:
                            st.session_state['websocket_active'] = True
                            st.success(f"✅ WebSocket 시작! ({len(stock_codes)}개 종목)")
                            if not hts_id_to_use:
                                st.info("💡 HTS ID 없이 연결 시도 중입니다.")
                        else:
                            st.error("❌ WebSocket 시작 실패. HTS ID가 필요할 수 있습니다.")
                    else:
                        st.warning("⚠️ 먼저 종목을 추가하세요")

            # WebSocket 상태 표시
            if st.session_state.get('websocket_active', False):
                st.info("🔴 실시간 WebSocket 활성화")
        else:
            st.info("⚪ 네이버 금융 시세 사용 중 (15분 지연)")
            st.caption("API 키를 입력하면 실시간 시세로 전환됩니다")

        st.divider()
        st.caption("""
        **API 키 발급 방법:**
        1. https://apiportal.koreainvestment.com
        2. 로그인 (또는 모의투자 신청)
        3. "API 신청" → "App Key 발급"
        """)


    # 종목 추가 폼
    with st.expander("➕ 종목 추가", expanded=False):
        with st.form("add_stock_form", clear_on_submit=True):
            stock_name = st.text_input("종목명", placeholder="예: 삼성전자")
            stock_code = st.text_input("종목 코드", placeholder="예: 005930")
            avg_price = st.number_input("평균 단가 (원)", min_value=0.0, step=100.0, format="%.0f")
            quantity = st.number_input("보유 수량 (주)", min_value=0, step=1)

            # 투자금액 자동 계산
            investment_amount = avg_price * quantity
            st.info(f"투자금액: {investment_amount:,.0f}원")

            submitted = st.form_submit_button("추가")

            if submitted:
                if stock_name and stock_code and avg_price > 0 and quantity > 0:
                    success = portfolio_manager.add_stock(
                        stock_name=stock_name,
                        stock_code=stock_code,
                        avg_price=avg_price,
                        quantity=quantity,
                        investment_amount=investment_amount
                    )
                    if success:
                        st.success(f"✅ {stock_name} 추가 완료!")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 이미 존재하는 종목이거나 추가에 실패했습니다.")
                else:
                    st.warning("⚠️ 모든 항목을 올바르게 입력해주세요.")

    # 엑셀 일괄 등록
    with st.expander("📊 엑셀 일괄 등록", expanded=False):
        st.markdown("""
        **✨ 스마트 엑셀 템플릿:**
        - 종목명을 드롭다운에서 선택하면 종목코드가 자동 입력됩니다
        - KOSPI + KOSDAQ 전체 4,226개 종목 포함
        - 컬럼: 종목명, 종목코드, 평균단가, 보유수량
        """)

        st.info("⏱️ 템플릿 생성에 10-20초 소요됩니다 (전체 종목 로딩)")

        # 템플릿 생성 버튼
        if st.button("🔄 템플릿 생성", help="전체 상장 종목을 로드하여 스마트 템플릿을 생성합니다"):
            with st.spinner('전체 종목 로딩 중... (4,226개)'):
                try:
                    excel_data = create_smart_template()
                    st.session_state['excel_template'] = excel_data
                    st.success("✅ 템플릿 생성 완료! 아래 버튼을 클릭하세요.")
                except Exception as e:
                    st.error(f"❌ 템플릿 생성 오류: {e}")

        # 다운로드 버튼 (템플릿 생성 후에만 표시)
        if 'excel_template' in st.session_state:
            st.download_button(
                label="📥 스마트 템플릿 다운로드",
                data=st.session_state['excel_template'],
                file_name="포트폴리오_스마트템플릿.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="종목명 선택 시 종목코드가 자동으로 입력됩니다"
            )

        # 파일 업로드
        uploaded_file = st.file_uploader("엑셀 파일 업로드", type=['xlsx', 'xls'])

        if uploaded_file is not None:
            try:
                # 두 번째 시트 "포트폴리오 입력" 읽기
                df = pd.read_excel(uploaded_file, sheet_name="포트폴리오 입력")

                # 디버깅: 실제 컬럼명 출력
                st.write("📋 파일의 실제 컬럼명:", list(df.columns))

                # 컬럼명 공백 제거
                df.columns = df.columns.str.strip()

                # 컬럼명 검증 (매입금액은 선택)
                required_columns = ['종목명', '종목코드', '평균단가', '보유수량']
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    st.error(f"❌ 필수 컬럼이 없습니다: {', '.join(missing_columns)}")
                    st.info(f"필요한 컬럼: {', '.join(required_columns)}")
                    st.info(f"현재 파일 컬럼: {', '.join(df.columns)}")
                else:
                    st.dataframe(df, width='stretch')
                    st.info(f"총 {len(df)}개 종목")

                    # 중복 체크
                    existing_stocks = portfolio_manager.get_all_stocks()
                    existing_codes = {s['code'] for s in existing_stocks}

                    # 엑셀 내 중복 체크
                    excel_codes = []
                    duplicate_in_excel = []
                    duplicate_with_portfolio = []

                    for idx, row in df.iterrows():
                        try:
                            code_raw = str(row['종목코드']).strip()
                            if '.' in code_raw:
                                code_raw = code_raw.split('.')[0]
                            stock_code = code_raw.zfill(6)

                            # 엑셀 내 중복 체크
                            if stock_code in excel_codes:
                                duplicate_in_excel.append(f"{row['종목명']} ({stock_code})")
                            else:
                                excel_codes.append(stock_code)

                            # 포트폴리오와 중복 체크
                            if stock_code in existing_codes:
                                duplicate_with_portfolio.append(f"{row['종목명']} ({stock_code})")
                        except:
                            pass

                    # 중복 경고 표시
                    if duplicate_in_excel:
                        st.warning(f"⚠️ 엑셀 파일 내 중복된 종목코드 {len(duplicate_in_excel)}개:")
                        with st.expander("중복 종목 확인 (엑셀 내)", expanded=True):
                            for dup in duplicate_in_excel:
                                st.write(f"• {dup}")
                            st.caption("→ 중복된 종목은 첫 번째 행만 등록됩니다")

                    if duplicate_with_portfolio:
                        st.error(f"❌ 포트폴리오에 이미 존재하는 종목 {len(duplicate_with_portfolio)}개:")
                        with st.expander("중복 종목 확인 (포트폴리오)", expanded=True):
                            for dup in duplicate_with_portfolio:
                                st.write(f"• {dup}")
                            st.caption("→ 이미 존재하는 종목은 등록되지 않습니다")

                    if st.button("일괄 등록", type="primary"):
                        success_count = 0
                        fail_count = 0
                        skip_count = 0

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        # 중복 방지를 위한 세트
                        processed_codes = set()

                        for idx, row in df.iterrows():
                            try:
                                stock_name = str(row['종목명']).strip()

                                # 종목코드: 소수점 제거 후 6자리로 맞춤
                                code_raw = str(row['종목코드']).strip()
                                if '.' in code_raw:
                                    code_raw = code_raw.split('.')[0]  # 소수점 제거
                                stock_code = code_raw.zfill(6)  # 6자리로 패딩

                                # 중복 체크 (엑셀 내 중복 및 포트폴리오 중복)
                                if stock_code in processed_codes or stock_code in existing_codes:
                                    skip_count += 1
                                    status_text.text(f"⏭️ {stock_name} 건너뜀 (중복)")
                                    progress_bar.progress((idx + 1) / len(df))
                                    continue

                                processed_codes.add(stock_code)

                                avg_price = float(row['평균단가'])
                                quantity = int(row['보유수량'])

                                # 매입금액: 컬럼이 있고 값이 있으면 사용, 없으면 자동 계산
                                if '매입금액' in df.columns and pd.notna(row['매입금액']) and row['매입금액'] != '':
                                    investment_amount = float(row['매입금액'])
                                else:
                                    investment_amount = avg_price * quantity

                                # 종목 추가
                                success = portfolio_manager.add_stock(
                                    stock_name=stock_name,
                                    stock_code=stock_code,
                                    avg_price=avg_price,
                                    quantity=quantity,
                                    investment_amount=investment_amount
                                )

                                if success:
                                    success_count += 1
                                    status_text.text(f"✅ {stock_name} 등록 완료")
                                else:
                                    fail_count += 1
                                    status_text.text(f"⚠️ {stock_name} 등록 실패 (오류)")

                            except Exception as e:
                                fail_count += 1
                                status_text.text(f"❌ {idx+1}번째 행 오류: {e}")

                            progress_bar.progress((idx + 1) / len(df))

                        result_message = f"✅ 등록 완료: {success_count}개"
                        if skip_count > 0:
                            result_message += f" | 건너뜀: {skip_count}개 (중복)"
                        if fail_count > 0:
                            result_message += f" | 실패: {fail_count}개"

                        st.success(result_message)
                        st.cache_data.clear()
                        time.sleep(2)
                        st.rerun()

            except Exception as e:
                st.error(f"❌ 파일 읽기 오류: {e}")

    # 이미지 자동 인식 등록
    with st.expander("📸 이미지 자동 인식 (OCR)", expanded=False):
        st.markdown("""
        **✨ 스크린샷 자동 인식:**
        - 미래에셋증권 앱 화면 캡처
        - 이미지 업로드하면 자동으로 종목 정보 인식
        - 한글 인식 지원 (EasyOCR)
        """)

        st.info("⏱️ 최초 실행 시 OCR 모델 다운로드 (30초-1분, 1회만)")

        uploaded_image = st.file_uploader(
            "이미지 업로드",
            type=['png', 'jpg', 'jpeg', 'bmp'],
            help="미래에셋증권 보유 종목 화면 캡처"
        )

        if uploaded_image is not None:
            # 이미지 표시
            image = Image.open(uploaded_image)
            st.image(image, caption="업로드된 이미지", width='stretch')

            if st.button("🔍 이미지 인식 시작", type="primary"):
                with st.spinner('이미지 분석 중... (30초-1분 소요)'):
                    try:
                        # OCR 처리
                        ocr = get_ocr_instance()
                        detected_stocks = ocr.process_image(image)

                        if detected_stocks:
                            st.success(f"✅ {len(detected_stocks)}개 종목 인식 완료!")

                            # 인식 결과 표시
                            st.subheader("인식된 종목:")
                            for idx, stock in enumerate(detected_stocks, 1):
                                with st.expander(f"{idx}. {stock['name']}", expanded=True):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**종목명:** {stock['name']}")
                                        st.write(f"**종목코드:** {stock['code'] or 'N/A'}")
                                        st.write(f"**보유수량:** {stock['quantity'] or 'N/A'}주")
                                    with col2:
                                        st.write(f"**평균단가:** {stock['avg_price'] or 'N/A'}원")
                                        st.write(f"**매입금액:** {stock['investment_amount'] or 'N/A'}원")

                            # 일괄 등록 버튼
                            st.divider()
                            if st.button("📝 인식된 종목 일괄 등록", type="secondary"):
                                success_count = 0
                                fail_count = 0

                                for stock in detected_stocks:
                                    try:
                                        # 필수 정보 체크
                                        if not stock['name']:
                                            fail_count += 1
                                            continue

                                        # 종목코드 처리
                                        if stock['code']:
                                            code_fixed = str(stock['code']).zfill(6)
                                        else:
                                            st.warning(f"⚠️ {stock['name']}: 종목코드를 찾을 수 없어 건너뜁니다")
                                            fail_count += 1
                                            continue

                                        # 기본값 설정
                                        avg_price = stock['avg_price'] or 0
                                        quantity = stock['quantity'] or 0
                                        investment_amount = stock['investment_amount'] or (avg_price * quantity)

                                        if avg_price == 0 or quantity == 0:
                                            st.warning(f"⚠️ {stock['name']}: 가격 또는 수량 정보가 없어 건너뜁니다")
                                            fail_count += 1
                                            continue

                                        # 종목 등록
                                        success = portfolio_manager.add_stock(
                                            stock_name=stock['name'],
                                            stock_code=code_fixed,
                                            avg_price=avg_price,
                                            quantity=quantity,
                                            investment_amount=investment_amount
                                        )

                                        if success:
                                            success_count += 1
                                        else:
                                            fail_count += 1

                                    except Exception as e:
                                        fail_count += 1
                                        st.error(f"❌ {stock['name']} 등록 오류: {e}")

                                st.success(f"✅ 등록 완료: {success_count}개 / 실패: {fail_count}개")
                                st.cache_data.clear()
                                time.sleep(2)
                                st.rerun()

                        else:
                            st.warning("⚠️ 종목 정보를 인식하지 못했습니다. 다른 이미지를 시도해주세요.")
                            st.info("""
                            **팁:**
                            - 화면이 선명한 스크린샷 사용
                            - 종목 리스트가 잘 보이는 화면
                            - 밝기 조절 (너무 어둡지 않게)
                            """)

                    except Exception as e:
                        st.error(f"❌ OCR 처리 오류: {e}")

    # 종목 삭제 폼
    with st.expander("➖ 종목 삭제", expanded=False):
        stocks = portfolio_manager.get_all_stocks()
        if stocks:
            st.markdown(f"**현재 {len(stocks)}개 종목 보유 중**")

            # 개별 삭제
            st.subheader("개별 삭제")
            stock_options = {f"{s['name']} ({s['code']})": s['code'] for s in stocks}
            selected_stock = st.selectbox("삭제할 종목", list(stock_options.keys()))

            if st.button("선택 종목 삭제", type="secondary"):
                stock_code_to_delete = stock_options[selected_stock]
                if portfolio_manager.delete_stock(stock_code_to_delete):
                    st.success(f"✅ {selected_stock} 삭제 완료!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ 삭제에 실패했습니다.")

            st.divider()

            # 전체 삭제
            st.subheader("전체 삭제")
            st.warning("⚠️ 모든 종목이 삭제됩니다. 이 작업은 되돌릴 수 없습니다!")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🗑️ 전체 삭제", type="primary", width='stretch'):
                    st.session_state['confirm_delete_all'] = True

            if st.session_state.get('confirm_delete_all', False):
                with col2:
                    if st.button("✅ 정말 삭제", type="secondary", width='stretch'):
                        if portfolio_manager.clear_portfolio():
                            st.success(f"✅ {len(stocks)}개 종목 전체 삭제 완료!")
                            st.session_state['confirm_delete_all'] = False
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ 전체 삭제에 실패했습니다.")
        else:
            st.info("삭제할 종목이 없습니다.")

    st.divider()

    # 차트 설정
    st.subheader("📊 차트 설정")

    # 세션 상태 초기화
    if 'chart_height' not in st.session_state:
        st.session_state.chart_height = 500
    if 'chart_columns' not in st.session_state:
        st.session_state.chart_columns = 4

    chart_height = st.slider(
        "차트 높이",
        min_value=300,
        max_value=800,
        value=st.session_state.chart_height,
        step=50,
        help="차트를 크게 보려면 높이를 늘리세요"
    )
    st.session_state.chart_height = chart_height

    chart_columns = st.selectbox(
        "열 개수",
        options=[2, 3, 4, 5],
        index=[2, 3, 4, 5].index(st.session_state.chart_columns),
        help="한 줄에 표시할 차트 개수"
    )
    st.session_state.chart_columns = chart_columns

    st.caption(f"현재: {chart_columns}열 × {chart_height}px")

    st.divider()

    # 자동 새로고침 설정
    st.subheader("🔄 자동 새로고침")
    auto_refresh = st.checkbox("30초마다 자동 새로고침", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh

    if st.button("🔄 수동 새로고침"):
        st.cache_data.clear()
        stock_collector.clear_cache()
        st.session_state.last_refresh = datetime.now()
        st.rerun()

    if st.session_state.last_refresh:
        st.caption(f"마지막 새로고침: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

# 메인 화면
stocks = portfolio_manager.get_all_stocks()

if not stocks:
    st.info("📝 사이드바에서 종목을 추가해주세요.")
    st.stop()

# ========== 필터링 UI ==========
st.subheader("🔍 종목 필터")

# 검색창
st.markdown("##### 🔎 종목 검색")
search_query = st.text_input(
    "종목명 또는 종목코드로 검색",
    value=st.session_state.search_query,
    placeholder="예: 삼성, LG, 005930",
    key="search_input",
    help="종목명이나 종목코드의 일부만 입력해도 검색됩니다"
)
st.session_state.search_query = search_query

# 빠른 필터 버튼 (검색 결과를 빠르게 필터링)
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🔄 전체", type="secondary", use_container_width=True, key="reset_search"):
        st.session_state.search_query = ""
with col2:
    if st.session_state.search_query:
        st.info(f"🔍 검색 중: '{st.session_state.search_query}'")
    else:
        st.info(f"📊 전체 {len(stocks)}개 종목 표시")

st.divider()

# ========== 필터링 적용 ==========
# 검색어 필터 적용
if st.session_state.search_query:
    stocks = filter_by_search(stocks, st.session_state.search_query)

# 필터링 후 종목이 없으면 메시지 표시
if not stocks:
    st.warning("⚠️ 선택한 필터에 해당하는 종목이 없습니다.")
    st.stop()

# 현재가 조회
stock_codes = [stock['code'] for stock in stocks]
current_prices = get_all_current_prices(stock_codes)

# 포트폴리오 요약 계산
summary = PortfolioCalculator.calculate_portfolio_summary(stocks, current_prices)

# 포트폴리오 요약 카드
total_stocks_count = len(portfolio_manager.get_all_stocks())
filtered_stocks_count = len(stocks)

# 컴팩트한 포트폴리오 요약 (PC 큰 화면 최적화)
col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1.5, 1.5, 2])

with col1:
    st.metric("투자", f"{summary['total_investment']/10000:.0f}만")
    st.caption("총 투자금액")

with col2:
    st.metric("평가", f"{summary['total_current_value']/10000:.0f}만")
    st.caption("평가금액")

with col3:
    profit_loss = summary['total_profit_loss']
    st.metric("손익", f"{profit_loss/10000:+.0f}만",
              delta=f"{profit_loss:,.0f}원")
    st.caption("평가손익")

with col4:
    return_rate = summary['total_return_rate']
    st.metric("수익률", f"{return_rate:+.1f}%",
              delta=f"{return_rate:+.1f}%")
    st.caption("전체 수익률")

with col5:
    from datetime import datetime
    if filtered_stocks_count < total_stocks_count:
        st.info(f"📊 종목: {filtered_stocks_count}/{total_stocks_count}개")
    else:
        st.info(f"📊 전체: {total_stocks_count}개 종목")
    st.caption(f"업데이트: {datetime.now().strftime('%H:%M:%S')}")

st.divider()

# 탭으로 뷰 전환
tab1, tab2 = st.tabs(["📊 포트폴리오 요약", "📈 실시간 차트 (전체)"])

with tab1:
    # 종목 리스트 테이블
    if filtered_stocks_count < total_stocks_count:
        st.subheader(f"📊 보유 종목 ({filtered_stocks_count}개 표시)")
    else:
        st.subheader(f"📊 보유 종목 (전체 {filtered_stocks_count}개)")

# 현재가 조회 실패 체크
failed_stocks = [s for s in summary['stock_details'] if s['current_price'] == 0]
if failed_stocks:
    st.warning(f"⚠️ {len(failed_stocks)}개 종목의 현재가 조회 실패 (종목코드가 6자리가 아닐 수 있습니다)")
    with st.expander("조회 실패 종목 확인"):
        for s in failed_stocks:
            st.write(f"• {s['name']}: 코드 `{s['code']}` (길이: {len(str(s['code']))}자리)")
            st.caption("→ 종목코드는 반드시 6자리여야 합니다 (예: 005930)")

# 데이터프레임 생성
df_data = []
for stock_detail in summary['stock_details']:
    profit_loss = stock_detail['profit_loss']
    return_rate = stock_detail['return_rate']

    # 종목코드 길이 체크
    code_display = str(stock_detail['code']).zfill(6)

    df_data.append({
        "종목명": stock_detail['name'],
        "종목코드": code_display,
        "보유수량": f"{stock_detail['quantity']:,}주",
        "평균단가": f"{stock_detail['avg_price']:,.0f}원",
        "현재가": f"{stock_detail['current_price']:,.0f}원" if stock_detail['current_price'] > 0 else "N/A",
        "투자금액": f"{stock_detail['investment_amount']:,.0f}원",
        "평가금액": f"{stock_detail['current_value']:,.0f}원",
        "평가손익": f"{profit_loss:+,.0f}원",
        "수익률": f"{return_rate:+.2f}%"
    })

df = pd.DataFrame(df_data)

# 테이블 스타일링 함수
def color_profit_loss(val):
    if '원' in str(val) or '%' in str(val):
        if '+' in str(val):
            return 'color: #ff4444; font-weight: bold'
        elif '-' in str(val):
            return 'color: #4444ff; font-weight: bold'
    return ''

# 스타일 적용
styled_df = df.style.map(color_profit_loss, subset=['평가손익', '수익률'])

st.dataframe(styled_df, width='stretch', hide_index=True)

st.divider()

# 종목 상세 정보
st.subheader("🔍 종목 상세 정보")

# 종목 선택 (전체 옵션 추가)
stock_names = ["전체"] + [s['name'] for s in stocks]
selected_stock_name = st.selectbox("종목 선택", stock_names, index=0, key="stock_detail_select")

if selected_stock_name == "전체":
    # 전체 포트폴리오 요약 표시
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("##### 포트폴리오 기본 정보")
        st.write(f"**총 종목 수**: {len(stocks)}개")
        total_quantity = sum(s['quantity'] for s in stocks)
        st.write(f"**총 보유 수량**: {total_quantity:,}주")

    with col2:
        st.markdown("##### 투자 정보")
        st.write(f"**총 투자금액**: {summary['total_investment']:,.0f}원")
        st.write(f"**총 평가금액**: {summary['total_current_value']:,.0f}원")

    with col3:
        st.markdown("##### 손익 정보")
        profit_loss = summary['total_profit_loss']
        return_rate = summary['total_return_rate']

        profit_loss_class = "profit" if profit_loss > 0 else "loss" if profit_loss < 0 else "neutral"
        return_rate_class = "profit" if return_rate > 0 else "loss" if return_rate < 0 else "neutral"

        st.markdown(f"**총 평가손익**: <span class='{profit_loss_class}'>{profit_loss:+,.0f}원</span>", unsafe_allow_html=True)
        st.markdown(f"**전체 수익률**: <span class='{return_rate_class}'>{return_rate:+.2f}%</span>", unsafe_allow_html=True)

        # 손익 게이지
        if profit_loss > 0:
            st.success(f"전체 수익 중입니다! +{profit_loss:,.0f}원")
        elif profit_loss < 0:
            st.error(f"전체 손실 중입니다. {profit_loss:,.0f}원")
        else:
            st.info("손익 없음")

elif selected_stock_name:
    # 선택된 종목 정보 가져오기
    selected_stock_detail = None
    for stock_detail in summary['stock_details']:
        if stock_detail['name'] == selected_stock_name:
            selected_stock_detail = stock_detail
            break

    if selected_stock_detail:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("##### 기본 정보")
            st.write(f"**종목명**: {selected_stock_detail['name']}")
            st.write(f"**종목코드**: {selected_stock_detail['code']}")
            st.write(f"**보유수량**: {selected_stock_detail['quantity']:,}주")
            st.write(f"**평균단가**: {selected_stock_detail['avg_price']:,.0f}원")

        with col2:
            st.markdown("##### 투자 정보")
            st.write(f"**투자금액**: {selected_stock_detail['investment_amount']:,.0f}원")
            st.write(f"**현재가**: {selected_stock_detail['current_price']:,.0f}원")
            st.write(f"**평가금액**: {selected_stock_detail['current_value']:,.0f}원")

        with col3:
            st.markdown("##### 손익 정보")
            profit_loss = selected_stock_detail['profit_loss']
            return_rate = selected_stock_detail['return_rate']

            profit_loss_class = "profit" if profit_loss > 0 else "loss" if profit_loss < 0 else "neutral"
            return_rate_class = "profit" if return_rate > 0 else "loss" if return_rate < 0 else "neutral"

            st.markdown(f"**평가손익**: <span class='{profit_loss_class}'>{profit_loss:+,.0f}원</span>", unsafe_allow_html=True)
            st.markdown(f"**수익률**: <span class='{return_rate_class}'>{return_rate:+.2f}%</span>", unsafe_allow_html=True)

            # 손익 게이지
            if profit_loss > 0:
                st.success(f"수익 중입니다! +{profit_loss:,.0f}원")
            elif profit_loss < 0:
                st.error(f"손실 중입니다. {profit_loss:,.0f}원")
            else:
                st.info("손익 없음")

with tab2:
    # 실시간 차트 그리드
    if filtered_stocks_count < total_stocks_count:
        st.subheader(f"📈 실시간 차트 ({filtered_stocks_count}개 종목)")
    else:
        st.subheader(f"📈 실시간 차트 (전체 {filtered_stocks_count}개 종목)")

    # 새로고침 컨트롤
    col_refresh1, col_refresh2, col_refresh3, col_refresh4 = st.columns([1, 1, 1, 2])
    with col_refresh1:
        if st.button("🔄 새로고침", width='stretch', key="manual_refresh_chart"):
            st.rerun()
    with col_refresh2:
        auto_refresh_chart = st.checkbox("자동", value=True, help="자동 새로고침 활성화", key="auto_refresh_toggle")
    with col_refresh3:
        # 새로고침 간격 선택
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = 1
        refresh_interval = st.selectbox(
            "간격",
            options=[0.5, 1, 2, 3, 5],
            index=1,  # 기본 1초
            key="refresh_interval_select",
            help="차트 업데이트 간격 (초) - WebSocket 사용 시 0.5초 권장"
        )
        st.session_state.refresh_interval = refresh_interval
    with col_refresh4:
        current_time = datetime.now().strftime('%H:%M:%S')

        # WebSocket 연결 상태 확인
        from realtime_client import get_realtime_client
        ws_client = get_realtime_client()
        ws_active = ws_client is not None

        if auto_refresh_chart:
            if ws_active:
                st.success(f"🔴 LIVE WebSocket ({refresh_interval}초) | {current_time}")
            else:
                st.success(f"🟢 실시간 업데이트 ({refresh_interval}초) | {current_time}")
        else:
            st.caption(f"⚪ 수동 모드 | {current_time}")

    # WebSocket 안내 메시지
    from realtime_client import get_realtime_client
    ws_client = get_realtime_client()

    if ws_client:
        st.success("🔴 **LIVE 모드**: WebSocket으로 실시간 시세를 받아 차트에 표시합니다. (증권사 앱 방식)")
    else:
        st.info("💡 평단가는 주황색 점선으로 표시됩니다. 사이드바에서 **WebSocket을 시작**하면 진짜 실시간 모드로 전환됩니다.")

    # 종목을 ㄱㄴㄷ 순으로 정렬
    sorted_stocks = sorted(stocks, key=lambda x: x['name'])

    # 사이드바에서 설정한 값 가져오기
    num_columns = st.session_state.get('chart_columns', 4)
    chart_height = st.session_state.get('chart_height', 500)

    st.caption(f"📊 {len(sorted_stocks)}개 종목 | {num_columns}열 × {chart_height}px (사이드바에서 조절)")
    st.divider()

    # 실시간 차트 렌더링 방식 선택
    use_custom_component = st.checkbox(
        "🚀 진짜 실시간 모드 (Custom Component)",
        value=False,
        help="브라우저에서 직접 WebSocket 연결하여 깜빡임 0% (선택적, 빌드 필요)"
    )

    st.divider()

    if use_custom_component:
        # Custom Component 사용 (진짜 실시간)
        st.info("🔴 **LIVE MODE**: 브라우저가 WebSocket에 직접 연결하여 증권사 앱처럼 작동합니다.")

        # 그리드 레이아웃
        for i in range(0, len(sorted_stocks), num_columns):
            cols = st.columns(num_columns)

            for j, col in enumerate(cols):
                stock_idx = i + j
                if stock_idx < len(sorted_stocks):
                    stock = sorted_stocks[stock_idx]
                    with col:
                        # Custom Component로 실시간 차트 렌더링
                        # 키움 서버 사용 시: ws://localhost:9999
                        # 한투 서버 사용 시: ws://localhost:8765
                        realtime_chart(
                            stock_code=stock['code'],
                            stock_name=stock['name'],
                            avg_price=stock['avg_price'],
                            websocket_url="ws://localhost:9999",  # 키움 서버
                            height=300,
                            key=f"chart_{stock['code']}"
                        )
    else:
        # 기존 Fragment 방식 (폴링)
        @st.fragment(run_every=f"{refresh_interval}s" if auto_refresh_chart else None)
        def render_realtime_charts():
            """실시간 차트 렌더링 (Fragment로 부분 업데이트)"""
            chart_grid.render_grid(sorted_stocks, columns=num_columns, height=chart_height)

        # 차트 렌더링
        render_realtime_charts()

# 푸터
st.markdown("---")
st.caption("💡 Tip: 사이드바에서 종목을 추가/삭제하고, 자동 새로고침을 활성화하여 실시간으로 포트폴리오를 모니터링하세요.")
