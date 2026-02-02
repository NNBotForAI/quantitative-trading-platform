// Dashboard JavaScript
// Inspired by TradingView and QuantConnect interactive features

let priceChart = null;
let currentPrice = 0;
let marketData = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    updateTime();
    loadMarketData();
    loadPortfolioSummary();
    loadRiskStatus();
    
    // Auto-refresh every 30 seconds
    setInterval(updateTime, 1000);
    setInterval(loadMarketData, 30000);
    setInterval(loadRiskStatus, 60000);
});

// Initialize Chart.js chart (TradingView-style)
function initializeChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '价格',
                data: [],
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }, {
                label: 'SMA 10',
                data: [],
                borderColor: '#ffc107',
                borderWidth: 1,
                fill: false,
                hidden: true
            }, {
                label: 'SMA 30',
                data: [],
                borderColor: '#28a745',
                borderWidth: 1,
                fill: false,
                hidden: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

// Load market data from API
async function loadMarketData() {
    const symbol = document.getElementById('symbolSelect').value;
    const timeframe = document.getElementById('timeframeSelect').value;
    
    try {
        const response = await fetch(`/api/market/data?symbol=${symbol}&timeframe=${timeframe}&limit=100`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Error loading market data:', data.error);
            return;
        }
        
        marketData = data.data;
        updateChart(marketData);
        updateMarketDisplay(marketData);
        loadTradingSignals(symbol);
        
    } catch (error) {
        console.error('Error loading market data:', error);
        document.getElementById('marketDataDisplay').innerHTML = 
            '<p class="text-danger">加载失败</p>';
    }
}

// Update price chart
function updateChart(data) {
    if (!priceChart) return;
    
    // Sort data by timestamp
    const sortedData = data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    // Extract labels and prices
    const labels = sortedData.map(d => new Date(d.timestamp).toLocaleTimeString());
    const prices = sortedData.map(d => d.close);
    
    // Calculate SMAs
    const sma10 = calculateSMA(prices, 10);
    const sma30 = calculateSMA(prices, 30);
    
    // Update chart data
    priceChart.data.labels = labels;
    priceChart.data.datasets[0].data = prices;
    priceChart.data.datasets[1].data = sma10;
    priceChart.data.datasets[2].data = sma30;
    
    priceChart.update();
    
    // Update current price
    if (prices.length > 0) {
        currentPrice = prices[prices.length - 1];
    }
    
    // Update indicator values
    if (sma10.length > 0) {
        document.getElementById('sma10Value').textContent = 
            '$' + sma10[sma10.length - 1].toFixed(2);
    }
    if (sma30.length > 0) {
        document.getElementById('sma30Value').textContent = 
            '$' + sma30[sma30.length - 1].toFixed(2);
    }
    
    // Calculate and display RSI
    const rsi = calculateRSI(prices, 14);
    if (rsi.length > 0) {
        const lastRSI = rsi[rsi.length - 1];
        document.getElementById('rsiValue').textContent = lastRSI.toFixed(2);
        
        // Color code RSI
        const rsiElement = document.getElementById('rsiValue');
        if (lastRSI > 70) {
            rsiElement.className = 'h4 text-danger';
        } else if (lastRSI < 30) {
            rsiElement.className = 'h4 text-success';
        } else {
            rsiElement.className = 'h4 text-info';
        }
    }
}

// Update market data display
function updateMarketDisplay(data) {
    if (data.length === 0) {
        document.getElementById('marketDataDisplay').innerHTML = 
            '<p class="text-muted">无数据</p>';
        return;
    }
    
    const latest = data[data.length - 1];
    const previous = data[data.length - 2] || latest;
    const change = latest.close - previous.close;
    const changePercent = (change / previous.close) * 100;
    
    const changeClass = change >= 0 ? 'text-success' : 'text-danger';
    const changeIcon = change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
    
    document.getElementById('marketDataDisplay').innerHTML = `
        <div class="h3">${latest.close.toFixed(2)}</div>
        <div class="${changeClass}">
            <i class="fas ${changeIcon}"></i> 
            ${Math.abs(change).toFixed(2)} (${changePercent.toFixed(2)}%)
        </div>
        <div class="row mt-3">
            <div class="col-4">
                <small class="text-muted">最高</small>
                <div>$${latest.high.toFixed(2)}</div>
            </div>
            <div class="col-4">
                <small class="text-muted">最低</small>
                <div>$${latest.low.toFixed(2)}</div>
            </div>
            <div class="col-4">
                <small class="text-muted">成交量</small>
                <div>${(latest.volume / 1000).toFixed(1)}K</div>
            </div>
        </div>
    `;
}

// Load trading signals
async function loadTradingSignals(symbol) {
    try {
        const response = await fetch(`/api/signals?symbol=${symbol}`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Error loading signals:', data.error);
            return;
        }
        
        updateSignalsDisplay(data.signals);
        
    } catch (error) {
        console.error('Error loading trading signals:', error);
        document.getElementById('signalsDisplay').innerHTML = 
            '<p class="text-danger">加载信号失败</p>';
    }
}

// Update signals display
function updateSignalsDisplay(signals) {
    const container = document.getElementById('signalsDisplay');
    
    if (signals.length === 0) {
        container.innerHTML = '<p class="text-muted">无交易信号</p>';
        return;
    }
    
    let html = '';
    signals.forEach(signal => {
        const badgeClass = signal.action === 'BUY' ? 'bg-success' : 'bg-danger';
        const icon = signal.action === 'BUY' ? 'fa-arrow-up' : 'fa-arrow-down';
        
        html += `
            <div class="alert ${badgeClass} alert-dismissible fade show" role="alert">
                <strong><i class="fas ${icon}"></i> ${signal.type}</strong><br>
                ${signal.action} - ${signal.strength}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Load portfolio summary
async function loadPortfolioSummary() {
    try {
        const response = await fetch('/api/portfolio/summary');
        const data = await response.json();
        
        if (data.positions) {
            const positions = data.positions;
            
            document.getElementById('initialCapital').textContent = 
                '$' + positions.initial_capital.toFixed(2);
            document.getElementById('currentValue').textContent = 
                '$' + positions.portfolio_value.toFixed(2);
            
            const totalPnl = positions.portfolio_value - positions.initial_capital;
            const returnPercent = (totalPnl / positions.initial_capital) * 100;
            
            const pnlClass = totalPnl >= 0 ? 'text-success' : 'text-danger';
            document.getElementById('totalPnl').className = 'fw-bold ' + pnlClass;
            document.getElementById('totalPnl').textContent = 
                (totalPnl >= 0 ? '+' : '') + '$' + totalPnl.toFixed(2);
            
            const returnClass = returnPercent >= 0 ? 'text-success' : 'text-danger';
            document.getElementById('returnPercent').className = 'fw-bold ' + returnClass;
            document.getElementById('returnPercent').textContent = 
                (returnPercent >= 0 ? '+' : '') + returnPercent.toFixed(2) + '%';
        }
        
    } catch (error) {
        console.error('Error loading portfolio summary:', error);
    }
}

// Load risk status
async function loadRiskStatus() {
    try {
        const response = await fetch('/api/risk/status');
        const data = await response.json();
        
        if (data.error) {
            console.error('Error loading risk status:', data.error);
            return;
        }
        
        // Update risk indicators
        const riskPercent = data.portfolio_risk.risk_percent;
        const exposurePercent = data.portfolio_risk.exposure_percent;
        const alert24h = data.alerts_24h.total;
        
        document.getElementById('riskPercent').textContent = riskPercent.toFixed(2) + '%';
        document.getElementById('riskProgressBar').style.width = riskPercent + '%';
        
        document.getElementById('exposurePercent').textContent = exposurePercent.toFixed(2) + '%';
        document.getElementById('exposureProgressBar').style.width = exposurePercent + '%';
        
        document.getElementById('alert24h').textContent = alert24h;
        
        // Color code risk level
        if (riskPercent > 10) {
            document.getElementById('riskProgressBar').className = 'progress-bar bg-danger';
        } else if (riskPercent > 5) {
            document.getElementById('riskProgressBar').className = 'progress-bar bg-warning';
        } else {
            document.getElementById('riskProgressBar').className = 'progress-bar bg-success';
        }
        
    } catch (error) {
        console.error('Error loading risk status:', error);
    }
}

// Toggle indicator visibility
function toggleIndicator(indicator) {
    if (!priceChart) return;
    
    if (indicator === 'sma') {
        priceChart.data.datasets[1].hidden = !priceChart.data.datasets[1].hidden;
        priceChart.data.datasets[2].hidden = !priceChart.data.datasets[2].hidden;
    }
    
    priceChart.update();
}

// Open buy modal
function openBuyModal() {
    const symbol = document.getElementById('symbolSelect').value;
    document.getElementById('buySymbol').value = symbol;
    
    // Update estimated amount when quantity changes
    document.getElementById('buyQuantity').addEventListener('input', updateBuyEstimate);
    
    const modal = new bootstrap.Modal(document.getElementById('buyModal'));
    modal.show();
}

// Open sell modal
function openSellModal() {
    const symbol = document.getElementById('symbolSelect').value;
    document.getElementById('sellSymbol').value = symbol;
    
    // Update estimated amount when quantity changes
    document.getElementById('sellQuantity').addEventListener('input', updateSellEstimate);
    
    const modal = new bootstrap.Modal(document.getElementById('sellModal'));
    modal.show();
}

// Update buy estimate
function updateBuyEstimate() {
    const quantity = parseFloat(document.getElementById('buyQuantity').value) || 0;
    const estimate = quantity * currentPrice;
    document.getElementById('buyEstimate').value = '$' + estimate.toFixed(2);
}

// Update sell estimate
function updateSellEstimate() {
    const quantity = parseFloat(document.getElementById('sellQuantity').value) || 0;
    const estimate = quantity * currentPrice;
    document.getElementById('sellEstimate').value = '$' + estimate.toFixed(2);
}

// Submit buy order
async function submitBuyOrder() {
    const symbol = document.getElementById('buySymbol').value;
    const quantity = parseFloat(document.getElementById('buyQuantity').value);
    const strategy = document.getElementById('buyExecutionStrategy').value;
    
    if (isNaN(quantity) || quantity <= 0) {
        alert('请输入有效的数量');
        return;
    }
    
    try {
        const response = await fetch('/api/strategy/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                side: 'buy',
                quantity: quantity,
                execution_strategy: strategy
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('订单创建成功！订单ID: ' + data.order_id);
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('buyModal'));
            modal.hide();
            
            // Reload portfolio
            loadPortfolioSummary();
        } else {
            alert('订单创建失败: ' + data.error);
        }
        
    } catch (error) {
        console.error('Error creating buy order:', error);
        alert('订单创建失败');
    }
}

// Submit sell order
async function submitSellOrder() {
    const symbol = document.getElementById('sellSymbol').value;
    const quantity = parseFloat(document.getElementById('sellQuantity').value);
    const strategy = document.getElementById('sellExecutionStrategy').value;
    
    if (isNaN(quantity) || quantity <= 0) {
        alert('请输入有效的数量');
        return;
    }
    
    try {
        const response = await fetch('/api/strategy/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                side: 'sell',
                quantity: quantity,
                execution_strategy: strategy
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('订单创建成功！订单ID: ' + data.order_id);
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('sellModal'));
            modal.hide();
            
            // Reload portfolio
            loadPortfolioSummary();
        } else {
            alert('订单创建失败: ' + data.error);
        }
        
    } catch (error) {
        console.error('Error creating sell order:', error);
        alert('订单创建失败');
    }
}

// Update current time
function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = 
        now.toLocaleString('zh-CN');
}

// Technical indicator calculations
function calculateSMA(prices, period) {
    const sma = [];
    for (let i = 0; i < prices.length; i++) {
        if (i < period - 1) {
            sma.push(null);
        } else {
            let sum = 0;
            for (let j = 0; j < period; j++) {
                sum += prices[i - j];
            }
            sma.push(sum / period);
        }
    }
    return sma;
}

function calculateRSI(prices, period) {
    const rsi = [];
    for (let i = 1; i < prices.length; i++) {
        if (i < period) {
            rsi.push(null);
            continue;
        }
        
        let gains = 0;
        let losses = 0;
        
        for (let j = 0; j < period; j++) {
            const change = prices[i - j] - prices[i - j - 1];
            if (change > 0) {
                gains += change;
            } else {
                losses += Math.abs(change);
            }
        }
        
        const avgGain = gains / period;
        const avgLoss = losses / period;
        
        if (avgLoss === 0) {
            rsi.push(100);
        } else {
            const rs = avgGain / avgLoss;
            rsi.push(100 - (100 / (1 + rs)));
        }
    }
    return rsi;
}