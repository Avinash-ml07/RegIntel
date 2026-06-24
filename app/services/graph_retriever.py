import os
import json
import numpy as np
import networkx as nx
from pathlib import Path
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from app.config import settings

class LocalDualStoreRetriever:
    def __init__(self) -> None:
        # 1. Semantic Vector Store Initialization
        try:
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            # Fallback wrapper path configuration for offline environments
            self.embedder = None
            print("Warning: SentenceTransformer 'all-MiniLM-L6-v2' not loaded. Run offline prep commands.")
        
        self.vector_store_path = settings.REGULATORY_DROPBOX / "vector_store.json"
        self.vector_documents: List[Dict[str, Any]] = []
        self._load_vector_store()
        
        # 2. Relational NetworkX Topology Initialization
        self.graph = nx.DiGraph()
        self._initialize_topology()

    def _load_vector_store(self) -> None:
        if self.vector_store_path.is_file():
            try:
                with open(self.vector_store_path, "r", encoding="utf-8") as f:
                    self.vector_documents = json.load(f)
            except Exception:
                self.vector_documents = []

    def _initialize_topology(self) -> None:
        """
        Hardcodes internal policy topology mapping dependencies between
        Databases, Core API Interfaces, and Operational Teams.
        """
        # Node Type definitions
        databases = ["ConsentMgmtDB", "CoreBankingDB", "CyberIncidentDB", "AuditLogsDB"]
        apis = ["ConsentValidationAPI", "DigitalLendingGateway", "SecurityIncidentLogger"]
        teams = ["IT Security Team", "Compliance Operations Division", "Core Platform Engineering"]
        
        for db in databases:
            self.graph.add_node(db, type="Database")
        for api in apis:
            self.graph.add_node(api, type="API")
        for team in teams:
            self.graph.add_node(team, type="OperationalTeam")
            
        # Define Directed Dependency Flows (System Dependencies -> Team Ownership)
        self.graph.add_edge("ConsentValidationAPI", "ConsentMgmtDB", relationship="READ_WRITE")
        self.graph.add_edge("DigitalLendingGateway", "CoreBankingDB", relationship="DEBITS_CREDITS")
        self.graph.add_edge("DigitalLendingGateway", "ConsentValidationAPI", relationship="DEPENDS_ON")
        self.graph.add_edge("SecurityIncidentLogger", "CyberIncidentDB", relationship="APPEND_LOGS")
        self.graph.add_edge("SecurityIncidentLogger", "AuditLogsDB", relationship="APPEND_LOGS")
        
        # Team assignments
        self.graph.add_edge("ConsentMgmtDB", "Compliance Operations Division", relationship="OWNED_BY")
        self.graph.add_edge("CoreBankingDB", "Core Platform Engineering", relationship="OWNED_BY")
        self.graph.add_edge("CyberIncidentDB", "IT Security Team", relationship="OWNED_BY")
        self.graph.add_edge("AuditLogsDB", "IT Security Team", relationship="OWNED_BY")

    def semantic_search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Calculates cosine similarity locally using the loaded model.
        """
        if not self.embedder or not self.vector_documents:
            return []
            
        try:
            query_vector = self.embedder.encode(query, convert_to_numpy=True)
            results = []
            
            for doc in self.vector_documents:
                doc_vector = np.array(doc["vector"])
                # Compute Cosine Similarity
                dot_product = np.dot(query_vector, doc_vector)
                norm_q = np.linalg.norm(query_vector)
                norm_d = np.linalg.norm(doc_vector)
                similarity = float(dot_product / (norm_q * norm_d)) if norm_q > 0 and norm_d > 0 else 0.0
                
                results.append((similarity, doc["text"], doc.get("metadata", {})))
                
            results.sort(key=lambda x: x[0], reverse=True)
            return [{"similarity": r[0], "text": r[1], "metadata": r[2]} for r in results[:top_k]]
        except Exception as e:
            print(f"Semantic search crash: {str(e)}")
            return []

    def get_blast_radius(self, keyword: str) -> Dict[str, Any]:
        """
        Computes the topological blast radius across dependent nodes up to 2 hops.
        """
        matched_node = None
        for node in self.graph.nodes:
            if keyword.lower() in node.lower():
                matched_node = node
                break
                
        if not matched_node:
            return {"matched_node": None, "dependencies": [], "responsible_teams": []}
            
        # Breadth-first search for hops
        dependencies = list(nx.single_source_shortest_path_length(self.graph, matched_node, cutoff=2).keys())
        
        # Resolve responsible teams in the path
        responsible_teams = []
        for dep in dependencies:
            if self.graph.nodes[dep].get("type") == "OperationalTeam":
                responsible_teams.append(dep)
            else:
                # Find direct neighbors that are teams
                for neighbor in self.graph.neighbors(dep):
                    if self.graph.nodes[neighbor].get("type") == "OperationalTeam":
                        responsible_teams.append(neighbor)
                        
        return {
            "matched_node": matched_node,
            "matched_type": self.graph.nodes[matched_node].get("type"),
            "dependencies": [d for d in dependencies if d != matched_node],
            "responsible_teams": list(set(responsible_teams))
        }