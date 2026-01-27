/**
 * Premium Theme Manager - 2026
 * Handles dark/light mode with localStorage persistence
 * System preference detection with user override
 */

class ThemeManager {
    constructor() {
        this.STORAGE_KEY = 'muntech-theme-preference';
        this.THEME_CLASS = 'dark-mode';
        this.init();
        this.setupEventListeners();
    }

    init() {
        const saved = this.getSavedTheme();
        const preferred = this.getSystemPreference();
        const theme = saved || preferred || 'light';
        this.setTheme(theme);
    }

    getSavedTheme() {
        return localStorage.getItem(this.STORAGE_KEY);
    }

    getSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    setTheme(theme) {
        const isDark = theme === 'dark';
        const root = document.documentElement;

        if (isDark) {
            root.classList.add(this.THEME_CLASS);
        } else {
            root.classList.remove(this.THEME_CLASS);
        }

        localStorage.setItem(this.STORAGE_KEY, theme);
        this.updateThemeToggle(isDark);
    }

    toggleTheme() {
        const current = this.getCurrentTheme();
        const newTheme = current === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    getCurrentTheme() {
        return document.documentElement.classList.contains(this.THEME_CLASS) ? 'dark' : 'light';
    }

    updateThemeToggle(isDark) {
        const toggleBtn = document.querySelector('.theme-toggle');
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-pressed', isDark);
            toggleBtn.innerHTML = isDark ? '☀️' : '🌙';
            toggleBtn.setAttribute('title', isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
        }
    }

    setupEventListeners() {
        const toggleBtn = document.querySelector('.theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleTheme());
            toggleBtn.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
        }

        // Listen for system preference changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!this.getSavedTheme()) {
                    this.setTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ThemeManager();
    });
} else {
    new ThemeManager();
}

/**
 * Micro-interactions Manager
 * Handles animations, ripple effects, and transitions
 */

class MicroInteractions {
    constructor() {
        this.setupRippleEffect();
        this.setupScrollAnimations();
    }

    setupRippleEffect() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-primary, .btn-premium, .btn');
            if (btn && !btn.classList.contains('no-ripple')) {
                this.createRipple(btn, e);
            }
        });
    }

    createRipple(element, event) {
        const rect = element.getBoundingClientRect();
        const ripple = document.createElement('span');
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    }

    setupScrollAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        document.querySelectorAll('.stat-card, .card, .fade-in').forEach((el) => {
            observer.observe(el);
        });
    }
}

// Initialize micro-interactions
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new MicroInteractions();
    });
} else {
    new MicroInteractions();
}

/**
 * Form Enhancements
 * Floating labels, validation feedback, auto-focus styling
 */

class FormEnhancements {
    constructor() {
        this.setupFloatingLabels();
        this.setupValidation();
        this.setupFocusEffects();
    }

    setupFloatingLabels() {
        document.querySelectorAll('.form-floating input, .form-floating textarea').forEach((input) => {
            input.addEventListener('input', function () {
                this.parentElement.classList.toggle('has-value', this.value.length > 0);
            });

            if (input.value.length > 0) {
                input.parentElement.classList.add('has-value');
            }
        });
    }

    setupValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach((form) => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }

    setupFocusEffects() {
        document.querySelectorAll('.form-control, .form-select').forEach((input) => {
            input.addEventListener('focus', function () {
                this.closest('.form-group')?.classList.add('focused');
            });

            input.addEventListener('blur', function () {
                this.closest('.form-group')?.classList.remove('focused');
            });
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new FormEnhancements();
    });
} else {
    new FormEnhancements();
}

/**
 * Accessibility Manager
 * Keyboard navigation, ARIA labels, focus management
 */

class AccessibilityManager {
    constructor() {
        this.setupKeyboardShortcuts();
        this.setupFocusTrap();
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt + T for theme toggle
            if (e.altKey && e.key === 't') {
                e.preventDefault();
                document.querySelector('.theme-toggle')?.click();
            }
        });
    }

    setupFocusTrap() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const focusableElements = document.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];

                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        lastElement?.focus();
                        e.preventDefault();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        firstElement?.focus();
                        e.preventDefault();
                    }
                }
            }
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new AccessibilityManager();
    });
} else {
    new AccessibilityManager();
}

/**
 * Performance Monitor
 * Track Core Web Vitals and performance metrics
 */

class PerformanceMonitor {
    constructor() {
        this.reportWebVitals();
    }

    reportWebVitals() {
        // Largest Contentful Paint
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    console.log('LCP:', lastEntry.renderTime || lastEntry.loadTime);
                });
                observer.observe({ type: 'largest-contentful-paint', buffered: true });
            } catch (e) {
                console.log('LCP observer not supported');
            }
        }

        // First Input Delay
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach((entry) => {
                        console.log('FID:', entry.processingDuration);
                    });
                });
                observer.observe({ type: 'first-input', buffered: true });
            } catch (e) {
                console.log('FID observer not supported');
            }
        }
    }
}

/**
 * Sankofa Loader Manager - Adinkra Cultural Integration
 * Replaces default loaders with culturally-relevant animated symbol
 * "Go back and fetch it" - represents learning and retrieval
 */
class SankofaLoaderManager {
    constructor() {
        this.loaderClass = 'loader-sankofa';
        this.loaderContainerClass = 'loader-sankofa-container';
    }

    /**
     * Create a Sankofa loader element
     * @returns {HTMLElement} The loader container
     */
    createLoader() {
        const container = document.createElement('div');
        container.className = this.loaderContainerClass;
        container.innerHTML = `<div class="${this.loaderClass}"></div>`;
        return container;
    }

    /**
     * Show loader in a target element
     * @param {HTMLElement|string} target - Element or selector where to show loader
     */
    showLoader(target) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (element) {
            element.innerHTML = '';
            element.appendChild(this.createLoader());
        }
    }

    /**
     * Hide loader from target element
     * @param {HTMLElement|string} target - Element or selector
     */
    hideLoader(target) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (element) {
            const loader = element.querySelector(`.${this.loaderClass}`);
            if (loader) loader.remove();
        }
    }

    /**
     * Replace Bootstrap spinners with Sankofa loader
     * Automatically finds and replaces all .spinner-border elements
     */
    replaceBootstrapSpinners() {
        const spinners = document.querySelectorAll('.spinner-border, .spinner-grow');
        spinners.forEach(spinner => {
            const container = spinner.parentElement;
            spinner.remove();
            container.appendChild(this.createLoader());
        });
    }
}

// Initialize Sankofa Loader
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new PerformanceMonitor();
        window.sankofaLoader = new SankofaLoaderManager();
        window.sankofaLoader.replaceBootstrapSpinners();
    });
} else {
    new PerformanceMonitor();
    window.sankofaLoader = new SankofaLoaderManager();
    window.sankofaLoader.replaceBootstrapSpinners();
