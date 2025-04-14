from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os
import json
import requests
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage

# Load environment variables
load_dotenv()

# Slack setup
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

# Trello setup
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_API_TOKEN = os.getenv("TRELLO_API_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")
TRELLO_LISTS = {
    "To Do": os.getenv("TRELLO_LIST_TODO_ID"),
    "In Progress": os.getenv("TRELLO_LIST_IN_PROGRESS_ID"),
    "Completed": os.getenv("TRELLO_LIST_COMPLETED_ID"),
}

# Groq LLM setup
llm = ChatGroq(
    model_name="llama3-8b-8192",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# File for persisting tasks
TASK_FILE = "tasks.json"

def load_tasks():
    if not os.path.exists(TASK_FILE):
        return {}

    with open(TASK_FILE, "r") as f:
        tasks = json.load(f)

    # Migrate old format to new dictionary structure
    migrated = False
    for task_name in list(tasks.keys()):
        details = tasks[task_name]
        if isinstance(details, str):
            tasks[task_name] = {
                "status": details,
                "priority": "medium",
                "card_id": None
            }
            migrated = True

    if migrated:
        save_tasks(tasks)

    return tasks

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

def build_prompt(user_message):
    return f"""
You are a Slack assistant that manages tasks in a Kanban board.

When given a user message, extract:
- the action: either "create", "complete", "update", "delete", or "view"
- the task: a short task name
- if action is "update", provide the new task name or priority

Respond ONLY in JSON format like this:
{{"action": "create", "task": "design the homepage", "priority": "high"}}

Message: "{user_message}"
"""

def extract_task_from_message(message):
    prompt = build_prompt(message)
    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        return json.loads(response.content)
    except Exception as e:
        print(f"⚠️ LLM response parsing failed: {e}")
        return None

def create_trello_card(task_name, list_name, priority="medium"):
    url = f"https://api.trello.com/1/cards?key={TRELLO_API_KEY}&token={TRELLO_API_TOKEN}"
    data = {
        "name": task_name.capitalize(),
        "idList": TRELLO_LISTS.get(list_name, TRELLO_LISTS["To Do"]),
        "desc": f"Priority: {priority.capitalize()}",
    }
    
    response = requests.post(url, data=data)
    
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")
    
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error decoding JSON from response.")
        return None

def update_trello_card(card_id, list_name):
    url = f"https://api.trello.com/1/cards/{card_id}?key={TRELLO_API_KEY}&token={TRELLO_API_TOKEN}"
    data = {
        "idList": TRELLO_LISTS.get(list_name, TRELLO_LISTS["To Do"])
    }
    
    response = requests.put(url, data=data)
    
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error decoding JSON from response.")
        return None

@app.event("message")
def handle_message_events(body, say):
    if body.get("event", {}).get("subtype") == "bot_message":
        return

    text = body.get("event", {}).get("text", "")
    if not text.strip():
        return

    result = extract_task_from_message(text)

    if not result or "task" not in result or not result["task"]:
        say("❌ *Oops!* I didn't understand your request. Try again with a proper format, like:")
        say("> `Let's work on client onboarding docs`")
        say("> `Just finished the API integration`")
        return

    action = result["action"]
    task_name = result["task"].strip().lower()
    tasks = load_tasks()

    if action == "create":
        priority = result.get("priority", "medium")
        tasks[task_name] = {
            "status": "To Do",
            "priority": priority,
            "card_id": None
        }
        save_tasks(tasks)
        card = create_trello_card(task_name, "To Do", priority)
        if card:
            tasks[task_name]["card_id"] = card.get("id")
            save_tasks(tasks)
        say(f"📋 *New Task Added:*\n> {task_name.capitalize()} with priority {priority.capitalize()}")

    elif action == "complete":
        if task_name in tasks:
            tasks[task_name]["status"] = "Completed"
            card_id = tasks[task_name].get("card_id")
            if card_id:
                update_trello_card(card_id, "Completed")
            save_tasks(tasks)
            say(f"🎉 *Task Completed:*\n> {task_name.capitalize()}")
        else:
            say(f"⚠️ *Unknown Task:*\n> {task_name.capitalize()}")

    elif action == "update":
        if task_name in tasks:
            new_task_name = result.get("new_task_name", None)
            new_priority = result.get("priority", None)
            
            if new_task_name:
                tasks[new_task_name] = tasks.pop(task_name)
                task_name = new_task_name  # Update reference for priority change
            
            if new_priority:
                tasks[task_name]["priority"] = new_priority
                
            save_tasks(tasks)
            say(f"🔄 *Task Updated:*\n> {task_name.capitalize()}")
        else:
            say(f"⚠️ *Task not found for update:*\n> {task_name.capitalize()}")

    elif action == "delete":
        if task_name in tasks:
            del tasks[task_name]
            save_tasks(tasks)
            say(f"🗑️ *Task Deleted:*\n> {task_name.capitalize()}")
        else:
            say(f"⚠️ *Task not found for deletion:*\n> {task_name.capitalize()}")

    elif action == "view":
        if tasks:
            tasks_list = "\n".join(
                [f"• {task}: {details['status']} (Priority: {details['priority'].capitalize()})" 
                 for task, details in tasks.items()]
            )
            say(f"📝 *Current Tasks:*\n{tasks_list}")
        else:
            say("❌ *No tasks in the Kanban board yet*")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
