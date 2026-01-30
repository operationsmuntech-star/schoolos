export async function loadHeader() {
  document.getElementById("header").innerHTML = `
    <header class="header">
      <div class="logo">MunTech</div>
      <div class="header-right">
        <span id="school-name">My School</span>
        <button onclick="logout()">Logout</button>
      </div>
    </header>
  `;
}

window.logout = () => {
  localStorage.clear();
  location.href = "/";
};
