from pathlib import Path
from app.schemas.state import RegulatoryState
from app.services.parser import RegulatoryParser
from app.config import settings

parser = RegulatoryParser()

async def ingest_node(state: RegulatoryState) -> RegulatoryState:
    file_path_str = state.get("source_url", "")
    raw_text = state.get("raw_text", "")
    errors = list(state.get("errors", []))
    
    if raw_text:
        return {
            **state,
            "status": "INGESTED",
            "errors": errors
        }
        
    if not file_path_str:
        errors.append("Validation Error: No file path or raw text was provided for ingestion.")
        return {
            **state,
            "status": "FAILED",
            "errors": errors
        }
        
    try:
        target_path = settings.REGULATORY_DROPBOX / file_path_str
        if not target_path.is_file():
            target_path = Path(file_path_str)
            
        if target_path.is_file():
            with open(target_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            return {
                **state,
                "raw_text": file_content,
                "status": "INGESTED",
                "errors": errors
            }
        else:
            errors.append(f"Offline Storage Failure: File not resolved in dropbox or absolute path: '{target_path}'")
            return {
                **state,
                "status": "FAILED",
                "errors": errors
            }
    except Exception as e:
        errors.append(f"FileSystem Access Exception: {str(e)}")
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