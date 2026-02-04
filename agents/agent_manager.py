"""
Agent Manager
에이전트들을 관리하고 실행하는 매니저
"""

import asyncio
from typing import Dict, List, Optional, Any
from .architecture_agent import ArchitectureAnalysisAgent
from .chart_research_agent import ChartResearchAgent
from .streaming_agent import DataStreamingAgent
from .ui_design_agent import UIDesignAgent
from .kis_api_agent import KISAPIAnalysisAgent


class AgentManager:
    """에이전트 매니저 - 모든 에이전트를 관리"""

    def __init__(self):
        self.agents = {
            'architecture': ArchitectureAnalysisAgent(),
            'chart_research': ChartResearchAgent(),
            'streaming': DataStreamingAgent(),
            'ui_design': UIDesignAgent(),
            'kis_api': KISAPIAnalysisAgent()
        }

    def list_agents(self) -> List[Dict[str, Any]]:
        """등록된 모든 에이전트 목록 반환"""
        return [agent.get_info() for agent in self.agents.values()]

    def get_agent(self, agent_name: str):
        """특정 에이전트 가져오기"""
        return self.agents.get(agent_name)

    async def run_agent(self, agent_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """특정 에이전트 실행"""
        agent = self.get_agent(agent_name)
        if agent:
            return await agent.run(context)
        return {'error': f'Agent {agent_name} not found'}

    async def run_all_agents(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """모든 에이전트를 병렬로 실행"""
        tasks = [
            agent.run(context) for agent in self.agents.values()
        ]
        results = await asyncio.gather(*tasks)

        return {
            agent_name: result
            for agent_name, result in zip(self.agents.keys(), results)
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """모든 에이전트의 상태 반환"""
        return {
            agent_name: {
                'name': agent.name,
                'description': agent.description,
                'last_run': agent.last_run.isoformat() if agent.last_run else None,
                'run_count': agent.run_count
            }
            for agent_name, agent in self.agents.items()
        }

    def print_agent_summary(self):
        """에이전트 요약 출력"""
        print("\n=== 등록된 에이전트 목록 ===\n")
        for idx, (key, agent) in enumerate(self.agents.items(), 1):
            print(f"{idx}. [{key}] {agent.name}")
            print(f"   설명: {agent.description}")
            print(f"   실행 횟수: {agent.run_count}")
            if agent.last_run:
                print(f"   마지막 실행: {agent.last_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
