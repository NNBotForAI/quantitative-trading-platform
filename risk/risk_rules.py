"""
Risk Rules Engine for Quantitative Trading Platform
Based on QuantConnect risk management best practices
"""

from typing import Dict, List, Optional, Callable
from data_interface_framework import Position, Order


class RiskRule:
    """
    Base class for risk rules
    """
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.violations: List[Dict] = []
    
    def check(self, context: Dict) -> bool:
        """
        Check if rule is violated
        Returns True if violated, False if passed
        """
        raise NotImplementedError(f"{self.name}.check not implemented")
    
    def add_violation(self, reason: str, details: Dict = None):
        """Add violation record"""
        from datetime import datetime
        
        violation = {
            'rule': self.name,
            'reason': reason,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.violations.append(violation)
    
    def get_violations(self) -> List[Dict]:
        """Get all violations"""
        return self.violations
    
    def clear_violations(self):
        """Clear all violations"""
        self.violations = []
    
    def reset(self):
        """Reset rule state"""
        self.clear_violations()


class MaxPositionSizeRule(RiskRule):
    """
    Rule: Maximum position size
    Prevents opening positions larger than a specified size
    """
    
    def __init__(self, max_size: float):
        super().__init__("MaxPositionSizeRule")
        self.max_size = max_size
    
    def check(self, context: Dict) -> bool:
        """
        Check if position size exceeds maximum
        """
        position_size = context.get('position_size', 0)
        symbol = context.get('symbol', '')
        
        if position_size > self.max_size:
            self.add_violation(
                f"Position size {position_size} exceeds maximum {self.max_size}",
                {'symbol': symbol, 'position_size': position_size}
            )
            return True
        
        return False


class MaxDailyLossRule(RiskRule):
    """
    Rule: Maximum daily loss
    Prevents excessive daily losses
    """
    
    def __init__(self, max_daily_loss: float):
        super().__init__("MaxDailyLossRule")
        self.max_daily_loss = max_daily_loss
        self.daily_pnl = 0.0
        self.daily_trade_count = 0
    
    def check(self, context: Dict) -> bool:
        """
        Check if daily loss exceeds maximum
        """
        # Update daily PnL
        trade_pnl = context.get('trade_pnl', 0)
        if 'trade_pnl' in context:
            self.daily_pnl += trade_pnl
            self.daily_trade_count += 1
        
        # Check loss limit
        if self.daily_pnl < -self.max_daily_loss:
            self.add_violation(
                f"Daily loss {abs(self.daily_pnl)} exceeds maximum {self.max_daily_loss}",
                {
                    'daily_pnl': self.daily_pnl,
                    'daily_trades': self.daily_trade_count
                }
            )
            return True
        
        return False
    
    def reset_day(self):
        """Reset daily stats"""
        self.daily_pnl = 0.0
        self.daily_trade_count = 0
        self.clear_violations()


class MaxDrawdownRule(RiskRule):
    """
    Rule: Maximum drawdown
    Prevents portfolio drawdown exceeding threshold
    """
    
    def __init__(self, max_drawdown_percent: float):
        super().__init__("MaxDrawdownRule")
        self.max_drawdown_percent = max_drawdown_percent
        self.peak_value = 0.0
        self.current_value = 0.0
    
    def check(self, context: Dict) -> bool:
        """
        Check if drawdown exceeds maximum
        """
        # Update current value
        portfolio_value = context.get('portfolio_value', 0)
        if 'portfolio_value' in context:
            self.current_value = portfolio_value
            
            # Update peak
            if portfolio_value > self.peak_value:
                self.peak_value = portfolio_value
        
        # Calculate drawdown
        if self.peak_value > 0:
            drawdown_percent = ((self.peak_value - self.current_value) / self.peak_value) * 100
            
            if drawdown_percent > self.max_drawdown_percent:
                self.add_violation(
                    f"Drawdown {drawdown_percent:.2f}% exceeds maximum {self.max_drawdown_percent}%",
                    {
                        'peak_value': self.peak_value,
                        'current_value': self.current_value,
                        'drawdown': drawdown_percent
                    }
                )
                return True
        
        return False
    
    def reset_peak(self):
        """Reset peak value"""
        self.peak_value = 0.0
        self.clear_violations()


class StopLossRule(RiskRule):
    """
    Rule: Stop loss
    Closes positions that hit stop loss level
    """
    
    def __init__(self):
        super().__init__("StopLossRule")
    
    def check(self, context: Dict) -> bool:
        """
        Check if position hit stop loss
        """
        positions = context.get('positions', [])
        violations = []
        
        for position in positions:
            stop_loss = getattr(position, 'stop_loss', None)
            side = getattr(position, 'side', 'buy')
            
            if stop_loss and position.current_price:
                if side == 'buy':
                    # Long position: stop loss below entry
                    if position.current_price <= stop_loss:
                        violations.append({
                            'symbol': position.symbol,
                            'reason': 'Stop loss triggered',
                            'stop_price': stop_loss,
                            'current_price': position.current_price,
                            'action': 'sell'
                        })
                else:  # sell
                    # Short position: stop loss above entry
                    if position.current_price >= stop_loss:
                        violations.append({
                            'symbol': position.symbol,
                            'reason': 'Stop loss triggered',
                            'stop_price': stop_loss,
                            'current_price': position.current_price,
                            'action': 'buy'
                        })
        
        if violations:
            for violation in violations:
                self.add_violation(
                    violation['reason'],
                    violation
                )
            return True
        
        return False


class TakeProfitRule(RiskRule):
    """
    Rule: Take profit
    Closes positions that hit take profit level
    """
    
    def __init__(self):
        super().__init__("TakeProfitRule")
    
    def check(self, context: Dict) -> bool:
        """
        Check if position hit take profit
        """
        positions = context.get('positions', [])
        violations = []
        
        for position in positions:
            take_profit = getattr(position, 'take_profit', None)
            side = getattr(position, 'side', 'buy')
            
            if take_profit and position.current_price:
                if side == 'buy':
                    # Long position: take profit above entry
                    if position.current_price >= take_profit:
                        violations.append({
                            'symbol': position.symbol,
                            'reason': 'Take profit triggered',
                            'profit_price': take_profit,
                            'current_price': position.current_price,
                            'action': 'sell'
                        })
                else:  # sell
                    # Short position: take profit below entry
                    if position.current_price <= take_profit:
                        violations.append({
                            'symbol': position.symbol,
                            'reason': 'Take profit triggered',
                            'profit_price': take_profit,
                            'current_price': position.current_price,
                            'action': 'buy'
                        })
        
        if violations:
            for violation in violations:
                self.add_violation(
                    violation['reason'],
                    violation
                )
            return True
        
        return False


class RiskRulesEngine:
    """
    Risk Rules Engine - Manages and executes all risk rules
    """
    
    def __init__(self):
        self.rules: List[RiskRule] = []
        self.enabled = True
    
    def add_rule(self, rule: RiskRule):
        """Add a risk rule"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        """Remove a risk rule by name"""
        self.rules = [r for r in self.rules if r.name != rule_name]
    
    def check_rules(self, context: Dict) -> List[Dict]:
        """
        Check all enabled rules
        Returns list of violations
        """
        violations = []
        
        if not self.enabled:
            return violations
        
        for rule in self.rules:
            if rule.enabled:
                try:
                    is_violated = rule.check(context)
                    
                    if is_violated:
                        rule_violations = rule.get_violations()
                        violations.extend(rule_violations)
                        
                except Exception as e:
                    print(f"Error checking rule {rule.name}: {str(e)}")
        
        return violations
    
    def get_rule(self, rule_name: str) -> Optional[RiskRule]:
        """Get rule by name"""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def get_all_violations(self) -> List[Dict]:
        """Get all violations from all rules"""
        violations = []
        for rule in self.rules:
            violations.extend(rule.get_violations())
        return violations
    
    def clear_all_violations(self):
        """Clear all violations"""
        for rule in self.rules:
            rule.clear_violations()
    
    def enable_rules(self):
        """Enable all rules"""
        self.enabled = True
        for rule in self.rules:
            rule.enabled = True
    
    def disable_rules(self):
        """Disable all rules"""
        self.enabled = False
        for rule in self.rules:
            rule.enabled = False
    
    def create_default_rules(
        self,
        max_position_size: float = 10000.0,
        max_daily_loss: float = 5000.0,
        max_drawdown: float = 10.0
    ):
        """
        Create default risk rules
        """
        self.add_rule(MaxPositionSizeRule(max_position_size))
        self.add_rule(MaxDailyLossRule(max_daily_loss))
        self.add_rule(MaxDrawdownRule(max_drawdown))
        self.add_rule(StopLossRule())
        self.add_rule(TakeProfitRule())
        
        print(f"✓ Created {len(self.rules)} default risk rules")