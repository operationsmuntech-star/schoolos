/**
 * Status Bar Component - Shows sync and connection status
 */
function createStatusBar() {
  const statusbar = document.createElement('div');
  statusbar.className = 'bg-gray-800 text-white p-2 text-xs flex justify-between';
  statusbar.innerHTML = `
    <span id="connectionStatus">Offline</span>
    <span id="syncStatus">No sync pending</span>
  `;
  return statusbar;
}

function updateConnectionStatus(online) {
  const statusEl = document.getElementById('connectionStatus');
  if (statusEl) {
    statusEl.textContent = online ? '🟢 Online' : '🔴 Offline';
    statusEl.style.color = online ? '#10b981' : '#ef4444';
  }
}

function updateSyncStatus(pendingCount) {
  const syncEl = document.getElementById('syncStatus');
  if (syncEl) {
    syncEl.textContent = pendingCount > 0 ? `⏳ ${pendingCount} pending sync` : '✓ Synced';
  }
}

// Export for use in other scripts
window.createStatusBar = createStatusBar;
window.updateConnectionStatus = updateConnectionStatus;
window.updateSyncStatus = updateSyncStatus;
