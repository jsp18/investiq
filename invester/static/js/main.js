/**
 * InvestIQ — Main Application JavaScript
 * Core navigation, utilities, and API helpers
 */

// API helper
async function apiCall(url, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) options.body = JSON.stringify(body);
    
    const response = await fetch(url, options);
    return response.json();
}

// Format currency (INR)
function formatINR(amount) {
    if (!amount && amount !== 0) return '--';
    return '₹' + parseFloat(amount).toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

// Format large numbers (crores, lakhs)
function formatIndianNumber(num) {
    if (!num) return '--';
    if (num >= 10000000) return (num / 10000000).toFixed(2) + ' Cr';
    if (num >= 100000) return (num / 100000).toFixed(2) + ' L';
    if (num >= 1000) return (num / 1000).toFixed(1) + ' K';
    return num.toFixed(0);
}

// Notification toast
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; bottom: 24px; right: 24px; z-index: 10000;
        padding: 14px 24px; border-radius: 12px; font-size: 0.875rem; font-weight: 500;
        color: white; box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        animation: slideUp 0.3s ease; font-family: 'Inter', sans-serif;
        backdrop-filter: blur(16px);
    `;
    
    const colors = {
        info: 'rgba(99, 102, 241, 0.9)',
        success: 'rgba(16, 185, 129, 0.9)',
        error: 'rgba(239, 68, 68, 0.9)',
        warning: 'rgba(245, 158, 11, 0.9)'
    };
    toast.style.background = colors[type] || colors.info;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Add entrance animations
    const elements = document.querySelectorAll('.glass-card, .stat-card, .stats-grid');
    elements.forEach((el, i) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        setTimeout(() => {
            el.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, i * 80);
    });
});
