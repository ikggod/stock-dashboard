"""
Base Agent Class
모든 에이전트의 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import json


class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.last_run = None
        self.run_count = 0
        self.results_history = []

    @abstractmethod
    async def analyze(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        에이전트의 주요 분석 작업을 수행합니다.

        Args:
            context: 분석에 필요한 컨텍스트 정보

        Returns:
            분석 결과를 담은 딕셔너리
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """에이전트 정보를 반환합니다."""
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'run_count': self.run_count,
            'status': 'active'
        }

    async def run(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        에이전트를 실행합니다.

        Args:
            context: 실행 컨텍스트

        Returns:
            실행 결과
        """
        self.last_run = datetime.now()
        self.run_count += 1

        try:
            result = await self.analyze(context)
            result['status'] = 'success'
            result['timestamp'] = datetime.now().isoformat()
            result['agent'] = self.name

            # 결과 히스토리 저장 (최근 10개만)
            self.results_history.append(result)
            if len(self.results_history) > 10:
                self.results_history = self.results_history[-10:]

            return result
        except Exception as e:
            error_result = {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'agent': self.name
            }
            self.results_history.append(error_result)
            return error_result

    def save_result(self, filepath: str, result: Dict[str, Any]):
        """결과를 파일로 저장합니다."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """마지막 실행 결과를 반환합니다."""
        return self.results_history[-1] if self.results_history else None
