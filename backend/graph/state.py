from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict, total=False):
    user_query: str
    chat_history: List[Dict[str, str]]
    role: str
    workspace: str
    query_type: str
    selected_agents: List[str]
    agent_subqueries: Dict[str, str]
    timeline: List[Dict[str, Any]]
    responses: List[Dict[str, Any]]
    final_answer: str
    sources: List[str]
    trace: Dict[str, Any]