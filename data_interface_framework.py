"""
灵活数据接口框架
支持多种数据源接入，提供统一的数据访问接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime
from enum import Enum
import json


class AssetType(Enum):
    """资产类型枚举"""
    CRYPTO = "crypto"
    STOCK = "stock"
    FOREX = "forex"
    FUTURES = "futures"
    OPTIONS = "options"


class DataSourceType(Enum):
    """数据源类型枚举"""
    EXCHANGE_API = "exchange_api"      # 交易所API（CCXT、Alpaca等）
    DATA_FEED = "data_feed"           # 数据供应商（Bloomberg、Yahoo Finance等）
    WEBSOCKET = "websocket"           # WebSocket实时数据
    DATABASE = "database"               # 历史数据库
    CUSTOM = "custom"                 # 自定义数据源


class MarketData:
    """
    统一市场数据格式
    所有数据源都必须转换为这个格式
    """
    
    def __init__(
        self,
        timestamp: datetime,
        symbol: str,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        asset_type: AssetType = AssetType.CRYPTO,
        source: str = None
    ):
        self.timestamp = timestamp
        self.symbol = symbol
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.asset_type = asset_type
        self.source = source
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "asset_type": self.asset_type.value,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MarketData':
        """从字典创建对象"""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            symbol=data["symbol"],
            open_price=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
            asset_type=AssetType(data.get("asset_type", AssetType.CRYPTO.value)),
            source=data.get("source")
        )


class Order:
    """
    统一订单格式
    """
    
    def __init__(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        order_type: str,  # 'market', 'limit', 'stop_loss', 'take_profit'
        quantity: float,
        price: Optional[float] = None,
        asset_type: AssetType = AssetType.CRYPTO,
        stop_price: Optional[float] = None,
        take_profit_price: Optional[float] = None,
        time_in_force: str = "GTC"  # GTC, IOC, FOK
    ):
        self.symbol = symbol
        self.side = side.lower()
        self.order_type = order_type.lower()
        self.quantity = quantity
        self.price = price
        self.asset_type = asset_type
        self.stop_price = stop_price
        self.take_profit_price = take_profit_price
        self.time_in_force = time_in_force
        self.order_id = None
        self.status = "pending"
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "type": self.order_type,
            "quantity": self.quantity,
            "price": self.price,
            "asset_type": self.asset_type.value,
            "stop_price": self.stop_price,
            "take_profit_price": self.take_profit_price,
            "time_in_force": self.time_in_force,
            "order_id": self.order_id,
            "status": self.status
        }


class Position:
    """
    统一仓位格式
    """
    
    def __init__(
        self,
        symbol: str,
        quantity: float,
        avg_entry_price: float,
        current_price: float,
        asset_type: AssetType = AssetType.CRYPTO
    ):
        self.symbol = symbol
        self.quantity = quantity
        self.avg_entry_price = avg_entry_price
        self.current_price = current_price
        self.asset_type = asset_type
        self.pnl = self._calculate_pnl()
        
    def _calculate_pnl(self) -> float:
        """计算未实现盈亏"""
        if self.quantity == 0:
            return 0.0
        if self.quantity > 0:  # 多头仓位
            return (self.current_price - self.avg_entry_price) * self.quantity
        else:  # 空头仓位
            return (self.avg_entry_price - self.current_price) * abs(self.quantity)
    
    def update_price(self, new_price: float):
        """更新当前价格"""
        self.current_price = new_price
        self.pnl = self._calculate_pnl()
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_entry_price": self.avg_entry_price,
            "current_price": self.current_price,
            "pnl": self.pnl,
            "asset_type": self.asset_type.value
        }


class DataSourceAdapter(ABC):
    """
    数据源适配器抽象基类
    所有数据源都必须实现这个接口
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.connected = False
        self.asset_type = self._detect_asset_type(config)
        
    @abstractmethod
    async def connect(self) -> bool:
        """连接到数据源"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def get_price(self, symbol: str) -> Optional[float]:
        """获取当前价格"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str,  # '1m', '5m', '1h', '1d' 等
        limit: int = 100
    ) -> List[MarketData]:
        """获取历史数据"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> Dict:
        """下单"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """获取仓位"""
        pass
    
    @abstractmethod
    async def get_all_positions(self) -> List[Position]:
        """获取所有仓位"""
        pass
    
    @abstractmethod
    async def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        pass
    
    def _detect_asset_type(self, config: Dict) -> AssetType:
        """从配置检测资产类型"""
        asset_type = config.get("asset_type", AssetType.CRYPTO.value)
        return AssetType(asset_type)


class DataSourceRegistry:
    """
    数据源注册表
    管理所有可用的数据源
    """
    
    def __init__(self):
        self._adapters: Dict[str, DataSourceAdapter] = {}
        self._adapter_configs: Dict[str, Dict] = {}
        
    def register_adapter(
        self,
        name: str,
        adapter_class: type,
        config: Dict
    ):
        """注册数据源适配器"""
        adapter = adapter_class(config)
        self._adapters[name] = adapter
        self._adapter_configs[name] = config
        print(f"✓ 注册数据源: {name} ({adapter_class.__name__})")
        
    def get_adapter(self, name: str) -> Optional[DataSourceAdapter]:
        """获取指定的数据源适配器"""
        return self._adapters.get(name)
        
    def list_adapters(self) -> List[str]:
        """列出所有注册的适配器"""
        return list(self._adapters.keys())
        
    async def connect_all(self) -> Dict[str, bool]:
        """连接所有数据源"""
        results = {}
        for name, adapter in self._adapters.items():
            try:
                success = await adapter.connect()
                results[name] = success
                status = "✓ 连接成功" if success else "✗ 连接失败"
                print(f"{status}: {name}")
            except Exception as e:
                results[name] = False
                print(f"✗ 连接失败 {name}: {str(e)}")
        return results
        
    async def disconnect_all(self):
        """断开所有数据源连接"""
        for name, adapter in self._adapters.items():
            try:
                await adapter.disconnect()
                print(f"✓ 断开连接: {name}")
            except Exception as e:
                print(f"✗ 断开连接失败 {name}: {str(e)}")


class UnifiedDataManager:
    """
    统一数据管理器
    提供统一的数据访问接口，支持多数据源
    """
    
    def __init__(self):
        self.registry = DataSourceRegistry()
        self.default_source = None
        self.data_cache = {}  # 缓存机制
        self.websocket_connections = {}  # WebSocket连接管理
        
    async def initialize(self, config: Dict):
        """从配置初始化"""
        # 注册所有数据源
        sources = config.get("data_sources", {})
        
        for source_name, source_config in sources.items():
            adapter_class = self._get_adapter_class(source_config.get("type"))
            if adapter_class:
                self.registry.register_adapter(source_name, adapter_class, source_config)
                
                # 设置默认数据源
                if source_config.get("default", False):
                    self.default_source = source_name
                    
        # 连接所有数据源
        if self._adapters_available():
            await self.registry.connect_all()
            
    def _get_adapter_class(self, adapter_type: str) -> Optional[type]:
        """根据类型获取适配器类"""
        # 这里根据类型动态导入对应的适配器
        # 实际实现中需要导入具体的适配器类
        from data_adapters import (
            CryptoCCXTAdapter,
            StockAlpacaAdapter,
            ForexOANDAAdapter,
            FuturesIBAdapter
        )
        
        adapter_map = {
            "crypto_ccxt": CryptoCCXTAdapter,
            "stock_alpaca": StockAlpacaAdapter,
            "forex_oanda": ForexOANDAAdapter,
            "futures_ib": FuturesIBAdapter
        }
        
        return adapter_map.get(adapter_type)
        
    def _adapters_available(self) -> bool:
        """检查是否有可用的适配器"""
        return len(self.registry.list_adapters()) > 0
        
    async def get_price(self, symbol: str, source: str = None) -> Optional[float]:
        """获取价格（支持指定数据源）"""
        source_name = source or self.default_source
        adapter = self.registry.get_adapter(source_name)
        
        if not adapter:
            print(f"✗ 未找到数据源: {source_name}")
            return None
            
        return await adapter.get_price(symbol)
        
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        source: str = None
    ) -> List[MarketData]:
        """获取历史数据"""
        source_name = source or self.default_source
        adapter = self.registry.get_adapter(source_name)
        
        if not adapter:
            print(f"✗ 未找到数据源: {source_name}")
            return []
            
        return await adapter.get_historical_data(symbol, timeframe, limit)
        
    async def place_order(self, order: Order, source: str = None) -> Dict:
        """下单"""
        source_name = source or self.default_source
        adapter = self.registry.get_adapter(source_name)
        
        if not adapter:
            print(f"✗ 未找到数据源: {source_name}")
            return {"error": "数据源不存在"}
            
        return await adapter.place_order(order)
        
    async def get_positions(self, source: str = None) -> List[Position]:
        """获取所有仓位"""
        source_name = source or self.default_source
        adapter = self.registry.get_adapter(source_name)
        
        if not adapter:
            print(f"✗ 未找到数据源: {source_name}")
            return []
            
        return await adapter.get_all_positions()
        
    def get_available_sources(self) -> List[str]:
        """获取所有可用的数据源"""
        return self.registry.list_adapters()
        
    async def subscribe_realtime(self, symbols: List[str], callback, source: str = None):
        """订阅实时数据（WebSocket）"""
        source_name = source or self.default_source
        adapter = self.registry.get_adapter(source_name)
        
        if not adapter:
            print(f"✗ 未找到数据源: {source_name}")
            return False
            
        # 如果适配器支持WebSocket，订阅实时数据
        if hasattr(adapter, 'subscribe_websocket'):
            await adapter.subscribe_websocket(symbols, callback)
            return True
        else:
            print(f"✗ 数据源 {source_name} 不支持WebSocket")
            return False


class DataSourceConfig:
    """
    数据源配置类
    支持灵活配置和数据源管理
    """
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "data_sources_config.json"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件不存在，创建默认配置: {self.config_file}")
            default_config = self._create_default_config()
            self.save_config(default_config)
            return default_config
            
    def _create_default_config(self) -> Dict:
        """创建默认配置"""
        return {
            "data_sources": {
                "binance_crypto": {
                    "type": "crypto_ccxt",
                    "asset_type": "crypto",
                    "enabled": False,
                    "default": False,
                    "credentials": {
                        "api_key": "",
                        "secret": ""
                    },
                    "settings": {
                        "exchange": "binance",
                        "testnet": True
                    }
                },
                "alpaca_stock": {
                    "type": "stock_alpaca",
                    "asset_type": "stock",
                    "enabled": False,
                    "default": False,
                    "credentials": {
                        "api_key": "",
                        "secret": ""
                    },
                    "settings": {
                        "base_url": "https://paper-api.alpaca.markets",
                        "paper_trading": True
                    }
                },
                "oanda_forex": {
                    "type": "forex_oanda",
                    "asset_type": "forex",
                    "enabled": False,
                    "default": False,
                    "credentials": {
                        "api_key": "",
                        "account_id": ""
                    },
                    "settings": {
                        "environment": "practice"
                    }
                }
            },
            "global_settings": {
                "cache_enabled": True,
                "cache_ttl": 300,
                "retry_attempts": 3,
                "timeout": 30
            }
        }
        
    def save_config(self, config: Dict = None):
        """保存配置"""
        config_to_save = config or self.config
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, indent=2, ensure_ascii=False)
        print(f"✓ 配置已保存: {self.config_file}")
        
    def add_data_source(self, name: str, config: Dict):
        """添加新的数据源"""
        if "data_sources" not in self.config:
            self.config["data_sources"] = {}
            
        self.config["data_sources"][name] = config
        self.save_config()
        
    def enable_data_source(self, name: str, enabled: bool = True):
        """启用/禁用数据源"""
        if "data_sources" in self.config and name in self.config["data_sources"]:
            self.config["data_sources"][name]["enabled"] = enabled
            self.save_config()
            
    def set_default_source(self, name: str):
        """设置默认数据源"""
        # 先取消所有默认设置
        for source in self.config.get("data_sources", {}).values():
            source["default"] = False
            
        # 设置新的默认数据源
        if name in self.config["data_sources"]:
            self.config["data_sources"][name]["default"] = True
            self.save_config()
            
    def get_enabled_sources(self) -> Dict[str, Dict]:
        """获取所有启用的数据源"""
        enabled = {}
        for name, config in self.config.get("data_sources", {}).items():
            if config.get("enabled", False):
                enabled[name] = config
        return enabled
        
    def get_default_source(self) -> Optional[str]:
        """获取默认数据源"""
        for name, config in self.config.get("data_sources", {}).items():
            if config.get("default", False):
                return name
        return None


# 使用示例
if __name__ == "__main__":
    async def main():
        # 1. 创建配置管理器
        config_manager = DataSourceConfig()
        
        # 2. 启用和配置数据源
        config_manager.enable_data_source("binance_crypto")
        config_manager.set_default_source("binance_crypto")
        
        # 3. 创建统一数据管理器
        data_manager = UnifiedDataManager()
        
        # 4. 初始化
        await data_manager.initialize(config_manager.config)
        
        # 5. 测试数据获取
        price = await data_manager.get_price("BTC/USDT")
        print(f"BTC/USDT 价格: {price}")
        
        # 6. 测试历史数据获取
        historical = await data_manager.get_historical_data("BTC/USDT", "1h", 10)
        print(f"获取到 {len(historical)} 条历史数据")
        
        # 7. 列出所有可用数据源
        sources = data_manager.get_available_sources()
        print(f"可用数据源: {sources}")
        
    asyncio.run(main())