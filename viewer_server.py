"""
주식 포트폴리오 경량 뷰어 - FastAPI 백엔드
부모님용 대시보드 서버 (포트 8502)
- 가격 조회, 차트 데이터, 종목 검색만 담당
- 포트폴리오 데이터는 브라우저 localStorage에서 관리
"""

import json
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="주식 대시보드 뷰어")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 가격 캐시
_price_cache = {"data": None, "timestamp": 0, "key": ""}
CACHE_TTL = 10  # 초 (실시간 모드)


def fetch_price(code: str) -> dict:
    """네이버 금융에서 현재가 조회"""
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        el = soup.select_one(".no_today .blind")
        if not el:
            return {"code": code, "price": None, "error": "가격 요소를 찾을 수 없음"}
        price = int(el.text.strip().replace(",", ""))

        change_el = soup.select_one(".no_exday .blind")
        change = 0
        if change_el:
            try:
                change = int(change_el.text.strip().replace(",", ""))
            except ValueError:
                pass

        no_exday = soup.select_one(".no_exday")
        if no_exday:
            if "nv_down" in str(no_exday) or "dl_dnx" in str(no_exday.parent) or no_exday.select_one(".ico.down_sm"):
                change = -abs(change)

        return {"code": code, "price": price, "change": change}
    except Exception as e:
        return {"code": code, "price": None, "error": str(e)}


def fetch_all_prices(codes: list[str]) -> list[dict]:
    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_price, code): code for code in codes}
        for future in as_completed(futures):
            results.append(future.result())
    return results


@app.get("/")
async def index():
    html_path = STATIC_DIR / "viewer.html"
    if not html_path.exists():
        raise HTTPException(404, "viewer.html not found")
    return FileResponse(html_path, media_type="text/html")


@app.get("/api/prices")
async def api_prices(codes: str = ""):
    if not codes:
        return JSONResponse({})

    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return JSONResponse({})

    cache_key = ",".join(sorted(code_list))
    now = time.time()
    if _price_cache.get("key") == cache_key and _price_cache["data"] and (now - _price_cache["timestamp"]) < CACHE_TTL:
        return JSONResponse(_price_cache["data"])

    prices = fetch_all_prices(code_list)
    result = {p["code"]: p for p in prices}
    _price_cache["data"] = result
    _price_cache["timestamp"] = now
    _price_cache["key"] = cache_key
    return JSONResponse(result)


# 종목 리스트 (로컬 파일에서 로드)
STOCK_LIST_PATH = BASE_DIR / "stock_list.json"
_stock_list: list[dict] = []


def load_stock_list():
    """종목 리스트 로드 (서버 시작 시 1회)"""
    global _stock_list
    if STOCK_LIST_PATH.exists():
        with open(STOCK_LIST_PATH, "r", encoding="utf-8") as f:
            _stock_list = json.load(f)
        print(f"[종목 리스트] {len(_stock_list)}개 로드 완료")
    else:
        print("[경고] stock_list.json 없음 - 검색 불가")


def search_stocks_local(query: str) -> list[dict]:
    """로컬 종목 리스트에서 검색"""
    if not _stock_list:
        return []
    q = query.lower()
    results = []
    for s in _stock_list:
        if q in s["name"].lower() or q in s["code"]:
            results.append(s)
            if len(results) >= 15:
                break
    return results


@app.get("/api/search")
async def api_search(q: str = ""):
    if not q or len(q) < 1:
        return JSONResponse([])
    results = search_stocks_local(q)
    return JSONResponse(results)


@app.get("/api/chart/{code}")
async def api_chart(code: str):
    try:
        url = f"https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe=day&count=90&requestType=0"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        items = root.findall(".//item")
        candles = []
        for item in items:
            data = item.get("data", "").split("|")
            if len(data) >= 5:
                date_str = data[0]
                formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                candles.append({
                    "time": formatted,
                    "open": float(data[1]),
                    "high": float(data[2]),
                    "low": float(data[3]),
                    "close": float(data[4]),
                    "volume": int(data[5]) if len(data) > 5 else 0,
                })
        return JSONResponse(candles)
    except Exception as e:
        raise HTTPException(500, str(e))


def generate_stock_list():
    """네이버 금융에서 전체 종목 리스트 크롤링"""
    from bs4 import BeautifulSoup as BS
    all_stocks = []
    for sosok in [0, 1]:
        for page in range(1, 45):
            try:
                url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page={page}"
                r = requests.get(url, headers=HEADERS, timeout=10)
                found = False
                for a in BS(r.text, "html.parser").select("a"):
                    href = a.get("href", "")
                    if "main.naver?code=" in href:
                        code = href.split("code=")[1].split("&")[0]
                        name = a.text.strip()
                        if name and code:
                            all_stocks.append({"name": name, "code": code})
                            found = True
                if not found:
                    break
            except:
                continue
    if all_stocks:
        with open(STOCK_LIST_PATH, "w", encoding="utf-8") as f:
            json.dump(all_stocks, f, ensure_ascii=False)
        print(f"[종목 리스트] {len(all_stocks)}개 생성 완료")
    return all_stocks


def _refresh_stock_list():
    """백그라운드에서 최신 종목 목록 갱신"""
    import time
    generate_stock_list()
    load_stock_list()
    print("[종목 리스트] 최신 동기화 완료")


@app.on_event("startup")
async def startup_load_stocks():
    """서버 시작 시 초기화 - 기존 파일 로드 후 백그라운드 갱신"""
    import threading
    if STOCK_LIST_PATH.exists():
        load_stock_list()  # 일단 기존 파일로 빠르게 서비스 시작
    print("[종목 리스트] 백그라운드에서 최신 목록 동기화 중...")
    threading.Thread(target=_refresh_stock_list, daemon=True).start()


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8502))
    uvicorn.run(app, host="0.0.0.0", port=port)
