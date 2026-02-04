"""
Agents CLI
에이전트를 명령줄에서 실행하는 인터페이스
사용법: python agents_cli.py [command] [agent_name]
"""

import asyncio
import sys
import json
import io
from agents.agent_manager import AgentManager

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def print_help():
    """도움말 출력"""
    print("""
=== Stock Dashboard Agents CLI ===

사용법:
  python agents_cli.py list                    - 모든 에이전트 목록
  python agents_cli.py run [agent_name]        - 특정 에이전트 실행
  python agents_cli.py run-all                 - 모든 에이전트 실행
  python agents_cli.py status                  - 에이전트 상태 확인
  python agents_cli.py help                    - 도움말

에이전트 이름:
  - architecture    : 아키텍처 분석
  - chart_research  : 차트 솔루션 연구
  - streaming       : 스트리밍 아키텍처 설계
  - ui_design       : UI/UX 설계
  - kis_api         : KIS API 분석

예시:
  python agents_cli.py list
  python agents_cli.py run architecture
  python agents_cli.py run-all
    """)


async def main():
    """메인 함수"""
    manager = AgentManager()

    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command == 'help' or command == '--help' or command == '-h':
        print_help()

    elif command == 'list':
        print("\n=== 등록된 에이전트 목록 ===\n")
        for idx, agent_info in enumerate(manager.list_agents(), 1):
            print(f"{idx}. {agent_info['name']}")
            print(f"   설명: {agent_info['description']}")
            print(f"   상태: {agent_info['status']}")
            if agent_info['last_run']:
                print(f"   마지막 실행: {agent_info['last_run']}")
            print()

    elif command == 'status':
        print("\n=== 에이전트 상태 ===\n")
        status = manager.get_agent_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif command == 'run':
        if len(sys.argv) < 3:
            print("[X] 에이전트 이름을 지정해주세요.")
            print("예시: python agents_cli.py run architecture")
            return

        agent_name = sys.argv[2]
        print(f"\n[*] {agent_name} 에이전트 실행 중...\n")

        result = await manager.run_agent(agent_name)

        if result.get('status') == 'success':
            print(f"[OK] {agent_name} 분석 완료!\n")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # 결과를 파일로 저장
            output_file = f"agent_results/{agent_name}_result.json"
            import os
            os.makedirs('agent_results', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n[FILE] 결과 저장: {output_file}")
        else:
            print(f"[ERROR] 에러: {result.get('error', 'Unknown error')}")

    elif command == 'run-all':
        print("\n[*] 모든 에이전트 실행 중...\n")

        results = await manager.run_all_agents()

        print("\n=== 실행 결과 요약 ===\n")
        for agent_name, result in results.items():
            status_icon = "[OK]" if result.get('status') == 'success' else "[FAIL]"
            print(f"{status_icon} {agent_name}: {result.get('status', 'unknown')}")

        # 모든 결과를 파일로 저장
        import os
        os.makedirs('agent_results', exist_ok=True)
        output_file = 'agent_results/all_agents_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[FILE] 전체 결과 저장: {output_file}")

    else:
        print(f"[ERROR] 알 수 없는 명령어: {command}")
        print_help()


if __name__ == '__main__':
    asyncio.run(main())
