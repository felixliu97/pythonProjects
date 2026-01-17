// State
let todos = [];
let darkMode = false;

// DOM Elements
const todoInput = document.getElementById('todoInput');
const deadlineInput = document.getElementById('deadlineInput');
const priorityInput = document.getElementById('priorityInput');
const addBtn = document.getElementById('addBtn');
const todoList = document.getElementById('todoList');
const footer = document.getElementById('footer');
const searchInput = document.getElementById('searchInput');
const filterSelect = document.getElementById('filterSelect');
const clearCompletedBtn = document.getElementById('clearCompletedBtn');
const darkModeBtn = document.getElementById('darkModeBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadTodos();
    loadDarkMode();
});

// Event Listeners
addBtn.addEventListener('click', addTodo);
todoInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') addTodo();
});
searchInput.addEventListener('input', render);
filterSelect.addEventListener('change', render);
clearCompletedBtn.addEventListener('click', clearCompleted);
darkModeBtn.addEventListener('click', toggleDarkMode);

// Load todos from storage
function loadTodos() {
    chrome.storage.local.get(['todos'], (result) => {
        todos = result.todos || [];
        render();
    });
}

// Load dark mode preference
function loadDarkMode() {
    chrome.storage.local.get(['darkMode'], (result) => {
        darkMode = result.darkMode || false;
        applyDarkMode();
    });
}

// Apply dark mode
function applyDarkMode() {
    document.body.classList.toggle('dark-mode', darkMode);
    darkModeBtn.textContent = darkMode ? '☀️' : '🌙';
}

// Toggle dark mode
function toggleDarkMode() {
    darkMode = !darkMode;
    chrome.storage.local.set({ darkMode });
    applyDarkMode();
}

// Save todos to storage
function saveTodos() {
    chrome.storage.local.set({ todos }, () => {
        render();
    });
}

// Generate simple unique ID
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Add new todo with optional deadline and priority
function addTodo() {
    const text = todoInput.value.trim();
    if (!text) return;

    const deadline = deadlineInput.value || null;
    const priority = priorityInput.value || null;

    todos.unshift({
        id: generateId(),
        text: text,
        done: false,
        deadline: deadline,
        priority: priority
    });

    todoInput.value = '';
    deadlineInput.value = '';
    priorityInput.value = '';
    saveTodos();
}

// Toggle todo completion
function toggleTodo(id) {
    const todo = todos.find(t => t.id === id);
    if (todo) {
        todo.done = !todo.done;
        saveTodos();
    }
}

// Delete todo
function deleteTodo(id) {
    todos = todos.filter(t => t.id !== id);
    saveTodos();
}

// Clear all completed todos
function clearCompleted() {
    todos = todos.filter(t => !t.done);
    saveTodos();
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Check if deadline is overdue
function isOverdue(deadline) {
    if (!deadline) return false;
    const today = new Date().toISOString().split('T')[0];
    return deadline < today;
}

// Format deadline for display (e.g., "Jan 20")
function formatDeadline(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Get priority icon
function getPriorityIcon(priority) {
    switch (priority) {
        case 'high': return '🔴';
        case 'medium': return '🟡';
        case 'low': return '🟢';
        default: return '';
    }
}

// Filter todos based on search and filter
function getFilteredTodos() {
    const searchTerm = searchInput.value.toLowerCase();
    const filter = filterSelect.value;

    return todos.filter(todo => {
        // Search filter
        if (searchTerm && !todo.text.toLowerCase().includes(searchTerm)) {
            return false;
        }
        // Status filter
        switch (filter) {
            case 'active': return !todo.done;
            case 'completed': return todo.done;
            case 'overdue': return !todo.done && isOverdue(todo.deadline);
            default: return true;
        }
    });
}

// Render the todo list
function render() {
    const filteredTodos = getFilteredTodos();

    if (filteredTodos.length === 0) {
        const message = todos.length === 0
            ? 'No tasks yet. Add one above!'
            : 'No matching tasks.';
        todoList.innerHTML = `
      <div class="empty-state">
        <div class="icon">✨</div>
        <div>${message}</div>
      </div>
    `;
    } else {
        todoList.innerHTML = filteredTodos.map(todo => {
            const overdue = !todo.done && isOverdue(todo.deadline);
            const priorityIcon = getPriorityIcon(todo.priority);
            const deadlineHtml = todo.deadline
                ? `<span class="deadline ${overdue ? 'overdue' : ''}" title="${formatDeadline(todo.deadline)}">${overdue ? '⚠️' : '📅'}</span>`
                : '';

            return `
        <div class="todo-item ${todo.done ? 'done' : ''} ${overdue ? 'overdue-item' : ''}" data-id="${todo.id}">
          <input type="checkbox" class="todo-checkbox" ${todo.done ? 'checked' : ''}>
          ${priorityIcon ? `<span class="priority-icon">${priorityIcon}</span>` : ''}
          <span class="todo-text">${escapeHtml(todo.text)}</span>
          ${deadlineHtml}
          <button class="delete-btn">🗑️</button>
        </div>
      `;
        }).join('');

        // Add event listeners for checkboxes and delete buttons
        todoList.querySelectorAll('.todo-item').forEach(item => {
            const id = item.dataset.id;

            item.querySelector('.todo-checkbox').addEventListener('change', () => {
                toggleTodo(id);
            });

            item.querySelector('.delete-btn').addEventListener('click', () => {
                deleteTodo(id);
            });
        });
    }

    // Update footer
    const incomplete = todos.filter(t => !t.done).length;
    const completed = todos.filter(t => t.done).length;
    footer.textContent = `${incomplete} remaining`;

    // Show/hide clear completed button
    clearCompletedBtn.style.display = completed > 0 ? 'block' : 'none';
}
