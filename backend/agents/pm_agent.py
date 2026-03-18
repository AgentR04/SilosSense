import csv
from pathlib import Path

PM_DATA_PATH = Path("data/pm/tickets.csv")

def read_tickets():
    tickets = []

    if PM_DATA_PATH.exists():
        with open(PM_DATA_PATH, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                tickets.append(row)

    return tickets

def handle_pm_query(message: str):
    text = message.lower()
    tickets = read_tickets()

    for ticket in tickets:
        ticket_id = ticket["ticket_id"].lower()
        if ticket_id in text:
            return {
                "agent": "PM Agent",
                "reply": f'{ticket["ticket_id"]} is {ticket["status"]}, assigned to {ticket["owner"]}, with ETA {ticket["eta_days"]} days.',
                "source": "tickets.csv"
            }

    if "sprint" in text:
        completed = sum(1 for t in tickets if t["status"].lower() == "completed")
        in_progress = sum(1 for t in tickets if t["status"].lower() == "in progress")
        blocked = sum(1 for t in tickets if t["status"].lower() == "blocked")

        return {
            "agent": "PM Agent",
            "reply": f'The current sprint has {len(tickets)} tasks: {completed} completed, {in_progress} in progress, and {blocked} blocked.',
            "source": "tickets.csv"
        }

    return {
        "agent": "PM Agent",
        "reply": "I found project data, but I could not match this query precisely yet.",
        "source": "tickets.csv"
    }