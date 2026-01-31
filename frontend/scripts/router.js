export function router() {
  const app = document.getElementById("app");
  const route = location.hash || "#/dashboard";

  const routes = {
    "#/dashboard": "/static/views/dashboard.html",
    "#/attendance": "/static/views/attendance.html",
    "#/settings": "/static/views/settings.html",
  };

  const view = routes[route] || routes["#/dashboard"];

  fetch(view)
    .then(res => res.text())
    .then(html => app.innerHTML = html);
}

window.addEventListener("hashchange", router);
