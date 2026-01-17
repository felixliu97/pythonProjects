# Test Plan: Chrome Todo Extension

## Overview

This document outlines test cases for verifying all features of the Quick Todo Chrome extension.

---

## Test Environment

- **Browser**: Chrome v88+
- **Extension**: Load unpacked from `chrome://extensions`
- **Mode**: Developer mode enabled

---

## MVP Features

### TC-1: Add Task
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Type "Buy groceries" in input | Text appears in field |
| 2 | Press Enter | Task added to list, input cleared |
| 3 | Type "Call mom", click + | Task added to list |

### TC-2: Complete Task
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click checkbox on task | Task shows strikethrough |
| 2 | Badge count decreases | ✓ |
| 3 | Click checkbox again | Strikethrough removed |

### TC-3: Delete Task
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click 🗑️ on a task | Task removed from list |
| 2 | Badge updates | ✓ |

### TC-4: Persistence
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add 3 tasks | Tasks visible |
| 2 | Close Chrome | - |
| 3 | Reopen Chrome, click extension | All 3 tasks still present |

### TC-5: Deadline
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click 📅 icon, select future date | - |
| 2 | Add task | Task shows 📅 icon |
| 3 | Hover over 📅 | Tooltip shows date |
| 4 | Set past date on new task | Task shows ⚠️ icon, pink background |

---

## Phase 2 Features

### TC-6: Priority Levels
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Select 🔴 (High) from dropdown | - |
| 2 | Add task | Task shows 🔴 icon |
| 3 | Add task with 🟡 (Medium) | Task shows 🟡 icon |
| 4 | Add task with 🟢 (Low) | Task shows 🟢 icon |
| 5 | Add task with ⚪ (None) | No priority icon shown |

### TC-7: Search
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add tasks: "Work meeting", "Buy groceries", "Work report" | - |
| 2 | Type "work" in search | Only "Work meeting" and "Work report" visible |
| 3 | Clear search | All tasks visible again |

### TC-8: Filter
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add 3 tasks, complete 1 | - |
| 2 | Select "Active" filter | Only incomplete tasks shown |
| 3 | Select "Completed" filter | Only completed tasks shown |
| 4 | Select "Overdue" filter | Only overdue tasks shown |
| 5 | Select "All" filter | All tasks visible |

### TC-9: Dark Mode
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click 🌙 button | UI switches to dark theme |
| 2 | Button changes to ☀️ | ✓ |
| 3 | Close and reopen extension | Dark mode persists |
| 4 | Click ☀️ button | Light mode restored |

### TC-10: Clear Completed
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add 3 tasks | "Clear completed" button hidden |
| 2 | Complete 2 tasks | "Clear completed" button appears |
| 3 | Click "Clear completed" | Completed tasks removed |
| 4 | Button hides | ✓ |

---

## Edge Cases

### TC-11: Empty State
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Delete all tasks | "No tasks yet" message shown |
| 2 | Search with no matches | "No matching tasks" shown |

### TC-12: Long Text
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add task with 100+ characters | Text wraps properly |
| 2 | UI does not break | ✓ |

### TC-13: Special Characters
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add task with `<script>alert('xss')</script>` | Text escaped, no alert |
| 2 | Add task with emoji 🎉 | Displays correctly |

---

## Badge Tests

### TC-14: Badge Count
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Add 5 tasks | Badge shows "5" |
| 2 | Complete 2 tasks | Badge shows "3" |
| 3 | Delete 1 incomplete | Badge shows "2" |
| 4 | Complete all | Badge disappears |

---

## Verification Checklist

- [ ] All MVP features working
- [ ] All Phase 2 features working
- [ ] Dark mode persists
- [ ] Badge updates correctly
- [ ] No console errors
- [ ] Extension size < 100KB
