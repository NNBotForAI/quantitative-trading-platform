"""
OKX Adapter for Quantitative Trading Platform
Supports real-time price queries and historical data
Based on Backtrader pattern
"""

import requests
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from .base_adapter import BaseAdapter
from data_interface_framework import MarketData, Order, Position, AssetType


class OKXAdapter(BaseAdapter):
    """OKX exchange adapter based on Backtrader pattern"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "OKX"
        
        credentials = config.get("credentials", {})
        self.api_key = credentials.get("api_key", "")
        self.secret_key = credentials.get("secret_key", "")
        self.passphrase = credentials.get("passphrase", "")
        
        settings = config.get("settings", {})
        self.base_url = "https://www.okx.com"
        self.sandbox = settings.get("testnet", False)
        
    def _get_headers(self, extra_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Get OKX API headers"""
        headers = {
            'Content-Type': 'application/json',
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': '',  # Will be set when making requests
            'OK-ACCESS-TIMESTAMP': self._get_timestamp(),
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'x-simulated-trading': '1' if self.sandbox else '0'
        }
        
        if extra_headers:
            headers.update(extra_headers)
            
        return headers
    
    def _get_timestamp(self) -> str:
        """Generate OKX timestamp"""
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    def _create_signature(self, method: str, request_path: str, body: str = "") -> str:
        """Create OKX HMAC SHA256 signature"""
        import hmac
        import hashlib
        import base64
        
        timestamp = self._get_timestamp()
        sign_string = timestamp + method + request_path + body
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    async def connect(self) -> bool:
        """Connect to OKX exchange"""
        try:
            # Test public endpoint
            response = requests.get(
                f"{self.base_url}/api/v5/public/time",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                server_time = data.get('data', [{}])[0].get('ts', '')
                print(f"✓ {self.name} Server time: {server_time}")
                return True
            else:
                print(f"✗ {self.name} Connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ {self.name} Connection error: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from OKX"""
        print(f"✓ {self.name} Disconnected")
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Get real-time price - Public API (no auth required)"""
        try:
            # Public API doesn't need authentication
            response = requests.get(
                f"{self.base_url}/api/v5/market/ticker?instId={symbol}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    price = float(data['data'][0].get('last', 0))
                    print(f"✓ {self.name} {symbol}: ${price}")
                    return price
                    
        except Exception as e:
            print(f"✗ {self.name} Failed to get {symbol} price: {str(e)}")
            return None
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str = "1H",
        limit: int = 100
    ) -> List[MarketData]:
        """Get historical candle data - Public API (no auth required)"""
        try:
            # Public API doesn't need authentication
            response = requests.get(
                f"{self.base_url}/api/v5/market/candles?instId={symbol}&bar={timeframe}&limit={limit}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                market_data_list = []
                
                if 'data' in data and len(data['data']) > 0:
                    for candle in data['data']:
                        timestamp = datetime.fromtimestamp(int(candle[0]) / 1000.0)
                        
                        market_data = MarketData(
                            timestamp=timestamp,
                            symbol=symbol,
                            open_price=float(candle[1]),
                            high=float(candle[2]),
                            low=float(candle[3]),
                            close=float(candle[4]),
                            volume=float(candle[5]),
                            asset_type=AssetType.CRYPTO,
                            source="OKX"
                        )
                        market_data_list.append(market_data)
                    
                    print(f"✓ {self.name} Retrieved {len(market_data_list)} {symbol} historical data")
                    return market_data_list
                    
        except Exception as e:
            print(f"✗ {self.name} Failed to get {symbol} historical data: {str(e)}")
            return []
    
    async def place_order(self, order):
        """Place order - requires Trade permission"""
        print(f"✗ {self.name} Order placement requires Trade permission (current read-only API Key)")
        return {
            "order_id": None,
            "status": "failed",
            "message": "Requires Trade permission API Key"
        }
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order - requires Trade permission"""
        print(f"✗ {self.name} Cancel order requires Trade permission (current read-only API Key)")
        return False
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position - requires Trade permission"""
        print(f"✗ {self.name} Get position requires Trade permission (current read-only API Key)")
        return None
    
    async def get_all_positions(self) -> List[Position]:
        """Get all positions - requires Trade permission"""
        print(f"✗ {self.name} Get all positions requires Trade permission (current read-only API Key)")
        return []
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balance - requires Trade permission"""
        print(f"✗ {self.name} Get account balance requires Trade permission (current read-only API Key)")
        return {"cash": 0, "equity": 0}


# Test code
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # OKX config
        okx_config = {
            "name": "OKX",
            "type": "crypto_okx",
            "asset_type": "crypto",
            "enabled": True,
            "credentials": {
                "api_key": "da7e47af-4bb0-400d-b01c-3aa299279629",
                "secret_key": "9237CEEF04C1501D7BA4BFCCBB65200",
                "passphrase": "5683@Sjtu"
            },
            "settings": {
                "exchange": "okx",
                "testnet": True
            }
        }
        
        adapter = OKXAdapter(okx_config)
        
        # Test connection
        connected = await adapter.connect()
        
        if connected:
            # Test BTC price
            btc_price = await adapter.get_price("BTC-USDT")
            print(f"\nBTC price: ${btc_price}")
            
            # Test historical data
            historical = await adapter.get_historical_data("BTC-USDT", "1H", 3)
            print(f"Historical data count: {len(historical)}")
            
        else:
            print("OKX connection failed")
    
    asyncio.run(main())