from typing import List, Dict, Any
import re
import asyncio
from models import Action

class DocumentAnalyzer:
    def __init__(self):
        self._cache = {}
        self.risk_keywords = {
            "liability": {
                "keywords": ["liability", "responsible", "damages", "indemnify", "indemnity", "claims"],
                "high_risk": ["no liability", "shall not be liable", "irresponsible", "not liable", "not responsible", "limited to zero"],
                "default_level": "medium"
            },
            "termination": {
                "keywords": ["terminate", "termination", "cancel", "notice period"],
                "high_risk": ["immediately", "without notice", "at any time", "sole discretion", "unilateral"],
                "default_level": "medium"
            },
            "payment": {
                "keywords": ["payment", "fee", "refund", "invoice", "price"],
                "high_risk": ["non-refundable", "no refunds", "additional fees", "unconditional", "waives all refund rights"],
                "default_level": "medium"
            },
            "confidentiality": {
                "keywords": ["confidential", "privacy", "disclosure", "secret"],
                "high_risk": ["any time", "without consent", "forever", "perpetual"],
                "default_level": "low"
            },
            "compliance": {
                "keywords": ["comply", "laws", "regulation", "legal", "compliance", "warrants"],
                "high_risk": ["all laws worldwide", "unconditional compliance", "strict liability"],
                "default_level": "low"
            }
        }

    def segment_clauses(self, text: str) -> List[str]:
        # Split by numbering like 1. or 1.1 or (a) or headers like TERMINATION:
        # We split by these but keep them if possible, or just treat double newlines as primary boundaries
        pattern = r'(?:\n\s*\d+(?:\.\d+)*\.?\s+)|(?:\n\s*[A-Z\s]{5,}:\s*\n)|(?:\n\s*\n)'
        clauses = re.split(pattern, text)
        return [c.strip() for c in clauses if len(c.strip()) > 10]

    async def analyze_clause(self, clause: str) -> Action:
        # Yield to event loop to prevent blocking on heavy CPU tasks
        await asyncio.sleep(0)
        
        clause_lower = clause.lower()
        
        # Simple caching mechanism
        if clause_lower in self._cache:
            return self._cache[clause_lower]
        
        best_match = None
        highest_level = "low"
        confidence = 72
        highlights_red = []
        highlights_yellow = []
        phrases_map = {}
        
        for risk_type, info in self.risk_keywords.items():
            found_keywords = [kw for kw in info["keywords"] if kw in clause_lower]
            found_high_risk = [hr for hr in info["high_risk"] if hr in clause_lower]
            
            if found_keywords or found_high_risk:
                level = info["default_level"]
                if found_high_risk:
                    level = "high"
                
                confidence += (7 * len(found_high_risk)) + (3 * len(found_keywords))
                
                for hr in found_high_risk:
                    highlights_red.append(hr)
                    phrases_map[hr] = f"Critical {risk_type} risk: This phrase shifts disproportionate liability or waives core rights."
                for kw in found_keywords:
                    highlights_yellow.append(kw)
                    phrases_map[kw] = f"Potential {risk_type} concern: Language is vague or lacks standard protections."
                
                if level == "high" or (level == "medium" and highest_level == "low"):
                    highest_level = level
                    best_match = (risk_type, level)

        confidence = min(99, confidence)

        if not best_match:
            action = Action(
                risk_level="low",
                risk_type="compliance",
                rewrite="",
                reason="Standard compliant language identified.",
                explanation="The clause uses neutral terms that align with standard legal frameworks. No aggressive shifting of risk was detected.",
                impact="Minimal legal exposure. Standard operating risk only.",
                confidence=72,
                highlights_red=[],
                highlights_yellow=[],
                phrases={}
            )
            self._cache[clause_lower] = action
            return action
        
        risk_type, risk_level = best_match
        
        reason = f"Identified {risk_type} related terms with {risk_level} risk characteristics."
        explanation = f"This clause contains language related to {risk_type}. "
        if risk_level == "high":
            explanation += "The phrasing is highly aggressive and lacks the standard carve-outs or notice periods found in balanced commercial contracts."
            impact = "High financial and operational risk. Could lead to significant losses without legal recourse."
        else:
            explanation += "While standard, the language could be more precise to prevent misinterpretation."
            impact = "Moderate exposure. May lead to disputes over interpretation."
            
        rewrite = f"Modify the {risk_type} clause to include reasonable notice periods and limit liability according to industry standards (e.g., capping at 12 months fees)."
        
        action = Action(
            risk_level=risk_level,
            risk_type=risk_type,
            rewrite=rewrite,
            reason=reason,
            explanation=explanation,
            impact=impact,
            confidence=confidence,
            highlights_red=list(set(highlights_red)),
            highlights_yellow=list(set(highlights_yellow)),
            phrases={k: v for k, v in phrases_map.items() if k in clause_lower}
        )
        self._cache[clause_lower] = action
        return action

    async def _analyze_document_inner(self, text: str) -> Dict[str, Any]:
        clauses = self.segment_clauses(text)
        
        # Parallel Clause Processing
        tasks = [self.analyze_clause(clause) for clause in clauses]
        actions = await asyncio.gather(*tasks)
        
        results = []
        high_count = 0
        med_count = 0
        low_count = 0
        top_risks = set()
        
        for i, (clause, action) in enumerate(zip(clauses, actions)):
            results.append({
                "id": i + 1,
                "clause": clause,
                "analysis": action.model_dump()
            })
            
            if action.risk_level == "high":
                high_count += 1
                top_risks.add(f"Extreme {action.risk_type.value if hasattr(action.risk_type, 'value') else action.risk_type} exposure")
            elif action.risk_level == "medium":
                med_count += 1
            else:
                low_count += 1
        
        total = len(results) if results else 1
        score = 100 - (high_count * 15) - (med_count * 5)
        score = max(0, min(100, score))
        
        distribution = {
            "high": round((high_count / total) * 100) if total else 0,
            "medium": round((med_count / total) * 100) if total else 0,
            "low": round((low_count / total) * 100) if total else 0,
        }
        
        return {
            "results": results,
            "stats": {
                "score": score,
                "high_risk_count": high_count,
                "medium_risk_count": med_count,
                "low_risk_count": low_count,
                "distribution": distribution,
                "top_risks": list(top_risks)[:3]
            }
        }

    async def analyze_document(self, text: str) -> Dict[str, Any]:
        # Wrap processing in a timeout handle to prevent backend lockups
        try:
            return await asyncio.wait_for(self._analyze_document_inner(text), timeout=30.0)
        except asyncio.TimeoutError:
            raise RuntimeError("Document analysis timed out after 30 seconds.")
