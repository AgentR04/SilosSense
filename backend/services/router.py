from agents.hr_agent import handle_hr_query
from agents.pm_agent import handle_pm_query
from agents.tech_agent import handle_tech_query

def route_query(message: str):
    text = message.lower()

    hr_keywords = [
        "pto", "leave", "holiday", "benefits", "policy", "hr",
        "wellness", "reimbursement", "insurance", "learning", "employee"
    ]

    pm_keywords = [
        "ticket", "task", "sprint", "deadline", "project",
        "jira", "status", "blocked", "owner", "eta"
    ]

    tech_keywords = [
        "deploy", "deployment", "api", "backend", "frontend",
        "code", "auth", "setup", "token", "server"
    ]

    if any(word in text for word in hr_keywords):
        return handle_hr_query(message)

    if any(word in text for word in pm_keywords):
        return handle_pm_query(message)

    if any(word in text for word in tech_keywords):
        return handle_tech_query(message)

    return {
        "agent": "General Router",
        "reply": "I could not clearly classify this query yet.",
        "source": "Router Fallback"
    }