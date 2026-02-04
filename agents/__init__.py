"""
Stock Dashboard Agent System
실시간 차트 구현을 위한 전문 에이전트들
"""

from .architecture_agent import ArchitectureAnalysisAgent
from .chart_research_agent import ChartResearchAgent
from .streaming_agent import DataStreamingAgent
from .ui_design_agent import UIDesignAgent
from .kis_api_agent import KISAPIAnalysisAgent

__all__ = [
    'ArchitectureAnalysisAgent',
    'ChartResearchAgent',
    'DataStreamingAgent',
    'UIDesignAgent',
    'KISAPIAnalysisAgent'
]

__version__ = '1.0.0'
