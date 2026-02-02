"""
Stable Web Interface for Quantitative Trading Platform
Using direct app reference to ensure component access
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from typing import Dict, List
import pandas as pd
from datetime import datetime
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from adapters import OKXAdapter
from strategies import DualMACrossStrategy, MACDStrategy
from backtest import BacktestEngine, PerformanceAnalyzer
from risk import PositionManager, RiskMonitor, RiskRulesEngine
from trading import OrderManager, ExecutionEngine, ExecutionAlgorithm


class TradingPlatformWeb:
    """
    Web Platform - Main web interface for quantitative trading
    Inspired by TradingView (UI) and QuantConnect (features)
    """
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize components at class level
        self._initialize_components()
        
        # Configure routes
        self._configure_routes()
        
        print("✓ Web平台初始化完成")
        print("  基于成熟交易平台UI设计:")
        print("  - TradingView: 图表可视化")
        print("  - QuantConnect: 策略管理")
        print("  - Quantopian: 回测分析")
    
    def _initialize_components(self):
        """Initialize all platform components"""
        # Initialize OKX adapter
        okx_config = {
            "name": "OKX",
            "type": "crypto_okx",
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
        
        self.okx_adapter = OKXAdapter(okx_config)
        self.position_manager = PositionManager(initial_capital=100000.0)
        
        # Initialize risk management
        risk_rules = RiskRulesEngine()
        risk_rules.create_default_rules()
        self.risk_monitor = RiskMonitor(self.position_manager, risk_rules)
        
        # Initialize order management
        self.order_manager = OrderManager()
        self.execution_engine = ExecutionEngine()
        
        print("✓ 所有组件初始化完成")
    
    def _configure_routes(self):
        """Configure all API routes"""
        
        # Main page
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        # Dashboard
        @self.app.route('/dashboard')
        def dashboard():
            return render_template('dashboard.html')
        
        # Strategy Management
        @self.app.route('/strategies')
        def strategies():
            return render_template('strategies.html')
        
        # Backtesting
        @self.app.route('/backtest')
        def backtest():
            return render_template('backtest.html')
        
        # Risk Management
        @self.app.route('/risk')
        def risk():
            return render_template('risk.html')
        
        # Order Management
        @self.app.route('/orders')
        def orders():
            return render_template('orders.html')
        
        # API Routes
        
        # Health check
        @self.app.route('/api/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat()
            })
        
        # Market Data
        @self.app.route('/api/market/data', methods=['GET'])
        def get_market_data():
            """Get current market data"""
            try:
                symbol = request.args.get('symbol', 'BTC-USDT')
                timeframe = request.args.get('timeframe', '1H')
                limit = int(request.args.get('limit', 100))
                
                if not self.okx_adapter:
                    return jsonify({'error': 'Data adapter not initialized'}), 500
                
                # Get historical data
                data = asyncio.run(self.okx_adapter.get_historical_data(
                    symbol, timeframe, limit
                ))
                
                # Convert to list for JSON serialization
                data_list = [{
                    'timestamp': d.timestamp.isoformat(),
                    'open': d.open,
                    'high': d.high,
                    'low': d.low,
                    'close': d.close,
                    'volume': d.volume
                } for d in data]
                
                return jsonify({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'data': data_list
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Strategy Analysis
        @self.app.route('/api/strategy/analyze', methods=['POST'])
        def analyze_strategy():
            """Analyze strategy performance"""
            try:
                data = request.json
                
                symbol = data.get('symbol', 'BTC-USDT')
                strategy = data.get('strategy', 'dual_ma')
                params = data.get('params', {})
                
                if not self.okx_adapter:
                    return jsonify({'error': 'Data adapter not initialized'}), 500
                
                # Get market data
                historical_data = asyncio.run(self.okx_adapter.get_historical_data(
                    symbol, '1H', 200
                ))
                
                # Convert to DataFrame
                df = pd.DataFrame([{
                    'datetime': d.timestamp,
                    'open': d.open,
                    'high': d.high,
                    'low': d.low,
                    'close': d.close,
                    'volume': d.volume
                } for d in historical_data])
                
                df.set_index('datetime', inplace=True)
                df.sort_index(inplace=True)
                
                # Run backtest
                if strategy == 'dual_ma':
                    from backtest import DualMAStrategyWrapper
                    engine = BacktestEngine()
                    engine.add_strategy(
                        DualMAStrategyWrapper,
                        short_period=params.get('short_period', 10),
                        long_period=params.get('long_period', 30)
                    )
                elif strategy == 'macd':
                    from backtest import MACDStrategyWrapper
                    engine = BacktestEngine()
                    engine.add_strategy(
                        MACDStrategyWrapper,
                        fast_period=params.get('fast_period', 12),
                        slow_period=params.get('slow_period', 26),
                        signal_period=params.get('signal_period', 9)
                    )
                else:
                    return jsonify({'error': 'Unknown strategy'}), 400
                
                from backtest.engine import DataFeed
                data_feed = DataFeed(dataname=df)
                engine.add_data(data_feed)
                
                engine.set_commission(0.001)
                
                # Add analyzers
                from backtest.analyzers import create_analyzers
                create_analyzers(engine.cerebro)
                
                # Run backtest
                results = engine.run()
                
                if results:
                    analyzer = PerformanceAnalyzer(engine.cerebro, engine.results)
                    summary = analyzer.get_summary()

                    return jsonify({
                        'success': True,
                        'summary': {
                            'total_return': summary['total_return'],
                            'sharpe_ratio': summary['sharpe_ratio'],
                            'max_drawdown': summary['drawdown'].get('max_drawdown', 0),
                            'total_trades': summary['trades'].get('total', {}).get('total', 0)
                        }
                    })
                else:
                    return jsonify({'error': 'Backtest failed'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Risk Monitor
        @self.app.route('/api/risk/status', methods=['GET'])
        def get_risk_status():
            """Get current risk status"""
            try:
                if not self.risk_monitor:
                    return jsonify({'error': 'Risk monitor not initialized'}), 500
                
                # Check risk
                self.risk_monitor.check_risk()
                
                # Get summary
                summary = self.risk_monitor.get_risk_summary()
                
                return jsonify(summary)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Portfolio Summary
        @self.app.route('/api/portfolio/summary', methods=['GET'])
        def get_portfolio_summary():
            """Get portfolio summary"""
            try:
                summaries = {}
                
                if self.position_manager:
                    summaries['positions'] = self.position_manager.get_summary()
                
                if self.order_manager:
                    summaries['orders'] = self.order_manager.get_portfolio_summary()
                
                if self.risk_monitor:
                    summaries['risk'] = self.risk_monitor.get_risk_summary()
                
                return jsonify(summaries)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Create Order
        @self.app.route('/api/orders/create', methods=['POST'])
        def create_order():
            """Create new order"""
            try:
                data = request.json
                
                if not self.order_manager:
                    return jsonify({'error': 'Order manager not initialized'}), 500
                
                from trading import OrderType, OrderSide
                
                order = self.order_manager.create_order(
                    symbol=data.get('symbol', 'BTC-USDT'),
                    side=OrderSide.BUY if data.get('side') == 'buy' else OrderSide.SELL,
                    order_type=OrderType.MARKET if data.get('type') == 'market' else OrderType.LIMIT,
                    quantity=float(data.get('quantity', 0)),
                    price=float(data.get('price', 0)) if data.get('price') else None
                )
                
                return jsonify({
                    'success': True,
                    'order_id': order.id,
                    'status': order.status.value
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Get Orders
        @self.app.route('/api/orders', methods=['GET'])
        def get_orders():
            """Get all orders"""
            try:
                if not self.order_manager:
                    return jsonify({'error': 'Order manager not initialized'}), 500
                
                orders = self.order_manager.get_order_history()
                
                orders_list = [{
                    'id': o.id,
                    'symbol': o.symbol,
                    'side': o.side.value,
                    'type': o.order_type.value,
                    'quantity': o.quantity,
                    'price': o.price,
                    'filled': o.filled_quantity,
                    'status': o.status.value,
                    'timestamp': o.timestamp
                } for o in orders]
                
                return jsonify({'orders': orders_list})
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Execute Strategy
        @self.app.route('/api/strategy/execute', methods=['POST'])
        def execute_strategy():
            """Execute strategy with order"""
            try:
                data = request.json
                
                if not self.execution_engine:
                    return jsonify({'error': 'Execution engine not initialized'}), 500
                
                if not self.order_manager:
                    return jsonify({'error': 'Order manager not initialized'}), 500
                
                if not self.okx_adapter:
                    return jsonify({'error': 'Data adapter not initialized'}), 500
                
                # Create order
                from trading import OrderType, OrderSide
                
                order = self.order_manager.create_order(
                    symbol=data.get('symbol', 'BTC-USDT'),
                    side=OrderSide.BUY if data.get('side') == 'buy' else OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=float(data.get('quantity', 0))
                )
                
                # Get market data
                historical_data = asyncio.run(self.okx_adapter.get_historical_data(
                    data.get('symbol', 'BTC-USDT'), '1H', 100
                ))
                
                df = pd.DataFrame([{
                    'datetime': d.timestamp,
                    'open': d.open,
                    'high': d.high,
                    'low': d.low,
                    'close': d.close,
                    'volume': d.volume
                } for d in historical_data])
                
                # Execute with strategy
                strategy_name = data.get('execution_strategy', 'TWAP')
                
                if strategy_name == 'TWAP':
                    exec_strategy = ExecutionAlgorithm.TWAP
                elif strategy_name == 'VWAP':
                    exec_strategy = ExecutionAlgorithm.VWAP
                else:
                    exec_strategy = ExecutionAlgorithm.MIN_SLIPPAGE
                
                child_orders = self.execution_engine.execute_order_with_strategy(
                    order, exec_strategy, df
                )
                
                return jsonify({
                    'success': True,
                    'order_id': order.id,
                    'child_orders': len(child_orders),
                    'strategy': strategy_name
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Trading Signals
        @self.app.route('/api/signals', methods=['GET'])
        def get_signals():
            """Get current trading signals"""
            try:
                symbol = request.args.get('symbol', 'BTC-USDT')
                
                if not self.okx_adapter:
                    return jsonify({'error': 'Data adapter not initialized'}), 500
                
                # Get recent data
                historical_data = asyncio.run(self.okx_adapter.get_historical_data(
                    symbol, '1H', 50
                ))
                
                if len(historical_data) < 30:
                    return jsonify({'error': 'Insufficient data'}), 400
                
                # Calculate indicators
                df = pd.DataFrame([{
                    'datetime': d.timestamp,
                    'close': d.close
                } for d in historical_data])
                
                df['sma_10'] = df['close'].rolling(10).mean()
                df['sma_30'] = df['close'].rolling(30).mean()
                df['rsi'] = self._calculate_rsi(df['close'], 14)
                
                latest = df.iloc[-1]
                
                signals = {
                    'symbol': symbol,
                    'current_price': latest['close'],
                    'sma_10': latest['sma_10'],
                    'sma_30': latest['sma_30'],
                    'rsi': latest['rsi'],
                    'signal': self._generate_signal(latest['sma_10'], latest['sma_30'], latest['rsi']),
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify(signals)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _generate_signal(self, sma_10, sma_30, rsi):
        """Generate trading signal based on indicators"""
        if sma_10 > sma_30 and rsi < 70:
            return 'BUY'
        elif sma_10 < sma_30 and rsi > 30:
            return 'SELL'
        else:
            return 'HOLD'
    
    def run(self):
        """Run the web server"""
        print("\n" + "=" * 60)
        print("启动量化交易平台")
        print("=" * 60)
        print(f"  Web界面: http://0.0.0.0:{self.port}")
        print(f"  API端点: http://0.0.0.0:{self.port}/api")
        print("=" * 60)
        
        self.app.run(host=self.host, port=self.port, debug=False, threaded=False)


# Factory function
def create_web_platform():
    """Create and configure web platform instance"""
    platform = TradingPlatformWeb()
    return platform


# Main execution
if __name__ == "__main__":
    platform = create_web_platform()
    platform.run()