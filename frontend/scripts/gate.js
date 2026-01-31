const Gate = {
    init: async () => {
        // 1. Auto-Skip: If we already know the school, go to login
        const cachedSchool = localStorage.getItem('school_context');
        if (cachedSchool) {
            console.log('Gate: School cached, skipping to login.');
            window.Router.navigate('/login');
            return;
        }

        // 2. If not, bind the resolution form
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
            
            // Call API to resolve tenant
            // NOTE: In production, this hits your Django /api/v1/core/resolve/ endpoint
            const response = await fetch(`${App.API_URL}/core/resolve/?slug=${slug}`);
            
            if (!response.ok) {
                throw new Error('School not found. Please check the ID.');
            }

            const data = await response.json();

            // 3. Cache the Identity (The "Trust" Asset)
            const schoolContext = {
                id: data.tenant_id,
                name: data.name, // Ensure your API returns 'name'
                slug: slug,
                resolvedAt: Date.now()
            };
            
            localStorage.setItem('school_context', JSON.stringify(schoolContext));
            
            // 4. Redirect
            window.Router.navigate('/login');

        } catch (error) {
            errorDiv.classList.remove('hidden');
            errorMsg.textContent = error.message;
            submitBtn.disabled = false;
            submitBtn.textContent = 'Continue';
        }
    },

    // UX Helper: Allow user to "break" the cache if they are in the wrong school
    clearAndReset: (e) => {
        if(e) e.preventDefault();
        if (confirm("Are you sure you want to switch schools?")) {
            localStorage.removeItem('school_context');
            localStorage.removeItem('auth_token'); // Clear auth too
            window.Router.navigate('/'); // Back to Gate
        }
    }
};

window.Gate = Gate;