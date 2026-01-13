import argparse
import asyncio
import sys
from simco_agent.core.qa import QAAcceptanceAgent

async def certify(report_path):
    agent = QAAcceptanceAgent()
    results = await agent.run_full_certification(report_path)
    
    if "error" in results:
        print(f"❌ Certification Error: {results['error']}")
        sys.exit(1)
        
    agent.generate_acceptance_document(results)
    
    status = results.get("overall_status")
    if status == "PASS":
        print("✅ SYSTEM CERTIFIED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("❌ SYSTEM QUALIFICATION FAILED")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="reports/pilot_report.json")
    args = parser.parse_args()
    
    asyncio.run(certify(args.report))
