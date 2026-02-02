"""
Alpaca Adapter for Quantitative Trading Platform
Supports real-time stock price queries and historical data
Based on Backtrader pattern
"""

import requests
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from .base_adapter import BaseAdapter
from data_interface_framework import MarketData, Order, Position, AssetType


class AlpacaAdapter(BaseAdapter):
    """Alpaca stock exchange adapter based on Backtrader pattern"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "Alpaca"
        
        credentials = config.get("credentials", {})
        self.api_key = credentials.get("api_key", "")
        self.secret = credentials.get("secret", "")
        
        settings = config.get("settings", {})
        self.data_url = settings.get("data_url", "https://data.alpaca.markets/v2")
        self.trade_url = settings.get("trade_url", "https://paper-api.alpaca.markets/v2")
        self.paper_trading = settings.get("paper_trading", True)
        
    def _get_headers(self, extra_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Get Alpaca API headers"""
        headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret,
            'Content-Type': 'application/json'
        }
        
        if extra_headers:
            headers.update(extra_headers)
            
        return headers
    
    async def connect(self) -> bool:
        """Connect to Alpaca exchange"""
        try:
            response = requests.get(
                f"{self.trade_url}/account",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                cash = float(data.get('cash', 0))
                buying_power = float(data.get('buying_power', 0))
                status = data.get('status', 'Unknown')
                print(f"✓ {self.name} Account status: {status}")
                print(f"✓ {self.name} Cash: ${cash:,.2f}")
                print(f"✓ {self.name} Buying power: ${buying_power:,.2f}")
                return True
            else:
                print(f"✗ {self.name} Connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ {self.name} Connection error: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from Alpaca"""
        print(f"✓ {self.name} Disconnected")
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Get real-time stock price"""
        try:
            response = requests.get(
                f"{self.data_url}/stocks/{symbol}/snapshot",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'latestTrade' in data:
                    price = float(data['latestTrade'].get('p', 0))
                    print(f"✓ {self.name} {symbol}: ${price}")
                    return price
                    
        except Exception as e:
            print(f"✗ {self.name} Failed to get {symbol} price: {str(e)}")
            return None
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str = "day",
        limit: int = 100
    ) -> List[MarketData]:
        """Get historical candle data"""
        try:
            params = {
                'timeframe': timeframe,
                'limit': limit
            }
            
            response = requests.get(
                f"{self.data_url}/stocks/{symbol}/bars",
                headers=self._get_headers(),
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                market_data_list = []
                
                if 'bars' in data and len(data['bars']) > 0:
                    for bar in data['bars']:
                        timestamp = datetime.fromisoformat(bar['t'].replace('Z', '+00:00'))
                        
                        market_data = MarketData(
                            timestamp=timestamp,
                            symbol=symbol,
                            open_price=float(bar['o']),
                            high=float(bar['h']),
                            low=float(bar['l']),
                            close=float(bar['c']),
                            volume=float(bar['v']),
                            asset_type=AssetType.STOCK,
                            source="Alpaca"
                        )
                        market_data_list.append(market_data)
                    
                    print(f"✓ {self.name} Retrieved {len(market_data_list)} {symbol} historical data")
                    return market_data_list
                    
        except Exception as e:
            print(f"✗ {self.name} Failed to get {symbol} historical data: {str(e)}")
            return []
    
    async def place_order(self, order):
        """Place order"""
        try:
            order_data = {
                "symbol": order.symbol,
                "side": order.side,
                "type": "market",  # Market order
                "time_in_force": "day",
                "qty": int(order.quantity)
            }
            
            response = requests.post(
                f"{self.trade_url}/orders",
                headers=self._get_headers(),
                json=order_data,
                timeout=10
            )
            
            if response.status_code == 200 or response.status_code == 207:
                data = response.json()
                order_id = data.get('id', '')
                
                print(f"✓ {self.name} Order submitted: {order_id}")
                
                return {
                    "order_id": order_id,
                    "status": "success",
                    "message": "Order submitted"
                }
            else:
                error_msg = f"Order submission failed ({response.status_code})"
                print(f"✗ {self.name} {error_msg}")
                
                return {
                    "order_id": None,
                    "status": "failed",
                    "message": error_msg
                }
                    
        except Exception as e:
            print(f"✗ {self.name} Order failed: {str(e)}")
            
            return {
                "order_id": None,
                "status": "failed",
                "message": str(e)
            }
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        try:
            response = requests.delete(
                f"{self.trade_url}/orders/{order_id}",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200 or response.status_code == 204:
                print(f"✓ {self.name} Order canceled: {order_id}")
                return True
            else:
                print(f"✗ {self.name} Cancel order failed ({response.status_code})")
                return False
                
        except Exception as e:
            print(f"✗ {self.name} Cancel order failed: {str(e)}")
            return False
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position"""
        try:
            response = requests.get(
                f"{self.base_url}/positions/{symbol}",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if len(data) > 0:
                    position_data = data[0]
                    position = Position(
                        symbol=position_data.get('symbol', ''),
                        quantity=float(position_data.get('qty', 0)),
                        avg_entry_price=float(position_data.get('avg_entry_price', 0)),
                        current_price=float(position_data.get('current_price', 0)),
                        unrealized_pl=float(position_data.get('unrealized_pl', 0))
                    )
                    return position
            return None
                
        except Exception as e:
            print(f"✗ {self.name} Failed to get position for {symbol}: {str(e)}")
            return None
    
    async def get_all_positions(self) -> List[Position]:
        """Get all positions"""
        try:
            response = requests.get(
                f"{self.base_url}/positions",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                positions = []
                
                for position_data in data:
                    # Skip zero positions
                    if float(position_data.get('qty', 0)) == 0:
                        continue
                    
                    position = Position(
                        symbol=position_data.get('symbol', ''),
                        quantity=float(position_data.get('qty', 0)),
                        avg_entry_price=float(position_data.get('avg_entry_price', 0)),
                        current_price=float(position_data.get('current_price', 0)),
                        unrealized_pl=float(position_data.get('unrealized_pl', 0))
                    )
                    positions.append(position)
                
                return positions
            return []
                
        except Exception as e:
            print(f"✗ {self.name} Failed to get all positions: {str(e)}")
            return []
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            account_info = await self.get_account_info()
            
            if account_info:
                cash = float(account_info.get('cash', 0))
                equity = float(account_info.get('equity', 0))
                buying_power = float(account_info.get('buying_power', 0))
                
                return {
                    "cash": cash,
                    "equity": equity,
                    "buying_power": buying_power
                }
            else:
                return {"cash": 0, "equity": 0, "buying_power": 0}
                
        except Exception as e:
            print(f"✗ {self.name} Failed to get account balance: {str(e)}")
            return {"cash": 0, "equity": 0, "buying_power": 0}
    
    async def get_account_info(self) -> Optional[Dict]:
        """Get account info"""
        try:
            response = requests.get(
                f"{self.trade_url}/account",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"✗ {self.name} Failed to get account info")
                return None
                
        except Exception as e:
            print(f"✗ {self.name} Failed to get account info: {str(e)}")
            return None


# Test code
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Alpaca config
        alpaca_config = {
            "name": "Alpaca",
            "type": "stock_alpaca",
            "asset_type": "stock",
            "enabled": True,
            "credentials": {
                "api_key": "PKB52GFFLQBADPYIGURJPBJJPE",
                "secret": "6kXriG9VMYWhicqMdSvPWBZYG8XUoc9yTaa795iyHGXs"
            },
            "settings": {
                "base_url": "https://data.alpaca.markets/v2",
                "paper_trading": True
            }
        }
        
        adapter = AlpacaAdapter(alpaca_config)
        
        # Test connection
        connected = await adapter.connect()
        
        if connected:
            # Test AAPL price
            aapl_price = await adapter.get_price("AAPL")
            print(f"\nAAPL price: ${aapl_price}")
            
            # Test historical data
            historical = await adapter.get_historical_data("AAPL", "day", 3)
            print(f"Historical data count: {len(historical)}")
            
        else:
            print("Alpaca connection failed")
    
    asyncio.run(main())