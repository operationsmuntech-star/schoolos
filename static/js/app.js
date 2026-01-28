// ========================================
// THEME MANAGER - Dark Mode System
// ========================================

class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || this.getSystemTheme();
        this.init();
    }
    
    init() {
        this.applyTheme(this.theme);
        this.setupEventListeners();
        this.observeSystemTheme();
    }
    
    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    applyTheme(theme) {
        const html = document.documentElement;
        if (theme === 'dark') {
            html.classList.add('dark-mode');
            document.body.classList.add('dark-mode');
        } else {
            html.classList.remove('dark-mode');
            document.body.classList.remove('dark-mode');
        }
        this.theme = theme;
    }
    
    setupEventListeners() {
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            toggle.addEventListener('click', () => this.toggleTheme());
            this.updateToggleState(toggle);
        }
    }
    
    toggleTheme() {
        const newTheme = this.theme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateToggleState(document.querySelector('.theme-toggle'));
    }
    
    updateToggleState(toggle) {
        if (toggle) {
            toggle.textContent = this.theme === 'dark' ? '☀️' : '🌙';
            toggle.setAttribute('aria-pressed', this.theme === 'dark');
        }
    }
    
    observeSystemTheme() {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager();
});

// ========================================
// NAVIGATION HANDLER
// ========================================

class NavigationHandler {
    constructor() {
        this.navbar = document.querySelector('.navbar');
        this.toggle = document.querySelector('.navbar-toggle');
        this.nav = document.querySelector('.navbar-nav');
        this.init();
    }
    
    init() {
        if (this.toggle) {
            this.toggle.addEventListener('click', () => this.toggleMenu());
        }
        
        // Close menu on link click
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => this.closeMenu());
        });
        
        // Close menu on outside click
        document.addEventListener('click', (e) => {
            if (!this.navbar.contains(e.target)) {
                this.closeMenu();
            }
        });
        
        this.setupScrollBehavior();
    }
    
    toggleMenu() {
        this.nav.classList.toggle('active');
        this.toggle.setAttribute('aria-expanded', 
            this.nav.classList.contains('active'));
    }
    
    closeMenu() {
        this.nav.classList.remove('active');
        this.toggle.setAttribute('aria-expanded', 'false');
    }
    
    setupScrollBehavior() {
        let lastScrollTop = 0;
        window.addEventListener('scroll', () => {
            const scrollTop = window.scrollY;
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // Scrolling down
                this.navbar.style.transform = 'translateY(-100%)';
            } else {
                // Scrolling up
                this.navbar.style.transform = 'translateY(0)';
            }
            lastScrollTop = scrollTop;
        }, false);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new NavigationHandler();
});

// ========================================
// FORM VALIDATION & FEEDBACK
// ========================================

class FormValidator {
    constructor() {
        this.forms = document.querySelectorAll('form');
        this.init();
    }
    
    init() {
        this.forms.forEach(form => {
            form.addEventListener('submit', (e) => this.validateForm(e, form));
            
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('blur', () => this.validateInput(input));
                input.addEventListener('focus', () => this.clearError(input));
            });
        });
    }
    
    validateForm(e, form) {
        let isValid = true;
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            if (!this.validateInput(input)) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            this.showAlert('Please fix the errors in the form', 'danger');
        }
    }
    
    validateInput(input) {
        const value = input.value.trim();
        
        // Required field
        if (input.hasAttribute('required') && !value) {
            this.showError(input, 'This field is required');
            return false;
        }
        
        // Email validation
        if (input.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                this.showError(input, 'Please enter a valid email');
                return false;
            }
        }
        
        // Password validation (min 8 chars if exists)
        if (input.type === 'password' && value && value.length < 8) {
            this.showError(input, 'Password must be at least 8 characters');
            return false;
        }
        
        // Min length
        if (input.hasAttribute('minlength')) {
            const minLength = input.getAttribute('minlength');
            if (value.length < minLength) {
                this.showError(input, `Minimum ${minLength} characters required`);
                return false;
            }
        }
        
        this.showSuccess(input);
        return true;
    }
    
    showError(input, message) {
        input.classList.add('form-error');
        input.classList.remove('form-success');
        
        let errorMessage = input.nextElementSibling;
        if (!errorMessage || !errorMessage.classList.contains('error-message')) {
            errorMessage = document.createElement('small');
            errorMessage.classList.add('error-message');
            input.parentNode.insertBefore(errorMessage, input.nextSibling);
        }
        errorMessage.textContent = message;
        errorMessage.style.color = 'var(--danger)';
    }
    
    showSuccess(input) {
        input.classList.remove('form-error');
        input.classList.add('form-success');
        
        const errorMessage = input.nextElementSibling;
        if (errorMessage && errorMessage.classList.contains('error-message')) {
            errorMessage.remove();
        }
    }
    
    clearError(input) {
        input.classList.remove('form-error');
    }
    
    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} animate-slideDown`;
        alert.innerHTML = `
            <div class="alert-icon">${this.getAlertIcon(type)}</div>
            <div>
                <strong>${type.toUpperCase()}</strong>
                <p>${message}</p>
            </div>
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        const container = document.querySelector('main') || document.body;
        container.insertBefore(alert, container.firstChild);
        
        setTimeout(() => alert.remove(), 5000);
    }
    
    getAlertIcon(type) {
        const icons = {
            success: '✓',
            warning: '⚠️',
            danger: '✕',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new FormValidator();
});

// ========================================
// SMOOTH PAGE TRANSITIONS
// ========================================

function smoothTransition(page) {
    const main = document.querySelector('main');
    main.style.opacity = '0';
    main.style.transform = 'translateY(10px)';
    
    setTimeout(() => {
        window.location.href = page;
    }, 300);
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Show loading spinner
function showLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.id = 'loading-spinner';
    spinner.innerHTML = `
        <div style="position: fixed; inset: 0; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 9999;">
            <div style="font-size: 3rem; animation: rotate 1s linear infinite;">⏳</div>
        </div>
    `;
    document.body.appendChild(spinner);
    return spinner;
}

function hideLoadingSpinner() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.remove();
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success animate-slideDown';
        alert.textContent = 'Copied to clipboard!';
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 2000);
    });
}

// Format date
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Format currency
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}
