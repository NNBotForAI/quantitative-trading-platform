"""
Base Adapter for Quantitative Trading Platform
Provides common interface for all data source adapters
"""

from data_interface_framework import DataSourceAdapter, MarketData, Order, Position, AssetType
from typing import Dict, List, Optional
import requests
from datetime import datetime


class BaseAdapter(DataSourceAdapter):
    """Base adapter class"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = config.get("name", "Base")
        self.config = config
        
    def _get_headers(self) -> Dict[str, str]:
        """Get common request headers"""
        return {
            'Content-Type': 'application/json'
        }
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Get price - implement in subclass"""
        raise NotImplementedError(f"{self.name}.get_price not implemented")
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str = "1H",
        limit: int = 100
    ) -> List[MarketData]:
        """Get historical data - implement in subclass"""
        raise NotImplementedError(f"{self.name}.get_historical_data not implemented")