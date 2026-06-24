# RegIntel: Agentic Regulatory Intelligence System for Indian Banking

RegIntel is an offline-first, air-gapped Agentic Regulatory Intelligence system designed to parse, analyze, and generate actionable compliance roadmaps from complex Indian financial regulations (such as RBI and SEBI circulars). 

This system complies with strict regulatory requirements: it operates with zero external network connectivity, runs entirely on local infrastructure, invokes no external LLM APIs, and implements zero-knowledge data privacy processing before sending contexts to local model engines.

---

## 1. Directory Structure

The complete system architecture is organized as follows:

```text
regintel-pipeline/
├── README.md                     # Documentation and execution guide
├── requirements.txt              # Production dependency specifications
├── offline_assets/               # Pre-downloaded wheels and models for offline transfer
│   └── en_core_web_sm-3.7.0-py3-none-any.whl
├── regulatory_dropbox/           # Local file database directory
│   ├── mock_rbi_circular.txt     # Test target document (Digital Lending Circular)
│   └── vector_store.json         # Seeded local semantic policy vector database
├── scripts/
│   └── seed_local_data.py        # Local vector store generation and seeding utility
├── app/
    ├── __init__.py
    ├── config.py                 # Core configurations and filesystem bootstrapping
    ├── main.py                   # FastAPI routing layout and LangGraph worker loops
    ├── schemas/
    │   ├── __init__.py
    │   ├── state.py              # LangGraph state machine types and structural definitions
    │   └── map_schema.py         # JSON schema specifications for output compliance actions
    ├── services/
    │   ├── __init__.py
    │   ├── parser.py             # Rule-based and spaCy regulatory parsing service
    │   ├── privacy.py            # Local PII and IT asset masking & Fernet encryption service
    │   └── graph_retriever.py    # Local dual-store (vector + NetworkX topology) retrieval
    └── agents/
        ├── __init__.py
        ├── watcher.py            # LangGraph nodes for document ingestion and structural parsing
        └── graph_rag.py          # Concurrent GraphRAG, zero-knowledge masking, and LLM nodes