const API_BASE = 'http://localhost:5000';
let allTasks = [];
let currentFilter = 'all';

// DOM Elements
const tasksContainer = document.getElementById('tasks-container');
const totalTasksEl = document.getElementById('total-tasks');
const pendingTasksEl = document.getElementById('pending-tasks');
const completedTasksEl = document.getElementById('completed-tasks');
const completionRateEl = document.getElementById('completion-rate');
const apiStatusEl = document.getElementById('api-status');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    checkAPIStatus();
    loadTasks();
    loadStats();
    
    // Form submission
    document.getElementById('add-task-form').addEventListener('submit', addTask);
    
    // Setup edit form
    setupEditForm();
    
    // Refresh stats every 30 seconds
    setInterval(loadStats, 30000);
});

// Check API status
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            apiStatusEl.innerHTML = '<i class="fas fa-circle"></i> API Connected';
            apiStatusEl.classList.add('connected');
            apiStatusEl.classList.remove('disconnected');
        }
    } catch (error) {
        apiStatusEl.innerHTML = '<i class="fas fa-circle"></i> API Disconnected';
        apiStatusEl.classList.add('disconnected');
        apiStatusEl.classList.remove('connected');
    }
}

// Load all tasks
async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE}/tasks`);
        const data = await response.json();
        allTasks = data.tasks;
        renderTasks();
        updateCategoryFilter();
        loadStats();
    } catch (error) {
        console.error('Error loading tasks:', error);
        showNotification('Failed to load tasks', 'error');
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();
        
        totalTasksEl.textContent = stats.total_tasks;
        pendingTasksEl.textContent = stats.pending;
        completedTasksEl.textContent = stats.completed;
        completionRateEl.textContent = `${Math.round(stats.completion_rate)}%`;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Render tasks based on current filter
function renderTasks() {
    tasksContainer.innerHTML = '';
    
    let tasksToShow = allTasks;
    
    // Apply filters
    if (currentFilter === 'completed') {
        tasksToShow = allTasks.filter(task => task.completed);
    } else if (currentFilter === 'pending') {
        tasksToShow = allTasks.filter(task => !task.completed);
    }
    
    // Apply category filter
    const categoryFilter = document.getElementById('category-filter').value;
    if (categoryFilter) {
        tasksToShow = tasksToShow.filter(task => task.category === categoryFilter);
    }
    
    // Apply search filter
    const searchTerm = document.getElementById('search-tasks').value.toLowerCase();
    if (searchTerm) {
        tasksToShow = tasksToShow.filter(task => 
            task.title.toLowerCase().includes(searchTerm) ||
            (task.description && task.description.toLowerCase().includes(searchTerm))
        );
    }
    
    if (tasksToShow.length === 0) {
        tasksContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clipboard-list"></i>
                <h3>No tasks found</h3>
                <p>Try changing your filters or add a new task</p>
            </div>
        `;
        return;
    }
    
    // Sort by priority and due date
    tasksToShow.sort((a, b) => {
        const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
        const priorityDiff = (priorityOrder[b.priority] || 0) - (priorityOrder[a.priority] || 0);
        if (priorityDiff !== 0) return priorityDiff;
        
        if (a.due_date && b.due_date) {
            return new Date(a.due_date) - new Date(b.due_date);
        }
        return new Date(b.created_at) - new Date(a.created_at);
    });
    
    // Render each task
    tasksToShow.forEach(task => {
        const taskElement = createTaskElement(task);
        tasksContainer.appendChild(taskElement);
    });
}

// Create task element
function createTaskElement(task) {
    const taskDiv = document.createElement('div');
    taskDiv.className = `task-item ${task.completed ? 'completed' : ''}`;
    taskDiv.innerHTML = `
        <div class="task-content">
            <div class="task-title ${task.completed ? 'completed' : ''}">
                <i class="fas ${task.completed ? 'fa-check-circle' : 'fa-circle'}"></i>
                ${task.title}
            </div>
            ${task.description ? `<div class="task-description">${task.description}</div>` : ''}
            <div class="task-meta">
                <span class="task-category">${getCategoryIcon(task.category)} ${task.category}</span>
                <span class="task-priority priority-${task.priority}">${task.priority}</span>
                ${task.due_date ? `<span class="task-due"><i class="far fa-calendar"></i> ${formatDate(task.due_date)}</span>` : ''}
                ${task.tags && task.tags.length > 0 ? `
                    <div>
                        ${task.tags.map(tag => `<span class="task-tag">#${tag}</span>`).join(' ')}
                    </div>
                ` : ''}
            </div>
        </div>
        <div class="task-actions">
            <button class="action-btn complete" onclick="toggleTask(${task.id})" title="${task.completed ? 'Mark as pending' : 'Mark as complete'}">
                <i class="fas ${task.completed ? 'fa-undo' : 'fa-check'}"></i>
            </button>
            <button class="action-btn edit" onclick="openEditModal(${task.id})" title="Edit">
                <i class="fas fa-edit"></i>
            </button>
            <button class="action-btn delete" onclick="deleteTask(${task.id})" title="Delete">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    return taskDiv;
}

// Add new task
async function addTask(event) {
    event.preventDefault();
    
    const title = document.getElementById('task-title').value.trim();
    if (!title) return;
    
    const taskData = {
        title: title,
        description: document.getElementById('task-description').value.trim(),
        category: document.getElementById('task-category').value,
        priority: document.getElementById('task-priority').value,
        due_date: document.getElementById('task-due').value || null,
        tags: document.getElementById('task-tags').value.split(',').map(tag => tag.trim()).filter(tag => tag)
    };
    
    try {
        const response = await fetch(`${API_BASE}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        
        if (response.ok) {
            const newTask = await response.json();
            showNotification(`Task "${newTask.title}" added successfully!`, 'success');
            document.getElementById('add-task-form').reset();
            loadTasks();
        }
    } catch (error) {
        console.error('Error adding task:', error);
        showNotification('Failed to add task', 'error');
    }
}

// Toggle task completion
async function toggleTask(taskId) {
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}/toggle`, {
            method: 'PATCH'
        });
        
        if (response.ok) {
            const updatedTask = await response.json();
            showNotification(`Task marked as ${updatedTask.completed ? 'completed' : 'pending'}`, 'success');
            loadTasks();
        }
    } catch (error) {
        console.error('Error toggling task:', error);
        showNotification('Failed to update task', 'error');
    }
}

// Delete task
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Task deleted successfully!', 'success');
            loadTasks();
        }
    } catch (error) {
        console.error('Error deleting task:', error);
        showNotification('Failed to delete task', 'error');
    }
}

// Clear completed
