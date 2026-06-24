# scripts/seed_local_data.py
import os
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

# 1. Define document metadata corpus representing internal bank policy passages
internal_policies = [
    {
        "text": "Existing Bank Policy: Information Security Policy Version 4.2 dictates that core customer databases like CoreBankingDB and ConsentMgmtDB require Multi-Factor Authentication (MFA) on all access protocols.",
        "metadata": {"section": "Database Policy 4.2", "policy_doc": "ISP_V4.2"}
    },
    {
        "text": "Existing Bank Policy: Customer Consent Management Policy V2 requires that validation endpoints like ConsentValidationAPI must maintain a secure ledger and read-write locks for user records.",
        "metadata": {"section": "Consent Validation V2", "policy_doc": "CCMP_V2"}
    },
    {
        "text": "Existing Bank Policy: Incident Response Policy mandates that any cyber-security intrusion inside our server limits must be reported to security-alert@compliance-operations.org within 24 hours.",
        "metadata": {"section": "Incident Thresholds V1", "policy_doc": "IRP_V1"}
    }
]

def seed():
    print("[+] Seeding Local Semantic Vector Store...")
    dropbox_dir = Path("./regulatory_dropbox")
    dropbox_dir.mkdir(exist_ok=True)
    
    store_file = dropbox_dir / "vector_store.json"
    
    print("[+] Loading local sentence-transformers model...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    seeded_docs = []
    for doc in internal_policies:
        print(f" -> Encoding passage: '{doc['text'][:50]}...'")
        vector = embedder.encode(doc["text"], convert_to_numpy=True).tolist()
        seeded_docs.append({
            "text": doc["text"],
            "metadata": doc["metadata"],
            "vector": vector
        })
        
    with open(store_file, "w", encoding="utf-8") as f:
        json.dump(seeded_docs, f, indent=2)
        
    print(f"[+] Seeding Complete. Created {store_file}")

if __name__ == "__main__":
    seed()