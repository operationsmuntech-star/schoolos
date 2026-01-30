import { loadHeader } from "../components/header.js";
import { loadSidebar } from "../components/sidebar.js";
import { loadStatusBar } from "../components/statusbar.js";
import { router } from "./router.js";

document.addEventListener("DOMContentLoaded", async () => {
  await loadHeader();
  await loadSidebar();
  await loadStatusBar();

  router(); // initial route
});
