/* ==========================================
   MUNTECH - Main JavaScript
   Production Quality Code
   ========================================== */

/**
 * Initialize application on DOM ready
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    setupFormValidation();
    setupSmoothScroll();
    initializeAOS();
    setupPasswordToggle();
});

/**
 * Initialize Bootstrap Tooltips
 */
function initializeTooltips() {
    const tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    });
}

/**
 * Setup smooth scrolling for anchor links
 */
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

/**
 * Initialize AOS (Animate On Scroll) if available
 */
function initializeAOS() {
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 1000,
            once: true,
            offset: 100
        });
    }
}

/**
 * Setup password visibility toggle
 */
function setupPasswordToggle() {
    const toggleBtns = document.querySelectorAll('.toggle-password');
    toggleBtns.forEach(btn => {
        btn.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });
}

/**
 * Toggle password visibility
 * @param {string} inputId - The ID of the password input field
 */
function togglePasswordVisibility(inputId = 'id_password') {
    const passwordInput = document.getElementById(inputId);
    const toggleBtn = event.target.closest('.toggle-password');
    
    if (!passwordInput || !toggleBtn) return;
    
    const icon = toggleBtn.querySelector('.icon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        if (icon) icon.textContent = '🔒';
    } else {
        passwordInput.type = 'password';
        if (icon) icon.textContent = '👁️';
    }
}

/**
 * Show alert message
 * @param {string} message - The message to display
 * @param {string} type - The alert type (success, danger, warning, info)
 */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('main') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

/**
 * Handle errors and show user-friendly message
 */
function handleError(error) {
    console.error(error);
    showAlert('An error occurred. Please try again.', 'danger');
}

/**
 * Utility: Format date
 */
function formatDate(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

/**
 * Utility: Format currency
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Utility: Validate email format
 */
function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Utility: Debounce function for performance
 */
function debounce(func, wait = 300) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}

console.log('✅ MunTech loaded successfully');
