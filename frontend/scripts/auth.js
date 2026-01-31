const Auth = {
    init: () => {
        const loginForm = document.getElementById('login-form');
        
        // 1. TRUST: If on login page, show the school name immediately
        if (loginForm) {
            Auth.renderSchoolIdentity();
            loginForm.addEventListener('submit', Auth.handleLogin);
        }
    },

    // Inject cached school name into the UI
    renderSchoolIdentity: () => {
        const cachedStr = localStorage.getItem('school_context');
        const container = document.getElementById('school-identity-container');
        const generic = document.getElementById('generic-identity');
        const nameDisplay = document.getElementById('school-name-display');

        if (cachedStr && container && nameDisplay) {
            const context = JSON.parse(cachedStr);
            nameDisplay.textContent = context.name; // "Joyland Academy"
            
            // Swap Generic Title for Specific Trust Signal
            if(generic) generic.classList.add('hidden');
            container.classList.remove('hidden');
        }
    },

    handleLogin: async (e) => {
        e.preventDefault();
        
        // 2. OFFLINE GUARD: Check connectivity first
        if (!navigator.onLine) {
            return Auth.handleOfflineLoginAttempt(e);
        }

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('login-error');
        const errorMsg = document.getElementById('error-message');
        const submitBtn = e.target.querySelector('button');

        // Get context for multi-tenancy
        const context = JSON.parse(localStorage.getItem('school_context'));
        if (!context) {
            // Safety valve: if no school context, force back to gate
            window.Router.navigate('/');
            return;
        }

        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Verifying...';

            const response = await fetch(`${App.API_URL}/token/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-School-ID': context.id // Critical: Tenant Header
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                throw new Error('Invalid credentials');
            }

            const data = await response.json();
            
            // 3. Store Session Data (Token + Expiry)
            Auth.saveSession(data.access, data.refresh);

            window.Router.navigate('/dashboard');

        } catch (error) {
            errorDiv.classList.remove('hidden');
            errorMsg.textContent = error.message;
            submitBtn.disabled = false;
            submitBtn.textContent = 'Sign in';
        }
    },

    saveSession: (access, refresh) => {
        localStorage.setItem('auth_token', access);
        localStorage.setItem('refresh_token', refresh);
        
        // Decode JWT to get real expiry (simple base64 decode for client-side check)
        try {
            const payload = JSON.parse(atob(access.split('.')[1]));
            localStorage.setItem('token_expiry', payload.exp * 1000); // Store as ms
        } catch (e) {
            // Fallback: 24 hours if decode fails
            localStorage.setItem('token_expiry', Date.now() + 86400000);
        }
    },

    // The "Monday Morning" Logic
    handleOfflineLoginAttempt: (e) => {
        // If offline, we can't verify credentials against DB.
        // We check if a VALID token already exists.
        const token = localStorage.getItem('auth_token');
        const expiry = localStorage.getItem('token_expiry');
        const errorDiv = document.getElementById('login-error');
        const errorMsg = document.getElementById('error-message');

        if (token && expiry && Date.now() < parseInt(expiry)) {
            // Token is theoretically valid. Allow entry to App Shell.
            console.log('Auth: Offline but session valid. Allowing entry.');
            window.Router.navigate('/dashboard');
        } else {
            // Token expired or missing. Block entry.
            errorDiv.classList.remove('hidden');
            errorMsg.textContent = "You are offline and your session has expired. Please connect to the internet to log in again.";
        }
    },

    // Called by Router to protect pages
    isAuthenticated: () => {
        const token = localStorage.getItem('auth_token');
        const expiry = localStorage.getItem('token_expiry');
        
        // Simple check: Do we have a token and is it not expired?
        if (!token || !expiry) return false;
        return Date.now() < parseInt(expiry);
    },

    logout: () => {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token_expiry');
        window.Router.navigate('/login');
    }
};

window.Auth = Auth;