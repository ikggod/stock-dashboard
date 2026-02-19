"""
키움증권 OpenAPI 서버
PyQt5 + 키움 OpenAPI → WebSocket으로 실시간 데이터 브로드캐스트
"""
import sys
import asyncio
import json
from collections import defaultdict
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEventLoop
import websockets
import threading


class KiwoomAPI:
    """키움증권 OpenAPI 래퍼"""

    def __init__(self):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.connected = False

        # 실시간 데이터 저장
        self.realtime_data = defaultdict(dict)

        # 이벤트 연결
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.ocx.OnReceiveRealData.connect(self._on_receive_real_data)
        self.ocx.OnReceiveMsg.connect(self._on_receive_msg)

        # WebSocket 클라이언트 리스트
        self.ws_clients = set()

    def login(self):
        """로그인"""
        ret = self.ocx.dynamicCall("CommConnect()")
        if ret == 0:
            print("로그인 요청 성공")
        else:
            print(f"로그인 요청 실패: {ret}")

    def _on_event_connect(self, err_code):
        """로그인 이벤트"""
        if err_code == 0:
            print("[OK] 키움증권 로그인 성공")
            self.connected = True
        else:
            print(f"[ERROR] 로그인 실패: {err_code}")
            self.connected = False

    def _on_receive_tr_data(self, screen_no, rqname, trcode, recordname, prev_next):
        """TR 데이터 수신"""
        print(f"TR 데이터 수신: {rqname}")

    def _on_receive_real_data(self, code, real_type, real_data):
        """실시간 데이터 수신"""
        if real_type == "주식체결":
            # 현재가 데이터 파싱
            current_price = self._get_comm_real_data(code, 10)  # 현재가
            change = self._get_comm_real_data(code, 11)  # 전일대비
            change_rate = self._get_comm_real_data(code, 12)  # 등락률
            volume = self._get_comm_real_data(code, 13)  # 거래량
            time = self._get_comm_real_data(code, 20)  # 체결시간

            # 데이터 저장
            self.realtime_data[code] = {
                'code': code,
                'price': abs(int(current_price)),
                'change': int(change),
                'change_rate': float(change_rate),
                'volume': int(volume),
                'time': time
            }

            # WebSocket으로 브로드캐스트
            asyncio.run(self._broadcast_data(code, self.realtime_data[code]))

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신"""
        print(f"메시지: {msg}")

    def _get_comm_real_data(self, code, fid):
        """실시간 데이터 조회"""
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return data.strip()

    def set_real_reg(self, screen_no, code_list, fid_list, opt_type):
        """실시간 등록"""
        ret = self.ocx.dynamicCall(
            "SetRealReg(QString, QString, QString, QString)",
            screen_no,
            code_list,
            fid_list,
            opt_type
        )
        if ret == 0:
            print(f"[OK] 실시간 등록 성공: {code_list}")
        else:
            print(f"[ERROR] 실시간 등록 실패: {ret}")

    async def _broadcast_data(self, code, data):
        """WebSocket으로 데이터 브로드캐스트"""
        if self.ws_clients:
            message = json.dumps(data)
            disconnected = set()

            for ws in self.ws_clients:
                try:
                    await ws.send(message)
                except:
                    disconnected.add(ws)

            # 끊긴 클라이언트 제거
            self.ws_clients -= disconnected


# 전역 키움 API 인스턴스
kiwoom = None


async def websocket_handler(websocket, path):
    """WebSocket 연결 핸들러"""
    global kiwoom

    kiwoom.ws_clients.add(websocket)
    print(f"[OK] WebSocket 클라이언트 연결: {len(kiwoom.ws_clients)}명")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)

                if data.get('type') == 'subscribe':
                    # 실시간 등록
                    stock_codes = data.get('stock_codes', [])
                    code_list = ";".join(stock_codes)

                    # FID: 10=현재가, 11=전일대비, 12=등락률, 13=거래량, 20=체결시간
                    fid_list = "10;11;12;13;20"

                    kiwoom.set_real_reg("1000", code_list, fid_list, "0")
                    print(f"📡 실시간 등록: {stock_codes}")

            except json.JSONDecodeError:
                print(f"잘못된 메시지: {message}")

    except websockets.exceptions.ConnectionClosed:
        print("[INFO] WebSocket 클라이언트 연결 종료")
    finally:
        kiwoom.ws_clients.discard(websocket)


async def start_websocket_server():
    """WebSocket 서버 시작"""
    async with websockets.serve(websocket_handler, "localhost", 9999):
        print("[OK] WebSocket 서버 시작: ws://localhost:9999")
        await asyncio.Future()  # 무한 대기


def run_websocket_server():
    """별도 스레드에서 WebSocket 서버 실행"""
    asyncio.run(start_websocket_server())


def main():
    """메인 함수"""
    global kiwoom

    # QApplication 생성
    app = QApplication(sys.argv)

    # 키움 API 초기화
    kiwoom = KiwoomAPI()

    # 로그인
    kiwoom.login()

    # WebSocket 서버 시작 (별도 스레드)
    ws_thread = threading.Thread(target=run_websocket_server, daemon=True)
    ws_thread.start()

    # Qt 이벤트 루프 실행
    print("[OK] 키움 서버 실행 중...")
    print("   - 로그인 창이 뜨면 로그인하세요")
    print("   - WebSocket: ws://localhost:9999")
    print("   - 종료: Ctrl+C")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
