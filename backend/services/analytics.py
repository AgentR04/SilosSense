import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
ANALYTICS_FILE = BASE_DIR / "data" / "analytics.json"

_lock = Lock()


def _default_payload() -> Dict[str, Any]:
    return {
        "total_queries": 0,
        "agent_usage": {
            "HR Agent": 0,
            "PM Agent": 0,
            "Tech Agent": 0,
        },
        "query_type_counts": {
            "single-agent": 0,
            "multi-agent": 0,
            "fallback": 0,
        },
        "multi_agent_queries": 0,
        "single_agent_queries": 0,
        "cumulative_response_time_ms": 0.0,
        "average_response_time_ms": 0.0,
    }


def _load_payload() -> Dict[str, Any]:
    ANALYTICS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not ANALYTICS_FILE.exists():
        payload = _default_payload()
        ANALYTICS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    try:
        return json.loads(ANALYTICS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = _default_payload()
        ANALYTICS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload


def _persist_payload(payload: Dict[str, Any]) -> None:
    ANALYTICS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def record_query(trace: Dict[str, Any], response_time_ms: float) -> None:
    selected_agents: List[str] = trace.get("selected_agents", [])
    query_mode = trace.get("mode")

    with _lock:
        payload = _load_payload()

        payload["total_queries"] += 1

        for agent in selected_agents:
            payload["agent_usage"][agent] = payload["agent_usage"].get(agent, 0) + 1

        if query_mode in payload["query_type_counts"]:
            payload["query_type_counts"][query_mode] += 1
        else:
            payload["query_type_counts"][query_mode] = 1

        if query_mode == "multi-agent":
            payload["multi_agent_queries"] += 1
        else:
            payload["single_agent_queries"] += 1

        payload["cumulative_response_time_ms"] += max(response_time_ms, 0)
        total_queries = max(payload["total_queries"], 1)
        payload["average_response_time_ms"] = round(
            payload["cumulative_response_time_ms"] / total_queries,
            2,
        )

        _persist_payload(payload)


def get_analytics() -> Dict[str, Any]:
    with _lock:
        payload = _load_payload()

    agent_usage = payload.get("agent_usage", {})
    query_type_counts = payload.get("query_type_counts", {})

    most_used_agent = "N/A"
    if agent_usage:
        most_used_agent = max(agent_usage, key=agent_usage.get)

    most_common_query_type = "N/A"
    if query_type_counts:
        most_common_query_type = max(query_type_counts, key=query_type_counts.get)

    return {
        **payload,
        "most_used_agent": most_used_agent,
        "most_common_query_type": most_common_query_type,
    }
