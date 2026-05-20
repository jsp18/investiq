/**
 * InvestIQ — Chart.js Configurations
 * Reusable chart templates for price lines, pie charts, etc.
 */

// Global Chart.js defaults for dark theme
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
Chart.defaults.font.family = "'Inter', sans-serif";


/**
 * Create a price line chart
 */
function createPriceChart(ctx, dates, prices, label = 'Price') {
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.3)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.01)');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: label,
                data: prices,
                borderColor: '#6366f1',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#6366f1',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(ctx) {
                            return '₹' + ctx.parsed.y.toLocaleString('en-IN', { maximumFractionDigits: 2 });
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { 
                        color: '#64748b',
                        maxTicksLimit: 8,
                        font: { size: 11 }
                    }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { 
                        color: '#64748b',
                        font: { size: 11 },
                        callback: function(value) {
                            return '₹' + value.toLocaleString('en-IN');
                        }
                    }
                }
            }
        }
    });
}


/**
 * Create a volume bar chart
 */
function createVolumeChart(ctx, dates, volumes) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Volume',
                data: volumes,
                backgroundColor: 'rgba(6, 182, 212, 0.3)',
                borderColor: 'rgba(6, 182, 212, 0.6)',
                borderWidth: 1,
                borderRadius: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { 
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { 
                        color: '#64748b',
                        callback: function(value) {
                            if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M';
                            if (value >= 1000) return (value / 1000).toFixed(0) + 'K';
                            return value;
                        }
                    }
                }
            }
        }
    });
}
