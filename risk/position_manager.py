"""
Position Manager for Quantitative Trading Platform
Based on QuantConnect best practices
"""

from typing import Dict, List, Optional
from data_interface_framework import Position, Order, AssetType


class PositionManager:
    """
    Position Manager - Manages portfolio positions
    Based on QuantConnect Position Management
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        max_position_size: float = 0.2,  # Maximum 20% of portfolio per position
        max_risk_per_trade: float = 0.02  # Maximum 2% risk per trade
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_size = max_position_size
        self.max_risk_per_trade = max_risk_per_trade
        
        self.positions: Dict[str, Position] = {}
        self.open_orders: Dict[str, Order] = {}
        self.trades: List[Dict] = []
        
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        risk_amount: Optional[float] = None
    ) -> float:
        """
        Calculate position size based on risk rules
        """
        if risk_amount is None:
            risk_amount = self.current_capital * self.max_risk_per_trade
        
        # Calculate based on stop loss if provided
        if stop_loss_price and stop_loss_price != entry_price:
            risk_per_share = abs(entry_price - stop_loss_price)
            if risk_per_share > 0:
                shares = int(risk_amount / risk_per_share)
            else:
                shares = 0
        else:
            # Fixed risk percentage without stop loss
            shares = int((self.current_capital * self.max_position_size) / entry_price)
        
        # Ensure minimum position size
        shares = max(1, shares)
        
        # Apply maximum position size limit
        max_position_value = self.current_capital * self.max_position_size
        max_shares = int(max_position_value / entry_price)
        shares = min(shares, max_shares)
        
        return shares
    
    def open_position(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        quantity: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Position:
        """
        Open a new position
        """
        # Convert side to quantity sign
        qty = quantity if side == 'buy' else -quantity
        
        position = Position(
            symbol=symbol,
            quantity=qty,
            avg_entry_price=entry_price,
            current_price=entry_price,
            asset_type=self._detect_asset_type(symbol)
        )
        
        # Store stop loss and take profit (not in Position class)
        position.stop_loss = stop_loss
        position.take_profit = take_profit
        position.side = side
        
        self.positions[symbol] = position
        
        # Log trade
        self.trades.append({
            'symbol': symbol,
            'action': 'open',
            'side': side,
            'quantity': quantity,
            'price': entry_price,
            'timestamp': self._get_timestamp()
        })
        
        return position
    
    def close_position(self, symbol: str, exit_price: float) -> Optional[float]:
        """
        Close an existing position
        Returns profit/loss
        """
        if symbol not in self.positions:
            return 0.0
        
        position = self.positions[symbol]
        side = getattr(position, 'side', 'buy')
        
        # Calculate profit/loss
        if side == 'buy':
            profit_loss = (exit_price - position.avg_entry_price) * position.quantity
        else:  # sell
            profit_loss = (position.avg_entry_price - exit_price) * abs(position.quantity)
        
        # Update capital
        self.current_capital += profit_loss
        
        # Log trade
        self.trades.append({
            'symbol': symbol,
            'action': 'close',
            'side': side,
            'quantity': abs(position.quantity),
            'price': exit_price,
            'profit_loss': profit_loss,
            'timestamp': self._get_timestamp()
        })
        
        # Remove position
        del self.positions[symbol]
        
        return profit_loss
    
    def update_position_price(self, symbol: str, current_price: float):
        """
        Update current price for a position
        """
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position by symbol
        """
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """
        Get all open positions
        """
        return list(self.positions.values())
    
    def get_portfolio_value(self) -> float:
        """
        Calculate total portfolio value
        """
        total_exposure = 0.0
        
        # Calculate exposure
        for symbol, position in self.positions.items():
            side = getattr(position, 'side', 'buy')
            
            # Calculate exposure
            if side == 'buy':
                position_exposure = position.quantity * position.current_price
            else:
                position_exposure = abs(position.quantity) * position.current_price
            
            total_exposure += position_exposure
        
        # Add cash
        cash = self.current_capital - sum(
            pos.quantity * pos.avg_entry_price
            for pos in self.positions.values()
        )
        
        total_value = total_exposure + cash
        
        return total_value
    
    def get_portfolio_risk(self) -> Dict:
        """
        Calculate portfolio risk metrics
        """
        total_risk = 0.0
        total_exposure = 0.0
        
        for symbol, position in self.positions.items():
            # Calculate risk based on stop loss
            if position.stop_loss and position.quantity > 0:  # Long position only
                position_risk = (position.avg_entry_price - position.stop_loss) * position.quantity
                total_risk += max(0, position_risk)
            
            # Calculate exposure
            position_exposure = abs(position.quantity) * position.current_price
            total_exposure += position_exposure
        
        portfolio_value = self.get_portfolio_value()
        
        return {
            'total_risk': total_risk,
            'total_exposure': total_exposure,
            'portfolio_value': portfolio_value,
            'risk_percent': (total_risk / portfolio_value * 100) if portfolio_value > 0 else 0,
            'exposure_percent': (total_exposure / portfolio_value * 100) if portfolio_value > 0 else 0
        }
    
    def check_position_limits(self, symbol: str, quantity: float, price: float) -> bool:
        """
        Check if position size exceeds limits
        """
        # Check max position size
        position_value = quantity * price
        max_position_value = self.current_capital * self.max_position_size
        
        if position_value > max_position_value:
            return False
        
        # Check total exposure
        current_exposure = sum(
            pos.quantity * pos.current_price
            for pos in self.positions.values()
        )
        
        total_exposure = current_exposure + position_value
        max_exposure = self.current_capital * 0.5  # Maximum 50% total exposure
        
        if total_exposure > max_exposure:
            return False
        
        return True
    
    def _detect_asset_type(self, symbol: str) -> AssetType:
        """
        Detect asset type from symbol
        """
        if '-USDT' in symbol or '-USD' in symbol:
            return AssetType.CRYPTO
        else:
            return AssetType.STOCK
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_summary(self) -> Dict:
        """
        Get position manager summary
        """
        portfolio_risk = self.get_portfolio_risk()
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'portfolio_value': portfolio_risk['portfolio_value'],
            'total_positions': len(self.positions),
            'total_trades': len(self.trades),
            'total_risk': portfolio_risk['total_risk'],
            'risk_percent': portfolio_risk['risk_percent'],
            'exposure_percent': portfolio_risk['exposure_percent'],
            'win_rate': self._calculate_win_rate()
        }
    
    def _calculate_win_rate(self) -> float:
        """
        Calculate win rate from closed trades
        """
        closed_trades = [
            trade for trade in self.trades
            if trade['action'] == 'close'
        ]
        
        if len(closed_trades) == 0:
            return 0.0
        
        wins = sum(1 for trade in closed_trades if trade['profit_loss'] > 0)
        return (wins / len(closed_trades)) * 100