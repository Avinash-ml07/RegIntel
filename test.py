#test -1 :
# import time
# import requests

# BASE_URL = "http://localhost:8000/api/v1/watcher"

# def main():
#     print("[1] Triggering local watcher pipeline...")
#     payload = {"file_path": "mock_rbi_circular.txt"}
    
#     try:
#         resp = requests.post(f"{BASE_URL}/trigger-local", json=payload)
#         resp.raise_for_status()
#         data = resp.json()
#         task_id = data["task_id"]
#         print(f"-> Success. Received Dynamic Task ID: {task_id}")
#     except Exception as e:
#         print(f"-> Failed to trigger: {e}")
#         return

#     print("\n[2] Waiting 2 seconds for background file processing...")
#     time.sleep(2)

#     print(f"\n[3] Fetching execution state for Task ID: {task_id}...")
#     try:
#         status_resp = requests.get(f"{BASE_URL}/status/{task_id}")
#         status_resp.raise_for_status()
#         result = status_resp.json()
#         print(f"-> Status: {result['status']}")
#         print(f"-> Total Segments Parsed: {result['clauses_count']}")
        
#         if result["clauses"]:
#             meta = result["clauses"][0]["metadata"]
#             print("\n=== Extracted Metadata ===")
#             print(f"Authority:      {meta['authority']}")
#             print(f"Circular ID:    {meta['circular_id'].strip()}")
#             print(f"Publish Date:   {meta['publish_date']}")
#             print(f"Effective Date: {meta['effective_date']}")
#             print(f"Subject:        {meta['subject']}")
            
#             print("\n=== Segment Samples ===")
#             for i, clause in enumerate(result["clauses"][:3]):
#                 print(f"Clause {clause['clause_reference']}: {clause['title']} -> {clause['text'][:100]}...")
#     except Exception as e:
#         print(f"-> Failed to retrieve status: {e}")

# if __name__ == "__main__":
#     main()

#test - 2 
# test_phase2.py
import time
import requests

BASE_URL = "http://localhost:6000/api/v1/watcher"

def run_integration_test():
    print("[1] Triggering Integrated Local GraphRAG Ingestion Pipeline...")
    payload = {"file_path": "mock_rbi_circular.txt"}
    
    try:
        resp = requests.post(f"{BASE_URL}/trigger-local", json=payload)
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
        print(f" -> Pipeline Triggered. Dynamic Task ID: {task_id}")
    except Exception as e:
        print(f" -> Error during trigger: {e}")
        return
        
    # Grant Ollama enough time to run CPU/GPU inference locally for 5 regulatory clauses
    print("\n[2] Waiting for local Ollama LLM execution (40s)...")
    for i in range(4):
        time.sleep(10)
        print(f"  ... {10 * (i+1)}s elapsed ...")
        
    # Query final State
    print("\n[3] Retrieving Final Pipeline State Output...")
    try:
        status_resp = requests.get(f"{BASE_URL}/status/{task_id}")
        status_resp.raise_for_status()
        result = status_resp.json()
        
        print(f" -> Status: {result['status']}")
        print(f" -> Error Logs: {result['errors']}")
        print(f" -> Parsed Clauses: {result['clauses_count']}")
        print(f" -> Generated MAPs: {len(result['maps'])}")
        
        if result["maps"]:
            print("\n=== SYSTEM MAPS GENERATED (UNMASKED BOUNDARY) ===")
            for item in result["maps"]:
                print(f"\n[Clause Reference]: {item['originating_clause']}")
                print(f"  Gap Identified:     {item['identified_policy_gap']}")
                print(f"  Action Required:    {item['concrete_action_required']}")
                print(f"  Success Criterion:  {item['binary_testable_success_criterion']}")
                print(f"  Target Deadline:    {item['deadline']}")
                print(f"  Responsible Teams:  {', '.join(item['responsible_departments'])}")
        else:
            print("\nWarning: No MAPs generated. Check Ollama API logs or model response format.")
            
    except Exception as e:
        print(f" -> Error retrieving status: {e}")

if __name__ == "__main__":
    run_integration_test()