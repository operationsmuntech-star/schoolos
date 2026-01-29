/**
 * Sidebar Component - Navigation menu
 */
function createSidebar() {
  const sidebar = document.createElement('nav');
  sidebar.className = 'bg-indigo-100 w-64 p-4 space-y-2';
  sidebar.innerHTML = `
    <ul class="space-y-2">
      <li><a href="views/dashboard.html" class="block p-2 rounded hover:bg-indigo-200">Dashboard</a></li>
      <li><a href="views/attendance.html" class="block p-2 rounded hover:bg-indigo-200">Attendance</a></li>
      <li><a href="views/academics.html" class="block p-2 rounded hover:bg-indigo-200">Academics</a></li>
      <li><a href="views/settings.html" class="block p-2 rounded hover:bg-indigo-200">Settings</a></li>
    </ul>
  `;
  return sidebar;
}

// Export for use in other scripts
window.createSidebar = createSidebar;
