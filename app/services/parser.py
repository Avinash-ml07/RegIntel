import re
import spacy
from typing import List
from app.schemas.state import StructuralClause, RegulatoryMetadata

class RegulatoryParser:
    def __init__(self) -> None:
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError as e:
            # Raise descriptive action steps instead of attempting a live network download
            raise RuntimeError(
                "NLP Engine Failure: spaCy model 'en_core_web_sm' is not loaded. "
                "Ensure you run 'pip install offline_assets/en_core_web_sm-3.7.0-py3-none-any.whl' "
                "inside your air-gapped virtual environment before starting the server."
            ) from e
    
    def extract_metadata(self, text: str) -> RegulatoryMetadata:
        doc_header = self.nlp(text[:4000])
        
        # 1. Authority Resolution
        org_candidates = [ent.text for ent in doc_header.ents if ent.label_ == "ORG"]
        authority = "Reserve Bank of India (RBI)"
        for org in org_candidates:
            if "RESERVE BANK" in org.upper() or "RBI" in org.upper():
                authority = "Reserve Bank of India (RBI)"
                break
            elif "SECURITIES" in org.upper() or "SEBI" in org.upper():
                authority = "Securities and Exchange Board of India (SEBI)"
                break
                
        # 2. Extract Circular/Notification ID
        id_pattern = re.compile(
            r"\b(?:RBI|SEBI|DoR|Ref\.?\s*No|Notification\s*No)[\s\w./()-]+/\d{2,4}-\d{2,4}(?:/\d+)?\b",
            re.IGNORECASE
        )
        circular_id_match = id_pattern.search(text)
        circular_id = circular_id_match.group(0).strip() if circular_id_match else "Unknown-ID"

        # 3. Date Resolution
        date_pattern = (
            r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+"
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}"
            r"|(?:January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+\d{1,2},\s+\d{4})\b"
        )
        regex_dates = re.findall(date_pattern, text)
        publish_date = regex_dates[0] if regex_dates else "Unknown Date"
        
        effective_date = "Immediate"
        eff_match = re.search(
            r"(?:effective\s+from|with\s+effect\s+from|come\s+into\s+force\s+on)\s+(" + date_pattern + r")", 
            text, 
            re.IGNORECASE
        )
        if eff_match:
            effective_date = eff_match.group(1)
        else:
            for sent in doc_header.sents:
                sent_text = sent.text.lower()
                if "effective from" in sent_text or "with effect from" in sent_text:
                    sent_doc = self.nlp(sent.text)
                    sent_dates = [ent.text for ent in sent_doc.ents if ent.label_ == "DATE"]
                    if sent_dates:
                        effective_date = sent_dates[0]
                        break

        # 4. Extract Regulatory Subject Text
        subject = "Unknown Subject"
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for i, line in enumerate(lines):
            if any(term in line for term in ["Madam", "Dear Sir", "All Scheduled", "All Category"]):
                for j in range(i + 1, min(i + 6, len(lines))):
                    if re.match(r"^\d+\.", lines[j]) or "Yours faithfully" in lines[j]:
                        break
                    if len(lines[j]) > 25:
                        subject = lines[j]
                        break
                break
        if subject == "Unknown Subject":
            subj_match = re.search(r"(?:Subject|Sub):\s*(.*)", text, re.IGNORECASE)
            if subj_match:
                subject = subj_match.group(1).strip()

        return RegulatoryMetadata(
            authority=authority,
            circular_id=circular_id,
            publish_date=publish_date,
            effective_date=effective_date,
            subject=subject
        )

    def segment_clauses(self, text: str, metadata: RegulatoryMetadata) -> List[StructuralClause]:
        lines = text.split("\n")
        clauses: List[StructuralClause] = []
        
        current_clause_ref = "0"
        current_title = "Preamble"
        current_text_lines: List[str] = []
        
        clause_pattern = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+(.*)")
        sub_clause_pattern = re.compile(r"^\s*([a-z]\)|[ivx]+\.)\s+(.*)")
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            clause_match = clause_pattern.match(stripped)
            if clause_match:
                if current_text_lines:
                    clauses.append(StructuralClause(
                        clause_id=f"clause_{current_clause_ref}",
                        clause_reference=current_clause_ref,
                        title=current_title,
                        text="\n".join(current_text_lines).strip(),
                        metadata=metadata
                    ))
                    current_text_lines = []
                
                current_clause_ref = clause_match.group(1)
                rest = clause_match.group(2).strip()
                if len(rest) < 60:
                    current_title = rest
                else:
                    current_title = "Regulatory Provision"
                    current_text_lines.append(rest)
            elif sub_clause_pattern.match(stripped):
                current_text_lines.append(stripped)
            else:
                current_text_lines.append(stripped)
                
        if current_text_lines:
            clauses.append(StructuralClause(
                clause_id=f"clause_{current_clause_ref}",
                clause_reference=current_clause_ref,
                title=current_title,
                text="\n".join(current_text_lines).strip(),
                metadata=metadata
            ))
            
        return clauses