document.addEventListener('DOMContentLoaded', () => {
  const signInBtn = document.getElementById('signInBtn');

  if (!signInBtn) return;

  signInBtn.addEventListener('click', () => {
    // Open a small school-resolution prompt (simple flow): prompt for code or name
    const input = prompt('Enter your School Code (e.g. JPA-001) or School Name');
    if (!input) return;

    // Basic heuristic: if looks like code, set code; otherwise set name
    const isCode = /^[A-Z0-9\-]{3,20}$/i.test(input.trim());

    // Try to resolve via API; fallback to using provided text as code
    const q = encodeURIComponent(input.trim());
    fetch(`/api/v1/schools/?q=${q}`)
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(results => {
        if (Array.isArray(results) && results.length === 1) {
          const school = results[0];
          localStorage.setItem('school_id', school.id);
          localStorage.setItem('school_code', school.code);
          localStorage.setItem('school_name', school.name);
          // Go to login, login view will pick up the stored school
          window.location.href = '/views/login.html';
        } else if (Array.isArray(results) && results.length > 1) {
          // If multiple, pick first for now
          const school = results[0];
          localStorage.setItem('school_id', school.id);
          localStorage.setItem('school_code', school.code);
          localStorage.setItem('school_name', school.name);
          window.location.href = '/views/login.html';
        } else {
          // Fallback: treat input as school code
          localStorage.setItem('school_code', input.trim());
          localStorage.removeItem('school_id');
          localStorage.removeItem('school_name');
          window.location.href = '/views/login.html';
        }
      })
      .catch(() => {
        // Network or API not available — still allow entering school code at login
        localStorage.setItem('school_code', input.trim());
        localStorage.removeItem('school_id');
        localStorage.removeItem('school_name');
        window.location.href = '/views/login.html';
      });
  });
});
