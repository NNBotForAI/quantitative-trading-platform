#!/bin/bash
# Quick deployment script for Quantitative Trading Platform

set -e

echo "=========================================="
echo "QUANTITATIVE TRADING PLATFORM"
echo "Quick Deployment & Launch"
echo "=========================================="
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Check Python
echo "Checking Python version..."
python3 --version

# Install dependencies (if needed)
echo ""
echo "Checking dependencies..."
pip3 list | grep -E "(flask|pandas|numpy|backtrader)" || {
    echo "Installing missing dependencies..."
    pip3 install flask pandas numpy backtrader requests
}

# Run quick component tests
echo ""
echo "Running quick component tests..."
python3 -c "
import sys
sys.path.insert(0, '.')
from web.web_platform import TradingPlatformWeb
print('✓ All imports successful')
platform = TradingPlatformWeb()
platform.initialize_components()
print('✓ Platform initialized')
"

# Start the platform
echo ""
echo "=========================================="
echo "Starting Trading Platform..."
echo "=========================================="
echo ""
echo "Access URLs:"
echo "  Dashboard: http://localhost:5000/dashboard"
echo "  Strategies: http://localhost:5000/strategies"
echo "  Backtest: http://localhost:5000/backtest"
echo "  Risk Management: http://localhost:5000/risk"
echo "  Orders: http://localhost:5000/orders"
echo ""
echo "API Endpoints:"
echo "  Health: http://localhost:5000/api/health"
echo "  Market Data: http://localhost:5000/api/market/data"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 -m flask run --host=0.0.0.0 --port=5000