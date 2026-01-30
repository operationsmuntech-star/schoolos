export function router() {
  const app = document.getElementById("app");
  const route = location.hash || "#/dashboard";

  const routes = {
    "#/dashboard": "/views/dashboard.html",
    "#/attendance": "/views/attendance.html",
    "#/settings": "/views/settings.html",
  };

  const view = routes[route] || routes["#/dashboard"];

  fetch(view)
    .then(res => res.text())
    .then(html => app.innerHTML = html);
}

window.addEventListener("hashchange", router);
}

// Initialize router
window.router = new Router();
