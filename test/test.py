import time
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1/watcher"

# Mock Complex RBI Circular Payload representing realistic regulatory structures
rbi_test_text = """
RESERVE BANK OF INDIA
Department of Regulation

RBI/2023-24/110
DoR.STR.REC.72/21.04.048/2023-24

January 15, 2024

All Commercial Banks (including Small Finance Banks & Payments Banks)

Dear Sir / Madam,

Master Direction - Risk Management Requirements for Digital Retail Lending Operations

1. Introduction
The Reserve Bank of India has observed elevated concentrations in digital channel lending and issues these prudential directives under Banking Regulation Act, 1949.

2. Risk Management Protocols
2.1 No bank shall enter digital retail lending associations unless structured risk frameworks are ratified by the Board of Directors.
2.2 Provided that the digital lending applications interface complies with strict customer authentication directives.

3. System Audit Requirements
Every banking system using automated digital interfaces must undergo standard independent cybersecurity audits on a half-yearly basis.

4. Effective Date
This Circular and structural framework provisions are effective from January 15, 2024.
"""

def run_verification():
    print("[1] Triggering Watcher Pipeline with RBI Circular Text...")
    payload = {
        "url": "mock://rbi-digital-lending-circular",
        "raw_text": rbi_test_text
    }
    
    trigger_resp = requests.post(f"{BASE_URL}/trigger", json=payload)
    if trigger_resp.status_code != 202:
        print(f"Error triggering watcher: {trigger_resp.text}")
        return
        
    data = trigger_resp.json()
    task_id = data["task_id"]
    print(f"Trigger successful. Task ID: {task_id}")
    
    # Wait for the background worker to execute the LangGraph state nodes
    print("\n[2] Waiting for asynchronous pipeline ingestion state evaluation...")
    time.sleep(2.5)
    
    # Query execution results
    status_resp = requests.get(f"{BASE_URL}/status/{task_id}")
    if status_resp.status_code != 200:
        print(f"Failed to query job state: {status_resp.text}")
        return
        
    result = status_resp.json()
    print("\n[3] Ingestion Pipeline Analysis State Result:")
    print(f"Status: {result['status']}")
    print(f"Total Segments Parsed: {result['clauses_count']}")
    
    if result["clauses"]:
        meta = result["clauses"][0]["metadata"]
        print("\n=== Extracted Document Metadata ===")
        print(f"Authority:      {meta['authority']}")
        print(f"Circular ID:    {meta['circular_id']}")
        print(f"Subject:        {meta['subject']}")
        print(f"Publish Date:   {meta['publish_date']}")
        print(f"Effective Date: {meta['effective_date']}")
        
        print("\n=== Parsed Section Structural Boundaries ===")
        for clause in result["clauses"]:
            print(f"\n[{clause['clause_reference']}] -> Title: {clause['title']}")
            print(f"Content Preview: {clause['text'][:150]}...")
            
if __name__ == "__main__":
    run_verification()