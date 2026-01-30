import os
import json
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage (for simplicity)
TASKS_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

@app.route("/")
def home():
    return jsonify({"message": "Task Tracker API is running", "status": "OK"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200

@app.route("/tasks", methods=["GET"])
def get_tasks():
    tasks = load_tasks()
    return jsonify({"tasks": tasks})

@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "Title is required"}), 400

    tasks = load_tasks()
    new_task = {
        "id": len(tasks) + 1,
        "title": data["title"],
        "done": False
    }
    tasks.append(new_task)
    save_tasks(tasks)
    logger.info(f"Task added: {new_task}")
    return jsonify(new_task), 201

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    tasks = load_tasks()
    task_to_delete = None
    for task in tasks:
        if task["id"] == task_id:
            task_to_delete = task
            break

    if not task_to_delete:
        return jsonify({"error": "Task not found"}), 404

    tasks.remove(task_to_delete)
    save_tasks(tasks)
    logger.info(f"Task deleted: {task_to_delete}")
    return jsonify({"message": "Task deleted"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
