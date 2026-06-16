import httpx
from langgraph.graph import StateGraph, END
from app.schemas.state import RegulatoryState
from app.services.parser import RegulatoryParser

parser = RegulatoryParser()

async def ingest_node(state: RegulatoryState) -> RegulatoryState:
    url = state.get("source_url", "")
    raw_text = state.get("raw_text", "")
    errors = list(state.get("errors", []))
    
    if raw_text:
        return {
            **state,
            "status": "INGESTED",
            "errors": errors
        }
        
    if not url:
        errors.append("Validation Error: Missing execution source.")
        return {
            **state,
            "status": "FAILED",
            "errors": errors
        }
        
    if url.startswith("mock://"):
        # Synthesized standardized RBI Master Direction document mockup
        mock_data = (
            "RESERVE BANK OF INDIA\n"
            "Department of Regulation\n\n"
            "RBI/2023-24/105\n"
            "DoR.RET.REC.54/12.01.001/2023-24\n\n"
            "December 28, 2023\n\n"
            "All Scheduled Commercial Banks\n\n"
            "Madam / Dear Sir,\n\n"
            "Master Direction - Classification, Valuation and Operation of Investment Portfolio of Commercial Banks\n\n"
            "1. Introduction\n"
            "The Reserve Bank of India has issued guidelines on classification and valuation of investment portfolio.\n\n"
            "2. Statutory Liquidity Ratio (SLR) Securities\n"
            "2.1 Every bank shall maintain in India assets, the value of which shall not be less than such percentage of its total demand and time liabilities.\n"
            "2.2 Provided that the valuation of these securities shall be in accordance with the specified guidelines.\n\n"
            "3. Effective Date\n"
            "These directions shall come into force with effect from April 1, 2024."
        )
        return {
            **state,
            "raw_text": mock_data,
            "status": "INGESTED",
            "errors": errors
        }
        
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return {
                    **state,
                    "raw_text": response.text,
                    "status": "INGESTED",
                    "errors": errors
                }
            else:
                errors.append(f"HTTP Ingestion connection rejected. Code: {response.status_code}")
                return {
                    **state,
                    "status": "FAILED",
                    "errors": errors
                }
    except Exception as e:
        errors.append(f"Ingestion connection failure exception: {str(e)}")
        return {
            **state,
            "status": "FAILED",
            "errors": errors
        }

async def parse_node(state: RegulatoryState) -> RegulatoryState:
    raw_text = state.get("raw_text", "")
    status = state.get("status", "")
    errors = list(state.get("errors", []))
    
    if status == "FAILED" or not raw_text:
        return state
        
    try:
        metadata = parser.extract_metadata(raw_text)
        clauses = parser.segment_clauses(raw_text, metadata)
        return {
            **state,
            "clauses": clauses,
            "status": "PARSED_SUCCESS",
            "errors": errors
        }
    except Exception as e:
        errors.append(f"Structural parsing engine error: {str(e)}")
        return {
            **state,
            "status": "FAILED",
            "errors": errors
        }

# Define workflow graph execution context
workflow = StateGraph(RegulatoryState)

workflow.add_node("ingest", ingest_node)
workflow.add_node("parse", parse_node)

# Fully compatible with both legacy and newer LangGraph instances
workflow.set_entry_point("ingest")
workflow.add_edge("ingest", "parse")
workflow.add_edge("parse", END)

watcher_graph = workflow.compile()