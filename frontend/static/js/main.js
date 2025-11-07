/**
 * O-SATE Web Frontend - Main JavaScript
 * Common functions and utilities for the web interface
 */

// API Base URL
const API_BASE_URL = window.location.origin;

/**
 * Make an API request
 * @param {string} endpoint - API endpoint
 * @param {string} method - HTTP method (GET, POST, etc.)
 * @param {object} data - Request data (for POST, PUT)
 * @returns {Promise<object>} Response data
 */
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const responseData = await response.json();
        
        if (!response.ok) {
            throw new Error(responseData.error || 'API request failed');
        }
        
        return responseData;
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

/**
 * Show a toast notification with enhanced styling
 * @param {string} message - Message to display
 * @param {string} type - Type of notification (success, error, warning, info)
 */
function showNotification(message, type = 'info') {
    const alertTypes = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const icons = {
        'success': '<i class="fas fa-check-circle me-2"></i>',
        'error': '<i class="fas fa-exclamation-triangle me-2"></i>',
        'warning': '<i class="fas fa-exclamation-circle me-2"></i>',
        'info': '<i class="fas fa-info-circle me-2"></i>'
    };

    const alertClass = alertTypes[type] || alertTypes['info'];
    const icon = icons[type] || icons['info'];
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '320px';
    alertDiv.style.maxWidth = '500px';
    alertDiv.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
    
    // Create elements safely to prevent XSS
    const contentDiv = document.createElement('div');
    contentDiv.className = 'd-flex align-items-center';
    
    // Create icon element safely
    const iconSpan = document.createElement('span');
    iconSpan.className = 'me-2';
    iconSpan.innerHTML = icon; // Icon is from controlled internal object, not user input
    contentDiv.appendChild(iconSpan);
    
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message; // Use textContent to prevent XSS
    contentDiv.appendChild(messageSpan);
    
    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'btn-close';
    closeBtn.setAttribute('data-bs-dismiss', 'alert');
    closeBtn.setAttribute('aria-label', 'Close');
    
    alertDiv.appendChild(contentDiv);
    alertDiv.appendChild(closeBtn);
    
    document.body.appendChild(alertDiv);
    
    // Add slide-in animation
    setTimeout(() => alertDiv.style.animation = 'slideInDown 0.3s ease', 10);
    
    // Auto-remove after 5 seconds with fade-out animation
    setTimeout(() => {
        alertDiv.style.animation = 'slideOutUp 0.3s ease';
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

// Add CSS animations for notifications
if (!document.getElementById('notification-animations')) {
    const style = document.createElement('style');
    style.id = 'notification-animations';
    style.textContent = `
        @keyframes slideInDown {
            from {
                transform: translate(-50%, -100%);
                opacity: 0;
            }
            to {
                transform: translate(-50%, 0);
                opacity: 1;
            }
        }
        @keyframes slideOutUp {
            from {
                transform: translate(-50%, 0);
                opacity: 1;
            }
            to {
                transform: translate(-50%, -100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format timestamp to readable string
 * @param {string|Date} timestamp - Timestamp to format
 * @returns {string} Formatted timestamp
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

/**
 * Format bytes to human-readable size
 * @param {number} bytes - Bytes to format
 * @returns {string} Formatted size
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Format seconds to readable duration
 * @param {number} seconds - Seconds to format
 * @returns {string} Formatted duration
 */
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(2)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = (seconds % 60).toFixed(0);
        return `${minutes}m ${remainingSeconds}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copied to clipboard!', 'success');
    } catch (error) {
        console.error('Failed to copy:', error);
        showNotification('Failed to copy to clipboard', 'error');
    }
}

/**
 * Download data as JSON file
 * @param {object} data - Data to download
 * @param {string} filename - Filename for download
 */
function downloadJSON(data, filename = 'data.json') {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification(`Downloaded ${filename}`, 'success');
}

/**
 * Show loading spinner in element
 * @param {HTMLElement} element - Element to show spinner in
 * @param {string} message - Optional loading message
 */
function showLoading(element, message = 'Loading...') {
    element.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">${message}</p>
        </div>
    `;
}

/**
 * Check API health
 * @returns {Promise<object>} Health status
 */
async function checkHealth() {
    try {
        const data = await apiRequest('/api/health');
        return data;
    } catch (error) {
        console.error('Health check failed:', error);
        return null;
    }
}

/**
 * Initialize tooltips (Bootstrap)
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    initTooltips();
    
    // Check API health on page load
    checkHealth().then(health => {
        if (!health) {
            console.warn('API health check failed');
        }
    });
    
    // Add current year to footer if needed
    const yearElements = document.querySelectorAll('.current-year');
    yearElements.forEach(el => {
        el.textContent = new Date().getFullYear();
    });
});

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        apiRequest,
        showNotification,
        escapeHtml,
        formatTimestamp,
        formatBytes,
        formatDuration,
        copyToClipboard,
        downloadJSON,
        showLoading,
        checkHealth
    };
}

/**
 * Add smooth scroll behavior to anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href !== '') {
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
 * Add ripple effect to buttons
 */
function addRippleEffect() {
    // Use event delegation to avoid multiple listeners
    document.body.addEventListener('click', function(e) {
        const button = e.target.closest('.btn');
        if (!button) return;
        
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        button.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    });
    
    // Add ripple CSS if not exists
    if (!document.getElementById('ripple-style')) {
        const style = document.createElement('style');
        style.id = 'ripple-style';
        style.textContent = `
            .btn {
                position: relative;
                overflow: hidden;
            }
            .ripple {
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.6);
                transform: scale(0);
                animation: ripple-animation 0.6s ease-out;
                pointer-events: none;
            }
            @keyframes ripple-animation {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Add parallax effect to elements (with debouncing for performance)
 */
function initParallax() {
    const handleParallax = debounce(() => {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.parallax');
        
        parallaxElements.forEach(element => {
            const speed = element.dataset.speed || 0.5;
            element.style.transform = `translateY(${scrolled * speed}px)`;
        });
    }, 16); // ~60fps
    
    window.addEventListener('scroll', handleParallax, { passive: true });
}

/**
 * Add typing animation effect
 * @param {HTMLElement} element - Element to apply typing effect
 * @param {string} text - Text to type
 * @param {number} speed - Typing speed in ms
 */
function typeWriter(element, text, speed = 50) {
    // Cancel any existing animation
    if (element._typingTimeout) {
        clearTimeout(element._typingTimeout);
        delete element._typingTimeout;
    }
    
    let i = 0;
    element.textContent = '';
    
    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            element._typingTimeout = setTimeout(type, speed);
        } else {
            delete element._typingTimeout;
        }
    }
    
    type();
}

/**
 * Animate counter numbers
 * @param {HTMLElement} element - Element containing the number
 * @param {number} target - Target number
 * @param {number} duration - Animation duration in ms
 * @returns {number} Interval ID that can be used with clearInterval() to stop the animation
 * @note The function also stores the interval ID on element._counterInterval for automatic cleanup
 *       if the function is called again on the same element
 */
function animateCounter(element, target, duration = 1000) {
    // Cancel any existing animation
    if (element._counterInterval) {
        clearInterval(element._counterInterval);
        delete element._counterInterval;
    }
    
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
            delete element._counterInterval;
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
    
    // Store on element for auto-cleanup and return for manual cleanup if needed
    element._counterInterval = timer;
    return timer;
}

/**
 * Add intersection observer for animations on scroll
 */
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.classList.contains('animate-in')) {
                entry.target.classList.add('animate-in');
                
                // If it's a counter element, animate it (only once)
                if (entry.target.classList.contains('counter') && !entry.target.dataset.animated) {
                    const target = parseInt(entry.target.textContent);
                    if (!isNaN(target)) {
                        entry.target.dataset.animated = 'true';
                        animateCounter(entry.target, target);
                    }
                }
            }
        });
    }, {
        threshold: 0.1
    });
    
    // Observe all elements with data-animate attribute
    document.querySelectorAll('[data-animate]').forEach(el => {
        observer.observe(el);
    });
    
    // Add animation styles
    if (!document.getElementById('scroll-animation-style')) {
        const style = document.createElement('style');
        style.id = 'scroll-animation-style';
        style.textContent = `
            [data-animate] {
                opacity: 0;
                transform: translateY(30px);
                transition: opacity 0.6s ease, transform 0.6s ease;
            }
            [data-animate].animate-in {
                opacity: 1;
                transform: translateY(0);
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Add loading skeleton for better UX
 * @param {HTMLElement} element - Element to show skeleton in
 * @param {number} lines - Number of skeleton lines
 */
function showLoadingSkeleton(element, lines = 3) {
    // Clear existing content safely
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
    
    // Create skeleton wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'skeleton-wrapper';
    
    // Create skeleton lines using DOM manipulation
    for (let i = 0; i < lines; i++) {
        const line = document.createElement('div');
        line.className = 'skeleton-line';
        line.style.animationDelay = `${i * 0.1}s`;
        wrapper.appendChild(line);
    }
    
    element.appendChild(wrapper);
    
    // Add skeleton CSS if not exists
    if (!document.getElementById('skeleton-style')) {
        const style = document.createElement('style');
        style.id = 'skeleton-style';
        style.textContent = `
            .skeleton-wrapper {
                padding: 1rem;
            }
            .skeleton-line {
                height: 20px;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: skeleton-loading 1.5s ease-in-out infinite;
                border-radius: 4px;
                margin-bottom: 10px;
            }
            .skeleton-line:last-child {
                width: 70%;
            }
            @keyframes skeleton-loading {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Debounce function for performance optimization
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 */
function debounce(func, wait = 300) {
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

/**
 * Add theme toggle functionality (light/dark mode)
 */
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        // Default to light theme to match the visual design
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        
        themeToggle.addEventListener('click', () => {
            const theme = document.documentElement.getAttribute('data-theme');
            const newTheme = theme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            showNotification(`Switched to ${newTheme} mode`, 'info');
        });
    }
}

/**
 * Enhanced page visibility handling
 */
function handlePageVisibility() {
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            console.log('Page is hidden - pausing updates');
        } else {
            console.log('Page is visible - resuming updates');
            // Refresh data when page becomes visible
            if (typeof checkHealth === 'function') {
                checkHealth();
            }
        }
    });
}

/**
 * Add keyboard shortcuts
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K for search (if implemented)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals or clear focus
        if (e.key === 'Escape') {
            document.activeElement.blur();
        }
    });
}

/**
 * Initialize all interactive features
 */
function initializeInteractiveFeatures() {
    initSmoothScroll();
    addRippleEffect();
    initParallax();
    initScrollAnimations();
    initThemeToggle();
    handlePageVisibility();
    initKeyboardShortcuts();
}

/**
 * Initialize page - Enhanced version
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    initTooltips();
    
    // Initialize interactive features
    initializeInteractiveFeatures();
    
    // Check API health on page load
    checkHealth().then(health => {
        if (!health) {
            console.warn('API health check failed');
        } else {
            showNotification('System is healthy and ready!', 'success');
        }
    });
    
    // Add current year to footer if needed
    const yearElements = document.querySelectorAll('.current-year');
    yearElements.forEach(el => {
        el.textContent = new Date().getFullYear();
    });
    
    // Add loading complete class for animations
    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
});

// Add page load animation
if (!document.getElementById('page-load-style')) {
    const style = document.createElement('style');
    style.id = 'page-load-style';
    style.textContent = `
        body:not(.loaded) {
            opacity: 0;
        }
        body.loaded {
            opacity: 1;
            transition: opacity 0.3s ease;
        }
    `;
    document.head.appendChild(style);
}
