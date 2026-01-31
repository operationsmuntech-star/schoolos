const Auth = {
    init: () => {
        const loginForm = document.getElementById('login-form');
        
        if (loginForm) {
            // 1. SECURITY: Check if we know the school.
            // If Gate is missing or context is missing, stop execution.
            if (window.Gate && !Gate.verifyContext()) {
                return; // Stop here, Gate.verifyContext() handles the redirect
            }

            Auth.renderSchoolIdentity();
            loginForm.addEventListener('submit', Auth.handleLogin);
        }
    },

    renderSchoolIdentity: () => {
        const cachedStr = localStorage.getItem('school_context');
        const container = document.getElementById('school-identity-container');
        const generic = document.getElementById('generic-identity');
        const nameDisplay = document.getElementById('school-name-display');

        if (cachedStr && container && nameDisplay) {
            const context = JSON.parse(cachedStr);
            nameDisplay.textContent = context.name;
            
            if(generic) generic.classList.add('hidden');
            container.classList.remove('hidden');
        }
    },

    handleLogin: async (e) => {
        e.preventDefault();
        
        if (!navigator.onLine) {
            return Auth.handleOfflineLoginAttempt(e);
        }

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('login-error');
        const errorMsg = document.getElementById('error-message');
        const submitBtn = e.target.querySelector('button');

        const context = JSON.parse(localStorage.getItem('school_context'));
        
        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Verifying...';

            const response = await fetch(`${App.API_URL}/token/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-School-ID': context.id
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                throw new Error('Invalid credentials');
            }

            const data = await response.json();
            Auth.saveSession(data.access, data.refresh);

            // Use window.Router if available, else hard redirect
            if (window.Router) window.Router.navigate('/dashboard');
            else window.location.href = '/dashboard';

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
        try {
            const payload = JSON.parse(atob(access.split('.')[1]));
            localStorage.setItem('token_expiry', payload.exp * 1000);
        } catch (e) {
            localStorage.setItem('token_expiry', Date.now() + 86400000);
        }
    },

    handleOfflineLoginAttempt: (e) => {
        const token = localStorage.getItem('auth_token');
        const expiry = localStorage.getItem('token_expiry');
        const errorDiv = document.getElementById('login-error');
        const errorMsg = document.getElementById('error-message');

        if (token && expiry && Date.now() < parseInt(expiry)) {
            console.log('Auth: Offline entry allowed.');
            if (window.Router) window.Router.navigate('/dashboard');
            else window.location.href = '/dashboard';
        } else {
            errorDiv.classList.remove('hidden');
            errorMsg.textContent = "Offline: Session expired. Connect to internet.";
        }
    },

    isAuthenticated: () => {
        const token = localStorage.getItem('auth_token');
        const expiry = localStorage.getItem('token_expiry');
        if (!token || !expiry) return false;
        return Date.now() < parseInt(expiry);
    },

    logout: () => {
        localStorage.clear(); // Wipe everything
        window.location.href = '/';
    }
};

window.Auth = Auth;