from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict, total=False):
    user_query: str
    chat_history: List[Dict[str, str]]
    selected_agents: List[str]
    responses: List[Dict[str, Any]]
    final_answer: str
    sources: List[str]
    trace: Dict[str, Any]