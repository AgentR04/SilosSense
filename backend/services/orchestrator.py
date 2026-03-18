from agents.hr_agent import handle_hr_query
from agents.pm_agent import handle_pm_query
from agents.tech_agent import handle_tech_query
from utils.llm import generate_answer

def detect_agents(message: str):
    text = message.lower()

    hr_keywords = [
        "pto", "leave", "holiday", "benefits", "policy",
        "wellness", "reimbursement", "insurance", "learning", "employee"
    ]

    pm_keywords = [
        "ticket", "task", "sprint", "deadline", "project",
        "jira", "status", "blocked", "owner", "eta", "delay"
    ]

    tech_keywords = [
        "deploy", "deployment", "api", "backend", "frontend",
        "code", "auth", "setup", "token", "server"
    ]

    selected_agents = []

    if any(word in text for word in hr_keywords):
        selected_agents.append("hr")

    if any(word in text for word in pm_keywords):
        selected_agents.append("pm")

    if any(word in text for word in tech_keywords):
        selected_agents.append("tech")

    return selected_agents

def run_agents(message: str):
    selected_agents = detect_agents(message)

    if not selected_agents:
        return {
            "agent": "General Router",
            "reply": "I could not clearly classify this query yet.",
            "source": "Router Fallback"
        }

    responses = []

    if "hr" in selected_agents:
        responses.append(handle_hr_query(message))

    if "pm" in selected_agents:
        responses.append(handle_pm_query(message))

    if "tech" in selected_agents:
        responses.append(handle_tech_query(message))

    if len(responses) == 1:
        return responses[0]

    context_parts = []
    source_list = []
    agent_list = []

    for response in responses:
        agent_list.append(response["agent"])
        source_list.append(response.get("source", "Unknown Source"))
        context_parts.append(
            f"Agent: {response['agent']}\nResponse: {response['reply']}\nSource: {response.get('source', 'Unknown Source')}"
        )

    combined_context = "\n\n".join(context_parts)

    synthesis_prompt = f"""
You are an enterprise orchestration assistant.

The user asked:
{message}

Multiple specialist agents returned the following responses:
{combined_context}

Instructions:
- Combine the information into one clear and professional answer
- Preserve important facts from each agent
- If the query depends on both sources, explain the relationship clearly
- Do not mention internal implementation details
- Keep the answer concise but useful
"""

    final_answer = generate_answer(message, combined_context)

    return {
        "agent": ", ".join(agent_list),
        "reply": final_answer,
        "source": ", ".join(source_list)
    }