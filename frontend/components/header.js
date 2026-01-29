/**
 * Header Component - Top navigation bar
 */
function createHeader() {
  const header = document.createElement('header');
  header.className = 'bg-indigo-600 text-white p-4 flex justify-between items-center';
  header.innerHTML = `
    <h1 class="text-xl font-bold">MunTech School Infra</h1>
    <div class="flex items-center gap-4">
      <span id="status" class="text-sm">Offline</span>
      <button id="installBtn" class="bg-white text-indigo-600 px-3 py-1 rounded text-sm hover:bg-gray-100">Install App</button>
    </div>
  `;
  return header;
}

// Export for use in other scripts
window.createHeader = createHeader;
