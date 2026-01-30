export async function loadStatusBar() {
  const bar = document.getElementById("statusbar");

  function update() {
    const online = navigator.onLine;
    const lastSync = localStorage.getItem("last_sync") || "Never";
    const pending = localStorage.getItem("pending_sync") || 0;

    bar.innerHTML = `
      <div class="statusbar">
        <span class="${online ? "ok" : "warn"}">
          ${online ? "Online" : "Offline"}
        </span>
        <span>Pending: ${pending}</span>
        <span>Last Sync: ${lastSync}</span>
      </div>
    `;
  }

  update();
  window.addEventListener("online", update);
  window.addEventListener("offline", update);
}
