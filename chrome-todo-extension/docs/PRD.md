# PRD: Chrome Todo List Extension

## Overview

A lightweight Chrome extension that provides users with a simple, always-accessible todo list directly in their browser. The extension opens as a popup from the toolbar, allowing users to quickly add, complete, and manage tasks without leaving their current webpage.

## Problem Statement

Users frequently need to jot down quick tasks or reminders while browsing the web. Currently, they must:
- Switch to a separate app (disrupting workflow)
- Open a new tab for web-based todo apps (context switching)
- Rely on memory or physical notes

This creates friction and leads to forgotten tasks and reduced productivity.

## Goals & Success Metrics

| Goal | Success Metric |
|------|----------------|
| Quick task capture | Add task in < 3 seconds |
| Zero friction access | Single click to open popup |
| Data persistence | Tasks persist across browser sessions |
| MVP delivery | Launch within 1 week |

---

## User Stories

### US-1: Add a Task
```
As a browser user,
I want to quickly add a todo item,
So that I can capture tasks without leaving my current page.

Acceptance Criteria:
- Given the popup is open
  When I type in the input field and press Enter
  Then the task is added to my list

- Given the popup is open
  When I type and click the "Add" button
  Then the task is added to my list
```

### US-2: Complete a Task
```
As a browser user,
I want to mark tasks as complete,
So that I can track my progress.

Acceptance Criteria:
- Given I have tasks in my list
  When I click the checkbox next to a task
  Then the task is visually marked as complete (strikethrough)
```

### US-3: Delete a Task
```
As a browser user,
I want to remove tasks I no longer need,
So that my list stays clean and relevant.

Acceptance Criteria:
- Given I have tasks in my list
  When I click the delete button on a task
  Then the task is removed from my list
```

### US-4: Persistent Storage
```
As a browser user,
I want my tasks to be saved automatically,
So that they persist when I close and reopen the browser.

Acceptance Criteria:
- Given I have added tasks
  When I close and reopen Chrome
  Then my tasks are still visible
```

### US-5: Add Optional Deadline
```
As a browser user,
I want to optionally set a deadline for a task,
So that I can track time-sensitive items.

Acceptance Criteria:
- Given I am adding a task
  When I click the calendar icon
  Then I can select a date (optional)

- Given a task has a deadline
  When viewing the task list
  Then the deadline is displayed next to the task

- Given a task's deadline has passed
  When viewing the task list
  Then the task shows a visual "overdue" indicator
```

---

## Scope

### In Scope (MVP)
- Add new todo items
- **Optional deadline per task**
- Mark items as complete/incomplete
- Delete items
- Persist data using Chrome storage API
- Clean, minimal popup UI
- Badge showing incomplete task count

### Out of Scope (Future - Phase 2)
- Reminders/notifications
- Categories/tags
- Drag-and-drop reordering
- Cloud sync across devices
- Dark mode toggle
- Export/import tasks
- Keyboard shortcuts
- Priority levels (High/Medium/Low)
- Search/filter tasks
- Recurring tasks

---

## Phase 2 Features (Post-MVP)

### US-6: Priority Levels
```
As a browser user,
I want to set priority (High/Medium/Low) for tasks,
So that I can focus on what's most important.

Acceptance Criteria:
- Given I am adding a task
  When I click the priority button
  Then I can select High (🔴), Medium (🟡), or Low (🟢)

- Given a task has priority
  When viewing the task list
  Then the priority indicator is visible
```

### US-7: Categories/Tags
```
As a browser user,
I want to organize tasks into categories,
So that I can group related tasks together.

Acceptance Criteria:
- User can create custom categories (Work, Personal, Shopping, etc.)
- Tasks can be assigned to one category
- Can filter task list by category
```

### US-8: Search & Filter
```
As a browser user,
I want to search and filter my tasks,
So that I can quickly find specific items.

Acceptance Criteria:
- Search box filters tasks as user types
- Can filter by: All, Active, Completed, Overdue
```

### US-9: Dark Mode
```
As a browser user,
I want to toggle dark mode,
So that the extension is comfortable to use at night.

Acceptance Criteria:
- Toggle switch in settings
- Remembers preference
- Matches system preference by default
```

### US-10: Keyboard Shortcuts
```
As a power user,
I want keyboard shortcuts,
So that I can manage tasks efficiently.

Acceptance Criteria:
- Ctrl+Shift+T: Open extension popup
- Enter: Add task
- Delete: Remove selected task
- Space: Toggle complete
```

### US-11: Export/Import
```
As a browser user,
I want to export and import my tasks,
So that I can backup or transfer my data.

Acceptance Criteria:
- Export as JSON file
- Import from JSON file
- Merge or replace options
```

---

## Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | User can add a task via text input | ✅ Done |
| FR-2 | User can mark a task complete/incomplete | ✅ Done |
| FR-3 | User can delete a task | ✅ Done |
| FR-4 | Tasks persist in Chrome local storage | ✅ Done |
| FR-5 | Popup displays task list with scroll | ✅ Done |
| FR-6 | Badge shows count of incomplete tasks | ✅ Done |
| FR-7 | Empty state message when no tasks | ✅ Done |
| FR-8 | Clear completed tasks button | Phase 2 |
| FR-9 | User can optionally set a deadline for a task | ✅ Done |
| FR-10 | Overdue tasks show visual indicator | ✅ Done |
| FR-11 | Priority levels (High/Medium/Low) | Phase 2 |
| FR-12 | Categories/tags for task organization | Phase 2 |
| FR-13 | Search and filter tasks | Phase 2 |
| FR-14 | Dark mode toggle | Phase 2 |
| FR-15 | Keyboard shortcuts | Phase 2 |
| FR-16 | Export/import tasks as JSON | Phase 2 |

### Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | Popup opens in < 100ms |
| **Storage** | Support up to 500 tasks |
| **Accessibility** | Keyboard navigable, screen reader friendly |
| **Browser** | Chrome v88+ (Manifest V3) |
| **Size** | Extension < 100KB |

---

## Technical Design

### Architecture
```
chrome-todo-extension/
├── manifest.json       # Extension configuration (Manifest V3)
├── popup/
│   ├── popup.html      # Popup UI structure
│   ├── popup.css       # Styling
│   └── popup.js        # Logic (add, complete, delete)
├── background.js       # Service worker (badge updates)
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

### Data Model
```javascript
// Stored in chrome.storage.local
{
  "todos": [
    {
      "id": "uuid-1234",
      "text": "Task description",
      "done": false,
      "deadline": "2026-01-20",  // Optional, null if not set
      "createdAt": 1705123456789
    }
  ]
}
```

### Key APIs
- `chrome.storage.local` - Persist tasks
- `chrome.action.setBadgeText` - Show incomplete count
- `chrome.action.setBadgeBackgroundColor` - Style badge

---

## Wireframe

```
┌──────────────────────────────────┐
│  📋 Quick Todo                   │
├──────────────────────────────────┤
│ ┌──────────────────┬────┬───┐    │
│ │ Add a task...    │ 📅 │ + │    │
│ └──────────────────┴────┴───┘    │
├──────────────────────────────────┤
│ ☐ Buy groceries    Jan 20   🗑️  │
│ ☑ Reply to email            🗑️  │
│ ☐ Review PR       ⚠️ Jan 14 🗑️  │  ← overdue (red)
│ ☐ Schedule meeting          🗑️  │
├──────────────────────────────────┤
│ 3 tasks remaining                │
└──────────────────────────────────┘
```

---

## Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Chrome APIs | Platform | storage.local, action |
| None | External | No external dependencies for MVP |

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Chrome storage limits | Medium | Low | Limit to 500 tasks, implement cleanup |
| Manifest V3 complexity | Medium | Medium | Follow official Chrome docs closely |
| Data loss on extension update | High | Low | Test upgrade path thoroughly |

---

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Setup | 1 day | Project structure, manifest.json, icons |
| Core UI | 2 days | Popup HTML/CSS, Add task functionality |
| Features | 2 days | Complete/delete tasks, storage integration |
| Polish | 1 day | Badge updates, empty state, testing |
| **Total** | **6 days** | MVP ready for Chrome Web Store |

---

## MVP Launch Status ✅

- [x] All "Must Have" requirements implemented
- [x] Extension loads without errors
- [x] Tasks persist across browser sessions
- [x] Tested on Chrome v88+
- [x] Extension size < 100KB
- [ ] Ready for Chrome Web Store submission

---

## Phase 2 Roadmap

| Feature | Effort | Priority | Status |
|---------|--------|----------|--------|
| Priority Levels | 2 hrs | High | Pending |
| Clear Completed | 1 hr | High | Pending |
| Search/Filter | 3 hrs | Medium | Pending |
| Dark Mode | 2 hrs | Medium | Pending |
| Categories | 4 hrs | Medium | Pending |
| Keyboard Shortcuts | 2 hrs | Low | Pending |
| Export/Import | 3 hrs | Low | Pending |
