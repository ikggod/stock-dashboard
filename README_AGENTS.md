# Stock Dashboard Agents 🤖

실시간 차트 구현을 위한 전문 에이전트 시스템

## 개요

이 프로젝트는 5개의 전문 에이전트를 포함하고 있습니다. 각 에이전트는 실시간 주식 차트 구현의 특정 영역을 담당합니다.

## 설치된 에이전트

### 1. 🏗️ Architecture Analysis Agent
**역할**: 현재 코드베이스 아키텍처 분석
- 시스템 컴포넌트 파악
- 의존성 분석
- 데이터 흐름 분석
- 개선 권장사항 제공

### 2. 📊 Chart Research Agent
**역할**: 실시간 차트 라이브러리 연구
- 최적 차트 라이브러리 추천
- WebSocket vs Polling 비교
- 성능 벤치마크
- 구현 가이드 제공

### 3. 🌊 Data Streaming Agent
**역할**: 실시간 데이터 스트리밍 아키텍처 설계
- WebSocket 클라이언트 설계
- Rate Limiter 구현 계획
- 멀티 레이어 캐싱 전략
- 메시지 큐 및 버퍼링

### 4. 🎨 UI Design Agent
**역할**: 차트 UI/UX 설계
- 레이아웃 디자인
- 실시간 지표 설계
- 상호작용 기능 정의
- Streamlit 컴포넌트 추천

### 5. 🔌 KIS API Analysis Agent
**역할**: 한국투자증권 API 분석
- API 기능 조사
- WebSocket 지원 확인
- Rate Limit 분석
- 통합 전략 수립

## 사용법

### CLI를 통한 실행

```bash
# 모든 에이전트 목록 확인
python agents_cli.py list

# 특정 에이전트 실행
python agents_cli.py run architecture
python agents_cli.py run chart_research
python agents_cli.py run streaming
python agents_cli.py run ui_design
python agents_cli.py run kis_api

# 모든 에이전트 동시 실행
python agents_cli.py run-all

# 에이전트 상태 확인
python agents_cli.py status

# 도움말
python agents_cli.py help
```

### Python 코드에서 사용

```python
import asyncio
from agents.agent_manager import AgentManager

async def main():
    # 에이전트 매니저 초기화
    manager = AgentManager()

    # 특정 에이전트 실행
    result = await manager.run_agent('architecture')
    print(result)

    # 모든 에이전트 실행
    all_results = await manager.run_all_agents()
    print(all_results)

asyncio.run(main())
```

### Streamlit 앱에서 사용

```python
import streamlit as st
from agents.agent_manager import AgentManager
import asyncio

st.title("에이전트 대시보드")

manager = AgentManager()

# 사이드바에 에이전트 선택
agent_list = list(manager.agents.keys())
selected_agent = st.sidebar.selectbox("에이전트 선택", agent_list)

if st.sidebar.button("실행"):
    with st.spinner(f"{selected_agent} 실행 중..."):
        result = asyncio.run(manager.run_agent(selected_agent))

        if result.get('status') == 'success':
            st.success("분석 완료!")
            st.json(result)
        else:
            st.error(f"에러: {result.get('error')}")
```

## 결과 저장

에이전트 실행 결과는 자동으로 `agent_results/` 디렉토리에 JSON 형식으로 저장됩니다.

```
agent_results/
├── architecture_result.json
├── chart_research_result.json
├── streaming_result.json
├── ui_design_result.json
├── kis_api_result.json
└── all_agents_results.json
```

## 프로젝트 구조

```
stock-dashboard/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py              # 기본 에이전트 클래스
│   ├── architecture_agent.py      # 아키텍처 분석
│   ├── chart_research_agent.py    # 차트 연구
│   ├── streaming_agent.py         # 스트리밍 설계
│   ├── ui_design_agent.py         # UI 설계
│   ├── kis_api_agent.py          # KIS API 분석
│   └── agent_manager.py          # 에이전트 매니저
├── agents_cli.py                  # CLI 인터페이스
├── agent_results/                 # 결과 저장 폴더
└── README_AGENTS.md              # 이 파일
```

## 에이전트 확장

새로운 에이전트를 추가하려면:

1. `agents/` 폴더에 새 파일 생성 (예: `new_agent.py`)
2. `BaseAgent`를 상속받는 클래스 작성
3. `analyze()` 메서드 구현
4. `agents/__init__.py`에 추가
5. `agent_manager.py`의 `__init__`에 등록

예시:

```python
# agents/new_agent.py
from .base_agent import BaseAgent

class NewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="New Agent",
            description="새로운 에이전트 설명"
        )

    async def analyze(self, context=None):
        # 분석 로직
        return {
            'result': 'analysis result'
        }
```

## 요구사항

- Python 3.9+
- asyncio 지원

## 라이선스

MIT License

## 기여

개선 사항이나 버그 리포트는 이슈로 등록해주세요.

---

**제작**: Stock Dashboard Agent System v1.0.0
**최종 업데이트**: 2026-02-05
