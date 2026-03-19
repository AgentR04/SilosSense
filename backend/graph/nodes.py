import concurrent.futures
import time
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


def build_timeline_event(step, status="completed", details=""):
    return {
        "step": step,
        "status": status,
        "details": details,
        "timestamp": int(time.time() * 1000),
    }


def build_agent_subquery(agent_name, message):
    if agent_name == "HR Agent":
        return f"Extract HR policy implications for: {message}"
    if agent_name == "PM Agent":
        return f"Extract project status, delays, owners, and ETA related to: {message}"
    if agent_name == "Tech Agent":
        return f"Extract technical systems, backend or API impact for: {message}"
    return message


def role_guidance(role):
    normalized = (role or "employee").lower()

    if normalized == "manager":
        return "Prioritize business impact, ownership, and next actions in a concise manager-ready format."

    if normalized == "admin":
        return "Include concise diagnostics and cross-agent consistency checks when relevant."

    if normalized == "engineering_lead":
        return "Prioritize technical root cause, implementation implications, and risk."

    return "Keep language simple, direct, and practical for an employee audience."


def detect_agents_node(state):
    message = state["user_query"]
    chat_history = state.get("chat_history", [])
    workspace = state.get("workspace", "all")
    timeline = list(state.get("timeline", []))

    timeline.append(build_timeline_event("Query received", details=message[:160]))
    timeline.append(build_timeline_event("Intent detection", details="Analyzing domain intent and workspace scope"))

    history_text = " ".join([msg["text"].lower() for msg in chat_history[-6:]])
    combined_text = f"{history_text} {message.lower()}"

    hr_keywords = ["pto", "leave", "benefits", "wellness", "insurance", "employee", "reimbursement"]
    pm_keywords = ["task", "ticket", "sprint", "status", "delay", "blocked", "eta", "project", "owner"]
    tech_keywords = ["deploy", "api", "auth", "backend", "server", "token", "frontend"]

    scores = {
        "HR Agent": sum(1 for k in hr_keywords if k in combined_text),
        "PM Agent": sum(1 for k in pm_keywords if k in combined_text),
        "Tech Agent": sum(1 for k in tech_keywords if k in combined_text),
    }

    if workspace == "hr":
        scores["HR Agent"] += 3
    elif workspace == "engineering":
        scores["Tech Agent"] += 3
    elif workspace == "product":
        scores["PM Agent"] += 3

    selected = [agent for agent, score in scores.items() if score > 0]

    if not selected:
        if workspace == "hr":
            selected = ["HR Agent"]
        elif workspace == "engineering":
            selected = ["Tech Agent"]
        elif workspace == "product":
            selected = ["PM Agent"]

    query_type = "multi-agent" if len(selected) > 1 else "single-agent"

    timeline.append(
        build_timeline_event(
            "Agent selection",
            details=f"workspace={workspace}, selected={', '.join(selected) if selected else 'none'}",
        )
    )

    return {
        "selected_agents": selected,
        "query_type": query_type,
        "timeline": timeline,
    }


def decompose_query_node(state):
    message = state["user_query"]
    selected = state.get("selected_agents", [])
    timeline = list(state.get("timeline", []))

    subqueries = {agent: build_agent_subquery(agent, message) for agent in selected}

    timeline.append(
        build_timeline_event(
            "Sub-question generation",
            details=f"generated={len(subqueries)}",
        )
    )

    return {
        "agent_subqueries": subqueries,
        "timeline": timeline,
    }


def run_agents_node(state):
    selected = state.get("selected_agents", [])
    subqueries = state.get("agent_subqueries", {})
    timeline = list(state.get("timeline", []))

    timeline.append(build_timeline_event("Parallel execution started", details=f"agents={len(selected)}"))

    def run(agent_name):
        agent_query = subqueries.get(agent_name, state["user_query"])

        if agent_name == "HR Agent":
            start = time.perf_counter()
            response = handle_hr_query(agent_query)
            duration_ms = int((time.perf_counter() - start) * 1000)
            return response, build_timeline_event("HR retrieval completed", details=f"{duration_ms}ms")

        if agent_name == "PM Agent":
            start = time.perf_counter()
            response = handle_pm_query(agent_query)
            duration_ms = int((time.perf_counter() - start) * 1000)
            return response, build_timeline_event("PM lookup completed", details=f"{duration_ms}ms")

        if agent_name == "Tech Agent":
            start = time.perf_counter()
            response = handle_tech_query(agent_query)
            duration_ms = int((time.perf_counter() - start) * 1000)
            return response, build_timeline_event("Tech retrieval completed", details=f"{duration_ms}ms")

        return None, build_timeline_event("Unknown agent skipped", status="error", details=agent_name)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        run_results = list(executor.map(run, selected))

    responses = [result[0] for result in run_results if result[0] is not None]
    timeline.extend([result[1] for result in run_results])

    return {
        "responses": responses,
        "timeline": timeline,
    }


def synthesis_node(state):
    message = state["user_query"]
    chat_history = state.get("chat_history", [])
    role = state.get("role", "employee")
    workspace = state.get("workspace", "all")
    responses = state.get("responses", [])
    subqueries = state.get("agent_subqueries", {})
    selected_agents = state.get("selected_agents", [])
    query_type = state.get("query_type", "single-agent")
    timeline = list(state.get("timeline", []))

    history_context = format_history(chat_history)

    timeline.append(build_timeline_event("Final synthesis completed", details=f"role={role}"))

    trace_base = {
        "query": message,
        "role": role,
        "workspace": workspace,
        "query_type": query_type,
        "selected_agents": selected_agents,
        "subqueries": subqueries,
        "response_count": len(responses),
        "history_used": bool(chat_history),
        "history_preview": history_context,
        "timeline": timeline,
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
            "trace": {**trace_base, "mode": "fallback"},
        }

    if len(responses) == 1:
        response = responses[0]
        if role == "manager":
            final_answer = f"{response['reply']}\n\nOperational note: Monitor dependencies and communicate timeline impact early."
        elif role == "admin":
            final_answer = f"{response['reply']}\n\nDiagnostic summary: Served by {response.get('agent', 'Unknown')} from {response.get('source', 'Unknown')}."
        elif role == "engineering_lead":
            final_answer = f"{response['reply']}\n\nTechnical focus: Validate implementation risk, blockers, and integration impact before rollout."
        else:
            final_answer = response["reply"]

        return {
            "final_answer": final_answer,
            "sources": [response.get("source", "Unknown")],
            "trace": {
                **trace_base,
                "mode": "single-agent",
                "final_answer_preview": final_answer,
            },
        }

    context = "\n\n".join([
        f"Agent: {r['agent']}\nResponse: {r['reply']}\nSource: {r.get('source', 'Unknown')}"
        for r in responses
    ])

    if history_context:
        context = f"Conversation History:\n{history_context}\n\n{context}"

    synthesis_query = (
        f"Original user request: {message}\n"
        f"Role: {role}\n"
        f"Workspace scope: {workspace}\n"
        f"Style guidance: {role_guidance(role)}"
    )

    final = generate_answer(synthesis_query, context)
    sources = [r.get("source", "Unknown") for r in responses]

    return {
        "final_answer": final,
        "sources": sources,
        "trace": {
            **trace_base,
            "mode": "multi-agent",
            "final_answer_preview": final,
        },
    }