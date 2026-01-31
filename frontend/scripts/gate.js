const Gate = {
    init: async () => {
        // 1. Auto-Skip: If we already know the school, go to login
        const cachedSchool = localStorage.getItem('school_context');
        if (cachedSchool) {
            // Check if we are ALREADY at login to avoid loops
            if (!window.location.pathname.includes('/login')) {
                console.log('Gate: School cached, skipping to login.');
                // Use Router if available, else hard redirect
                if (window.Router) window.Router.navigate('/login');
                else window.location.href = '/login';
            }
            return;
        }

        // 2. Bind the resolution form if it exists
        const form = document.getElementById('school-resolution-form');
        if (form) {
            form.addEventListener('submit', Gate.handleResolution);
        }
    },

    handleResolution: async (e) => {
        e.preventDefault();
        const slugInput = document.getElementById('school-slug');
        const errorDiv = document.getElementById('resolution-error');
        const errorMsg = document.getElementById('error-message');
        const submitBtn = e.target.querySelector('button');

        const slug = slugInput.value.trim();
        if (!slug) return;

        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Searching...';
            
            const response = await fetch(`${App.API_URL}/core/resolve/?slug=${slug}`);
            
            if (!response.ok) {
                throw new Error('School not found. Please check the ID.');
            }

            const data = await response.json();

            const schoolContext = {
                id: data.tenant_id,
                name: data.name,
                slug: slug,
                resolvedAt: Date.now()
            };
            
            localStorage.setItem('school_context', JSON.stringify(schoolContext));
            
            // Redirect using Router or Fallback
            if (window.Router) window.Router.navigate('/login');
            else window.location.href = '/login';

        } catch (error) {
            if (errorDiv) {
                errorDiv.classList.remove('hidden');
                errorMsg.textContent = error.message;
            }
            submitBtn.disabled = false;
            submitBtn.textContent = 'Continue';
        }
    },

    // SECURITY CHECK: Use this in Auth.js
    verifyContext: () => {
        const cachedSchool = localStorage.getItem('school_context');
        if (!cachedSchool) {
            console.warn("Gate: Stranger detected. Hard redirecting to Gate.");
            // FIX: Use hard redirect to prevent Router crashes
            window.location.href = '/'; 
            return false;
        }
        return JSON.parse(cachedSchool);
    },

    clearAndReset: (e) => {
        if(e) e.preventDefault();
        if (confirm("Are you sure you want to switch schools?")) {
            localStorage.removeItem('school_context');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('token_expiry');
            window.location.href = '/';
        }
    }
};

window.Gate = Gate;