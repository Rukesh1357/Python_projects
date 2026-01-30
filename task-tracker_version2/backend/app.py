import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS  # For frontend-backend communication

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File for storage
TASKS_FILE = "tasks.json"

def load_tasks():
    """Load tasks from JSON file"""
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
    return []

def save_tasks(tasks):
    """Save tasks to JSON file"""
    try:
        with open(TASKS_FILE, "w") as f:
            json.dump(tasks, f, indent=4, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving tasks: {e}")
        return False

@app.route("/")
def home():
    return jsonify({
        "message": "Enhanced Task Tracker API",
        "version": "2.0",
        "endpoints": ["/tasks", "/tasks/<id>", "/health", "/stats"]
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/stats")
def stats():
    tasks = load_tasks()
    total = len(tasks)
    completed = sum(1 for task in tasks if task.get("completed", False))
    pending = total - completed
    
    return jsonify({
        "total_tasks": total,
        "completed": completed,
        "pending": pending,
        "completion_rate": (completed/total*100) if total > 0 else 0
    })

@app.route("/tasks", methods=["GET"])
def get_tasks():
    """Get all tasks with optional filtering"""
    tasks = load_tasks()
    
    # Filter parameters
    status = request.args.get("status")
    category = request.args.get("category")
    
    if status == "completed":
        tasks = [t for t in tasks if t.get("completed", False)]
    elif status == "pending":
        tasks = [t for t in tasks if not t.get("completed", False)]
    
    if category:
        tasks = [t for t in tasks if t.get("category") == category]
    
    return jsonify({"tasks": tasks})

@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    """Get a specific task"""
    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@app.route("/tasks", methods=["POST"])
def create_task():
    """Create a new task"""
    data = request.get_json()
    
    if not data or "title" not in data:
        return jsonify({"error": "Title is required"}), 400
    
    tasks = load_tasks()
    
    new_id = max([t["id"] for t in tasks], default=0) + 1
    
    new_task = {
        "id": new_id,
        "title": data["title"],
        "description": data.get("description", ""),
        "category": data.get("category", "general"),
        "priority": data.get("priority", "medium"),
        "completed": False,
        "created_at": datetime.now().isoformat(),
        "due_date": data.get("due_date"),
        "tags": data.get("tags", [])
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    
    logger.info(f"Task created: {new_task['title']}")
    return jsonify(new_task), 201

@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    """Update a task"""
    data = request.get_json()
    tasks = load_tasks()
    
    task_index = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    
    if task_index is None:
        return jsonify({"error": "Task not found"}), 404
    
    # Update fields
    for key in ["title", "description", "category", "priority", "due_date", "tags"]:
        if key in data:
            tasks[task_index][key] = data[key]
    
    if "completed" in data:
        tasks[task_index]["completed"] = data["completed"]
        tasks[task_index]["completed_at"] = datetime.now().isoformat() if data["completed"] else None
    
    tasks[task_index]["updated_at"] = datetime.now().isoformat()
    
    save_tasks(tasks)
    
    logger.info(f"Task {task_id} updated")
    return jsonify(tasks[task_index])

@app.route("/tasks/<int:task_id>/toggle", methods=["PATCH"])
def toggle_task(task_id):
    """Toggle task completion status"""
    tasks = load_tasks()
    
    task_index = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    
    if task_index is None:
        return jsonify({"error": "Task not found"}), 404
    
    tasks[task_index]["completed"] = not tasks[task_index].get("completed", False)
    
    if tasks[task_index]["completed"]:
        tasks[task_index]["completed_at"] = datetime.now().isoformat()
    else:
        tasks[task_index]["completed_at"] = None
    
    tasks[task_index]["updated_at"] = datetime.now().isoformat()
    
    save_tasks(tasks)
    
    status = "completed" if tasks[task_index]["completed"] else "pending"
    logger.info(f"Task {task_id} toggled to {status}")
    return jsonify(tasks[task_index])

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task"""
    tasks = load_tasks()
    
    task_to_delete = next((t for t in tasks if t["id"] == task_id), None)
    
    if not task_to_delete:
        return jsonify({"error": "Task not found"}), 404
    
    tasks.remove(task_to_delete)
    save_tasks(tasks)
    
    logger.info(f"Task deleted: {task_to_delete['title']}")
    return jsonify({"message": "Task deleted successfully", "task": task_to_delete})

@app.route("/tasks/clear-completed", methods=["DELETE"])
def clear_completed():
    """Delete all completed tasks"""
    tasks = load_tasks()
    
    completed_tasks = [t for t in tasks if t.get("completed", False)]
    tasks = [t for t in tasks if not t.get("completed", False)]
    
    save_tasks(tasks)
    
    logger.info(f"Cleared {len(completed_tasks)} completed tasks")
    return jsonify({
        "message": f"Cleared {len(completed_tasks)} completed tasks",
        "cleared": completed_tasks
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
