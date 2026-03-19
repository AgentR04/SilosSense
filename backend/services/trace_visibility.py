from copy import deepcopy
from typing import Any, Dict


def _strip_retrieval_chunks(trace: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = deepcopy(trace)

    for item in cleaned.get("agent_outputs", []):
        retrieval = item.get("retrieval", [])
        item["retrieval"] = [
            {
                "source": r.get("source", "Unknown"),
                "score": r.get("score"),
            }
            for r in retrieval
        ]

    return cleaned


def filter_trace_by_role(trace: Dict[str, Any], role: str) -> Dict[str, Any]:
    normalized_role = (role or "employee").lower()

    if normalized_role == "admin":
        return trace

    if normalized_role == "engineering_lead":
        filtered = deepcopy(trace)
        filtered.pop("history_preview", None)
        return filtered

    if normalized_role == "manager":
        filtered = _strip_retrieval_chunks(trace)
        filtered.pop("history_preview", None)
        return filtered

    filtered = _strip_retrieval_chunks(trace)
    filtered.pop("history_preview", None)

    timeline = filtered.get("timeline", [])
    filtered["timeline"] = [
        {
            "step": event.get("step"),
            "status": event.get("status"),
        }
        for event in timeline
    ]

    return filtered
