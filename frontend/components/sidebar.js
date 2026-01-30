export async function loadSidebar() {
  document.getElementById("sidebar").innerHTML = `
    <nav class="sidebar">
      <a href="#/dashboard">Dashboard</a>
      <a href="#/attendance">Attendance</a>
      <a href="#/settings">Settings</a>
    </nav>
  `;
}
