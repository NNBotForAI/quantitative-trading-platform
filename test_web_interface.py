"""
Test Script for Quantitative Trading Platform Web Interface
"""

import sys
import os
import threading
import time
import asyncio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from web.web_platform import TradingPlatformWeb


def run_server():
    """Run the web server in a separate thread"""
    platform = TradingPlatformWeb(host='0.0.0.0', port=5000)
    platform.initialize_components()
    
    # Run the Flask app
    platform.app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


def test_api_endpoints():
    """Test API endpoints"""
    import requests
    import time
    
    # Wait for server to start
    time.sleep(2)
    
    base_url = "http://localhost:5000"
    
    print("Testing API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✓ Health check: PASSED")
        else:
            print(f"✗ Health check: FAILED - Status {response.status_code}")
    except Exception as e:
        print(f"✗ Health check: ERROR - {str(e)}")
    
    # Test market data endpoint
    try:
        response = requests.get(f"{base_url}/api/market/data?symbol=BTC-USDT&timeframe=1H&limit=10")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                print("✓ Market data: PASSED")
            else:
                print("✗ Market data: No data returned")
        else:
            print(f"✗ Market data: FAILED - Status {response.status_code}")
    except Exception as e:
        print(f"✗ Market data: ERROR - {str(e)}")
    
    # Test risk status endpoint
    try:
        response = requests.get(f"{base_url}/api/risk/status")
        if response.status_code == 200:
            data = response.json()
            if 'alerts_24h' in data:
                print("✓ Risk status: PASSED")
            else:
                print("✗ Risk status: Invalid response format")
        else:
            print(f"✗ Risk status: FAILED - Status {response.status_code}")
    except Exception as e:
        print(f"✗ Risk status: ERROR - {str(e)}")


if __name__ == "__main__":
    print("Starting Quantitative Trading Platform Web Interface Test")
    print("=" * 60)
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\nWeb interface is ready!")
    print("Access at: http://localhost:5000")
    print("API endpoints available:")
    print("  - http://localhost:5000/api/health")
    print("  - http://localhost:5000/api/market/data?symbol=BTC-USDT")
    print("  - http://localhost:5000/api/risk/status")
    print("  - http://localhost:5000/api/portfolio/summary")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")