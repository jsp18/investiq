/**
 * InvestIQ — Market Page JavaScript
 * Stock search, live data, chart loading, and detail views
 */

let currentSymbol = '';
let priceChart = null;

// ---- Search ----
const searchInput = document.getElementById('stockSearch');
const searchResults = document.getElementById('searchResults');

if (searchInput) {
    searchInput.addEventListener('input', debounce(function() {
        const query = this.value.trim();
        if (query.length < 1) {
            searchResults.classList.remove('visible');
            return;
        }
        
        fetch(`/api/market/search?q=${encodeURIComponent(query)}`)
            .then(r => r.json())
            .then(data => {
                if (!data.success || !data.results.length) {
                    searchResults.innerHTML = '<div class="search-result-item" style="color: var(--text-muted);">No results found</div>';
                    searchResults.classList.add('visible');
                    return;
                }
                
                let html = '';
                data.results.forEach(stock => {
                    html += `
                        <div class="search-result-item" onclick="loadStockDetail('${stock.symbol}')">
                            <div>
                                <div style="font-weight: 600;">${stock.name}</div>
                                <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">${stock.symbol}</div>
                            </div>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">${stock.sector}</div>
                        </div>`;
                });
                
                searchResults.innerHTML = html;
                searchResults.classList.add('visible');
            })
            .catch(() => {
                searchResults.classList.remove('visible');
            });
    }, 300));
    
    // Close search on click outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.remove('visible');
        }
    });
    
    // Enter key
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const val = this.value.trim().toUpperCase();
            if (val) {
                loadStockDetail(val.includes('.') ? val : val + '.NS');
                searchResults.classList.remove('visible');
            }
        }
    });
}


// ---- Load Market Indices ----
function loadIndices() {
    const grid = document.getElementById('indicesGrid');
    if (!grid) return;
    
    grid.innerHTML = `
        <div class="stat-card"><div class="skeleton" style="width: 60%; height: 20px; margin-bottom: 8px;"></div><div class="skeleton" style="width: 40%; height: 32px;"></div></div>
        <div class="stat-card"><div class="skeleton" style="width: 60%; height: 20px; margin-bottom: 8px;"></div><div class="skeleton" style="width: 40%; height: 32px;"></div></div>
        <div class="stat-card"><div class="skeleton" style="width: 60%; height: 20px; margin-bottom: 8px;"></div><div class="skeleton" style="width: 40%; height: 32px;"></div></div>
        <div class="stat-card"><div class="skeleton" style="width: 60%; height: 20px; margin-bottom: 8px;"></div><div class="skeleton" style="width: 40%; height: 32px;"></div></div>
    `;
    
    fetch('/api/market/indices')
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            
            let html = '';
            const icons = { NIFTY50: '📊', SENSEX: '📉', NIFTYBANK: '🏦', NIFTYIT: '💻', GOLD: '🪙' };
            const iconColors = { NIFTY50: 'indigo', SENSEX: 'cyan', NIFTYBANK: 'green', NIFTYIT: 'purple', GOLD: 'amber' };
            
            for (const [name, info] of Object.entries(data.data)) {
                const isPositive = info.change_pct >= 0;
                html += `
                    <div class="stat-card">
                        <div class="stat-icon ${iconColors[name] || 'indigo'}">${icons[name] || '📌'}</div>
                        <div class="stat-value">${info.price?.toLocaleString('en-IN') || '--'}</div>
                        <div class="stat-label">${info.display_name || name}</div>
                        <div class="stat-change ${isPositive ? 'positive' : 'negative'}">
                            ${isPositive ? '+' : ''}${info.change_pct?.toFixed(2) || 0}%
                        </div>
                    </div>`;
            }
            
            grid.innerHTML = html;
        })
        .catch(() => {
            grid.innerHTML = '<p style="color: var(--text-muted);">Unable to load indices</p>';
        });
}


// ---- Load Top Movers ----
function loadMovers() {
    fetch('/api/market/movers')
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            
            renderMoverTable('topGainers', data.data.gainers || [], true);
            renderMoverTable('topLosers', data.data.losers || [], false);
        })
        .catch(() => {
            document.getElementById('topGainers').innerHTML = '<p style="color: var(--text-muted);">Unable to load</p>';
            document.getElementById('topLosers').innerHTML = '<p style="color: var(--text-muted);">Unable to load</p>';
        });
}

function renderMoverTable(containerId, stocks, isGainer) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (!stocks.length) {
        container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 20px;">No data available</p>';
        return;
    }
    
    let html = '<table class="data-table"><thead><tr><th>Stock</th><th>Price (₹)</th><th>Change</th></tr></thead><tbody>';
    
    stocks.forEach(stock => {
        const colorClass = isGainer ? 'text-success' : 'text-danger';
        const arrow = isGainer ? '▲' : '▼';
        html += `
            <tr style="cursor: pointer;" onclick="loadStockDetail('${stock.symbol}')">
                <td>
                    <div style="font-weight: 600; font-size: 0.85rem;">${stock.name || stock.symbol}</div>
                    <div style="font-size: 0.7rem; color: var(--text-muted); font-family: var(--font-mono);">${stock.symbol.replace('.NS','')}</div>
                </td>
                <td class="price">₹${stock.price?.toLocaleString('en-IN')}</td>
                <td class="${colorClass}" style="font-weight: 600;">
                    ${arrow} ${Math.abs(stock.change_pct || 0).toFixed(2)}%
                </td>
            </tr>`;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}


// ---- Load Stock Detail ----
function loadStockDetail(symbol) {
    if (!symbol.includes('.')) symbol += '.NS';
    currentSymbol = symbol;
    
    document.getElementById('stockDetail').classList.remove('hidden');
    document.getElementById('moversSection').style.display = 'none';
    
    // Update URL
    window.history.pushState({}, '', `/market?symbol=${symbol}`);
    
    // Clear search
    if (searchInput) {
        searchInput.value = symbol.replace('.NS', '');
        searchResults.classList.remove('visible');
    }
    
    // Load stock data
    fetch(`/api/market/stock/${symbol}?period=6mo`)
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            
            const info = data.info || {};
            const price = data.price || {};
            const history = data.history || {};
            const indicators = data.indicators || {};
            
            // Header
            document.getElementById('stockName').textContent = info.name || symbol;
            document.getElementById('stockSymbol').textContent = symbol + ' • ' + (info.sector || '');
            document.getElementById('stockPrice').textContent = '₹' + (price.price?.toLocaleString('en-IN') || '--');
            
            const changeEl = document.getElementById('stockChange');
            const isPositive = price.change_pct >= 0;
            changeEl.textContent = `${isPositive ? '+' : ''}${price.change?.toFixed(2)} (${isPositive ? '+' : ''}${price.change_pct?.toFixed(2)}%)`;
            changeEl.className = isPositive ? 'text-success' : 'text-danger';
            
            // Price chart
            if (history.dates && history.prices) {
                loadChartData(history.dates, history.prices);
            }
            
            // Stock info
            renderStockInfo(info, price);
            
            // Technical indicators
            renderIndicators(indicators);
        })
        .catch(err => {
            console.error('Error loading stock:', err);
        });
}


function loadChart(symbol, period, btn) {
    if (btn) {
        document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
    
    fetch(`/api/market/history/${symbol}?period=${period}`)
        .then(r => r.json())
        .then(data => {
            if (data.success && data.data) {
                loadChartData(data.data.dates, data.data.prices);
            }
        });
}

function loadChartData(dates, prices) {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;
    
    if (priceChart) priceChart.destroy();
    priceChart = createPriceChart(ctx, dates, prices, 'Price');
}


function renderStockInfo(info, price) {
    const container = document.getElementById('stockInfo');
    if (!container) return;
    
    const marketCap = info.market_cap ? formatIndianNumber(info.market_cap) : 'N/A';
    
    container.innerHTML = `
        <table class="data-table">
            <tr><td style="color: var(--text-muted);">Market Cap</td><td class="text-right text-mono font-bold">${marketCap}</td></tr>
            <tr><td style="color: var(--text-muted);">P/E Ratio</td><td class="text-right text-mono font-bold">${info.pe_ratio?.toFixed(2) || 'N/A'}</td></tr>
            <tr><td style="color: var(--text-muted);">P/B Ratio</td><td class="text-right text-mono font-bold">${info.pb_ratio?.toFixed(2) || 'N/A'}</td></tr>
            <tr><td style="color: var(--text-muted);">Dividend Yield</td><td class="text-right text-mono font-bold">${info.dividend_yield || 0}%</td></tr>
            <tr><td style="color: var(--text-muted);">52W High</td><td class="text-right text-mono font-bold text-success">₹${info.fifty_two_week_high?.toLocaleString('en-IN') || 'N/A'}</td></tr>
            <tr><td style="color: var(--text-muted);">52W Low</td><td class="text-right text-mono font-bold text-danger">₹${info.fifty_two_week_low?.toLocaleString('en-IN') || 'N/A'}</td></tr>
            <tr><td style="color: var(--text-muted);">Volume</td><td class="text-right text-mono font-bold">${formatIndianNumber(price.volume)}</td></tr>
            <tr><td style="color: var(--text-muted);">Day Range</td><td class="text-right text-mono" style="font-size: 0.8rem;">₹${price.low?.toLocaleString('en-IN') || '--'} - ₹${price.high?.toLocaleString('en-IN') || '--'}</td></tr>
        </table>
    `;
}


function renderIndicators(indicators) {
    const container = document.getElementById('technicalIndicators');
    if (!container) return;
    
    if (!indicators || !indicators.rsi) {
        container.innerHTML = '<p style="color: var(--text-muted);">Indicators unavailable</p>';
        return;
    }
    
    let html = `
        <table class="data-table">
            <tr><td style="color: var(--text-muted);">RSI (14)</td><td class="text-right text-mono font-bold">${indicators.rsi}</td></tr>
            <tr><td style="color: var(--text-muted);">MACD</td><td class="text-right text-mono font-bold">${indicators.macd}</td></tr>
            <tr><td style="color: var(--text-muted);">SMA 20</td><td class="text-right text-mono font-bold">₹${indicators.sma_20?.toLocaleString('en-IN')}</td></tr>
            <tr><td style="color: var(--text-muted);">SMA 50</td><td class="text-right text-mono font-bold">₹${indicators.sma_50?.toLocaleString('en-IN')}</td></tr>
            <tr><td style="color: var(--text-muted);">Bollinger Upper</td><td class="text-right text-mono font-bold">₹${indicators.bb_upper?.toLocaleString('en-IN')}</td></tr>
            <tr><td style="color: var(--text-muted);">Bollinger Lower</td><td class="text-right text-mono font-bold">₹${indicators.bb_lower?.toLocaleString('en-IN')}</td></tr>
            <tr><td style="color: var(--text-muted);">Volatility (20d)</td><td class="text-right text-mono font-bold">${indicators.volatility}%</td></tr>
            <tr><td style="color: var(--text-muted);">Momentum (20d)</td><td class="text-right text-mono font-bold ${indicators.momentum >= 0 ? 'text-success' : 'text-danger'}">${indicators.momentum > 0 ? '+' : ''}${indicators.momentum}%</td></tr>
        </table>
    `;
    
    // Signals
    if (indicators.signals && indicators.signals.length) {
        html += '<div style="margin-top: 16px;"><div style="font-size: 0.8rem; font-weight: 600; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase;">SIGNALS</div><ul class="signal-list">';
        
        indicators.signals.forEach(sig => {
            const badgeClass = sig.action === 'BUY' ? 'buy' : sig.action === 'SELL' ? 'sell' : 'hold';
            html += `
                <li class="signal-item">
                    <span class="signal-indicator">${sig.indicator}: ${sig.signal}</span>
                    <span class="signal-badge ${badgeClass}">${sig.action}</span>
                </li>`;
        });
        
        html += '</ul></div>';
    }
    
    container.innerHTML = html;
}
