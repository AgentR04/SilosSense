from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes import detect_agents_node, decompose_query_node, run_agents_node, synthesis_node

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("detect_agents", detect_agents_node)
    workflow.add_node("decompose_query", decompose_query_node)
    workflow.add_node("run_agents", run_agents_node)
    workflow.add_node("synthesis", synthesis_node)

    workflow.set_entry_point("detect_agents")

    workflow.add_edge("detect_agents", "decompose_query")
    workflow.add_edge("decompose_query", "run_agents")
    workflow.add_edge("run_agents", "synthesis")
    workflow.add_edge("synthesis", END)

    return workflow.compile()