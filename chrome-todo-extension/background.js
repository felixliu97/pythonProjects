// Background service worker - updates badge when storage changes
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local' && changes.todos) {
    updateBadge(changes.todos.newValue || []);
  }
});

// Update badge on extension install/startup
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(['todos'], (result) => {
    updateBadge(result.todos || []);
  });
});

chrome.runtime.onStartup.addListener(() => {
  chrome.storage.local.get(['todos'], (result) => {
    updateBadge(result.todos || []);
  });
});

function updateBadge(todos) {
  const incompleteCount = todos.filter(t => !t.done).length;
  chrome.action.setBadgeText({ 
    text: incompleteCount > 0 ? String(incompleteCount) : '' 
  });
  chrome.action.setBadgeBackgroundColor({ color: '#4285f4' });
}
