import json
import httpx
import asyncio
from typing import Dict, Any, List
from app.schemas.state import RegulatoryState, MeasurableActionPoint
from app.services.graph_retriever import LocalDualStoreRetriever
from app.services.privacy import LocalPrivacyProxy
from app.config import settings

retriever = LocalDualStoreRetriever()
privacy_proxy = LocalPrivacyProxy()

def construct_ollama_prompt(clause_text: str, semantic_ctx: str, relational_ctx: str) -> str:
    schema_template = {
        "maps": [
            {
                "originating_clause": "string",
                "identified_policy_gap": "string",
                "concrete_action_required": "string",
                "binary_testable_success_criterion": "string",
                "deadline": "string",
                "responsible_departments": ["string"]
            }
        ]
    }
    
    return (
        "You are an expert Enterprise Compliance Architect for Indian Banking.\n"
        "Generate a structured JSON compliance response based on the regulatory clause and provided contexts.\n\n"
        f"REGULATORY CLAUSE:\n{clause_text}\n\n"
        f"SEMANTIC POLICY CONTEXT:\n{semantic_ctx}\n\n"
        f"RELATIONAL INFRASTRUCTURE CONTEXT:\n{relational_ctx}\n\n"
        "INSTRUCTIONS:\n"
        "1. Identify the compliance gap between the regulatory clause and the semantic policy context.\n"
        "2. Formulate exactly 1 clear, concrete, and measurable technical action point based on the relational infrastructure context.\n"
        "3. Provide a strictly binary testable success criterion for the action point.\n"
        f"4. Output strictly a valid JSON matching this schema: {json.dumps(schema_template)}\n"
        "5. Do not include markdown code block syntax (like ```json), conversation text, or conversational preambles. Output raw JSON ONLY."
    )

async def process_single_clause(clause, errors: List[str]) -> List[MeasurableActionPoint]:
    """
    Asynchronous worker processing a single clause context lookup, masking, and local inference call.
    """
    search_terms = ["Consent", "Digital", "Audit", "Incident", "Lending", "Cyber"]
    matched_term = "Core"
    for term in search_terms:
        if term.lower() in clause.text.lower() or term.lower() in clause.title.lower():
            matched_term = term
            break
            
    # Retrieve context
    semantic_docs = retriever.semantic_search(clause.text, top_k=1)
    semantic_context = semantic_docs[0]["text"] if semantic_docs else "No matching existing bank policy."
    
    topology_data = retriever.get_blast_radius(matched_term)
    relational_context = (
        f"Asset Impacted: {topology_data['matched_node']} ({topology_data['matched_type']}). "
        f"Downstream Dependency Chain: {', '.join(topology_data['dependencies'])}. "
        f"Associated Responsible Teams: {', '.join(topology_data['responsible_teams'])}."
    ) if topology_data["matched_node"] else "No active internal system dependencies matched."

    # Symmetrically mask data (Zero-Knowledge)
    combined_text = (
        f"Clause: {clause.text}\n"
        f"Semantic Context: {semantic_context}\n"
        f"Relational Context: {relational_context}"
    )
    masked_text, encrypted_map = privacy_proxy.mask(combined_text)
    
    prompt = construct_ollama_prompt(clause.clause_reference, masked_text, relational_context)
    
    payload = {
        "model": settings.LOCAL_OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0}
    }
    
    clause_maps = []
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{settings.LOCAL_OLLAMA_BASE_URL}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                raw_llm_output = response.json().get("response", "").strip()
                
                # Strip markdown JSON wrappers if outputted
                if "```" in raw_llm_output:
                    raw_llm_output = raw_llm_output.split("```")[1]
                    if raw_llm_output.startswith("json"):
                        raw_llm_output = raw_llm_output[4:]
                raw_llm_output = raw_llm_output.strip()
                
                # Restore original identifiers
                unmasked_llm_output = privacy_proxy.unmask(raw_llm_output, encrypted_map)
                
                try:
                    parsed_json = json.loads(unmasked_llm_output)
                    for item in parsed_json.get("maps", []):
                        item["originating_clause"] = clause.clause_reference
                        clause_maps.append(MeasurableActionPoint(**item))
                except Exception as parse_error:
                    errors.append(f"JSON schema parsing exception on clause {clause.clause_reference}: {str(parse_error)}")
            else:
                errors.append(f"Ollama rejected request for clause {clause.clause_reference}. Code: {response.status_code}")
    except Exception as e:
        errors.append(f"Ollama connection failure on clause {clause.clause_reference}: {str(e)}")
        
    return clause_maps

async def graph_rag_node(state: RegulatoryState) -> RegulatoryState:
    clauses = state.get("clauses", [])
    errors = list(state.get("errors", []))
    
    if state.get("status") == "FAILED" or not clauses:
        return state
        
    # Execute all clauses concurrently to optimize performance
    tasks = [process_single_clause(clause, errors) for clause in clauses]
    results = await asyncio.gather(*tasks)
    
    # Flatten the result collections
    maps = [item for sublist in results for item in sublist]
    
    final_status = "MAPS_GENERATED" if maps else "PARTIAL_FAILURE"
    return {
        **state,
        "maps": maps,
        "status": final_status,
        "errors": errors
    }