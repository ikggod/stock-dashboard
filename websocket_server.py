"""
WebSocket 서버 - 브라우저에서 직접 연결하여 실시간 데이터 수신
"""
import asyncio
import json
import websockets
from typing import Set
from realtime_client import get_realtime_client
import threading
import time

# 연결된 클라이언트들
connected_clients: Set[websockets.WebSocketServerProtocol] = set()

# 종목별 구독자
subscribers = {}  # {stock_code: set(websockets)}


async def handle_client(websocket, path):
    """클라이언트 연결 처리"""
    connected_clients.add(websocket)
    subscribed_stocks = set()

    try:
        async for message in websocket:
            try:
                data = json.loads(message)

                if data.get('type') == 'subscribe':
                    stock_code = data.get('stock_code')
                    if stock_code:
                        subscribed_stocks.add(stock_code)
                        if stock_code not in subscribers:
                            subscribers[stock_code] = set()
                        subscribers[stock_code].add(websocket)
                        print(f"클라이언트가 {stock_code} 구독 시작")

                elif data.get('type') == 'unsubscribe':
                    stock_code = data.get('stock_code')
                    if stock_code and stock_code in subscribed_stocks:
                        subscribed_stocks.remove(stock_code)
                        if stock_code in subscribers:
                            subscribers[stock_code].discard(websocket)
                        print(f"클라이언트가 {stock_code} 구독 취소")

            except json.JSONDecodeError:
                print(f"잘못된 메시지 형식: {message}")

    except websockets.exceptions.ConnectionClosed:
        print("클라이언트 연결 종료")
    finally:
        # 연결 종료 시 구독 정리
        for stock_code in subscribed_stocks:
            if stock_code in subscribers:
                subscribers[stock_code].discard(websocket)
        connected_clients.discard(websocket)


async def broadcast_data():
    """실시간 데이터 브로드캐스트"""
    while True:
        try:
            ws_client = get_realtime_client()

            if ws_client and subscribers:
                # 각 종목별로 데이터 전송
                for stock_code, clients in list(subscribers.items()):
                    latest_data = ws_client.get_latest_data(stock_code)

                    if latest_data and clients:
                        message = json.dumps({
                            'stock_code': stock_code,
                            'price': latest_data['price'],
                            'time': latest_data['time'],
                            'change': latest_data['change'],
                            'change_rate': latest_data['change_rate']
                        })

                        # 구독 중인 클라이언트들에게 전송
                        disconnected = set()
                        for client in clients:
                            try:
                                await client.send(message)
                            except websockets.exceptions.ConnectionClosed:
                                disconnected.add(client)

                        # 연결 끊긴 클라이언트 제거
                        for client in disconnected:
                            clients.discard(client)

            await asyncio.sleep(0.1)  # 100ms마다 체크

        except Exception as e:
            print(f"브로드캐스트 오류: {e}")
            await asyncio.sleep(1)


async def main():
    """WebSocket 서버 시작"""
    # 서버 시작 (포트 8765)
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("WebSocket 서버 시작: ws://localhost:8765")

    # 브로드캐스트 태스크 시작
    broadcast_task = asyncio.create_task(broadcast_data())

    await asyncio.gather(server.wait_closed(), broadcast_task)


def start_websocket_server():
    """별도 스레드에서 WebSocket 서버 실행"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())


# 서버를 백그라운드 스레드로 실행
_server_thread = None


def init_websocket_server():
    """WebSocket 서버 초기화"""
    global _server_thread

    if _server_thread is None or not _server_thread.is_alive():
        _server_thread = threading.Thread(target=start_websocket_server, daemon=True)
        _server_thread.start()
        print("WebSocket 서버 스레드 시작됨")


if __name__ == "__main__":
    asyncio.run(main())
