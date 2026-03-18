import concurrent.futures
from agents.hr_agent import handle_hr_query
from agents.pm_agent import handle_pm_query
from agents.tech_agent import handle_tech_query
from utils.llm import generate_answer


def format_history(chat_history):
    if not chat_history:
        return ""

    recent = chat_history[-6:]
    return "\n".join([
        f"{item['role'].upper()}: {item['text']}"
        for item in recent
    ])


def detect_agents_node(state):
    message = state["user_query"]
    chat_history = state.get("chat_history", [])

    history_text = " ".join([msg["text"].lower() for msg in chat_history[-6:]])
    combined_text = f"{history_text} {message.lower()}"

    hr_keywords = ["pto", "leave", "benefits", "wellness", "insurance", "employee", "reimbursement"]
    pm_keywords = ["task", "ticket", "sprint", "status", "delay", "blocked", "eta", "project", "owner"]
    tech_keywords = ["deploy", "api", "auth", "backend", "server", "token", "frontend"]

    selected = []

    if any(k in combined_text for k in hr_keywords):
        selected.append("HR Agent")

    if any(k in combined_text for k in pm_keywords):
        selected.append("PM Agent")

    if any(k in combined_text for k in tech_keywords):
        selected.append("Tech Agent")

    return {"selected_agents": selected}


def run_agents_node(state):
    message = state["user_query"]
    selected = state.get("selected_agents", [])

    def run(agent_name):
        if agent_name == "HR Agent":
            return handle_hr_query(message)
        if agent_name == "PM Agent":
            return handle_pm_query(message)
        if agent_name == "Tech Agent":
            return handle_tech_query(message)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        responses = list(executor.map(run, selected))

    return {"responses": responses}


def synthesis_node(state):
    message = state["user_query"]
    chat_history = state.get("chat_history", [])
    responses = state.get("responses", [])
    selected_agents = state.get("selected_agents", [])

    history_context = format_history(chat_history)

    trace_base = {
        "query": message,
        "selected_agents": selected_agents,
        "response_count": len(responses),
        "history_used": bool(chat_history),
        "history_preview": history_context,
        "agent_outputs": [
            {
                "agent": r.get("agent", "Unknown"),
                "reply": r.get("reply", ""),
                "source": r.get("source", "Unknown"),
                "retrieval": r.get("debug", [])
            }
            for r in responses
        ]
    }

    if not responses:
        return {
            "final_answer": "I could not classify this query.",
            "sources": [],
            "trace": {**trace_base, "mode": "fallback"}
        }

    if len(responses) == 1:
        response = responses[0]
        return {
            "final_answer": response["reply"],
            "sources": [response.get("source", "Unknown")],
            "trace": {
                **trace_base,
                "mode": "single-agent",
                "final_answer_preview": response["reply"]
            }
        }

    context = "\n\n".join([
        f"Agent: {r['agent']}\nResponse: {r['reply']}\nSource: {r.get('source', 'Unknown')}"
        for r in responses
    ])

    if history_context:
        context = f"Conversation History:\n{history_context}\n\n{context}"

    final = generate_answer(message, context)
    sources = [r.get("source", "Unknown") for r in responses]

    return {
        "final_answer": final,
        "sources": sources,
        "trace": {
            **trace_base,
            "mode": "multi-agent",
            "final_answer_preview": final
        }
    }