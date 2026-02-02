"""
Risk Monitor for Quantitative Trading Platform
Real-time risk monitoring and alerts
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from data_interface_framework import Position, Order
from .position_manager import PositionManager
from .risk_rules import RiskRulesEngine


class RiskAlert:
    """
    Risk alert data structure
    """
    
    def __init__(
        self,
        level: str,  # 'info', 'warning', 'critical'
        message: str,
        details: Dict = None
    ):
        self.level = level
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
        self.acknowledged = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'level': self.level,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged
        }


class RiskMonitor:
    """
    Risk Monitor - Real-time risk monitoring
    """
    
    def __init__(
        self,
        position_manager: PositionManager,
        rules_engine: RiskRulesEngine
    ):
        self.position_manager = position_manager
        self.rules_engine = rules_engine
        
        self.alerts: List[RiskAlert] = []
        self.alert_callbacks: List[Callable] = []
        
        self.last_check_time = None
        self.check_interval = timedelta(minutes=5)
    
    def add_alert_callback(self, callback: Callable):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable):
        """Remove callback function"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def check_risk(self) -> List[RiskAlert]:
        """
        Check all risk rules and generate alerts
        """
        current_time = datetime.now()
        
        # Check interval
        if self.last_check_time and (current_time - self.last_check_time) < self.check_interval:
            return []
        
        self.last_check_time = current_time
        
        # Create context for rules
        portfolio_value = self.position_manager.get_portfolio_value()
        positions = self.position_manager.get_all_positions()
        
        context = {
            'portfolio_value': portfolio_value,
            'positions': positions,
            'timestamp': current_time.isoformat()
        }
        
        # Check rules
        violations = self.rules_engine.check_rules(context)
        
        # Generate alerts from violations
        new_alerts = []
        
        for violation in violations:
            alert_level = self._determine_alert_level(violation)
            alert = RiskAlert(
                level=alert_level,
                message=violation.get('reason', 'Risk violation detected'),
                details=violation
            )
            
            self.alerts.append(alert)
            new_alerts.append(alert)
            
            # Call callbacks
            self._trigger_callbacks(alert)
        
        return new_alerts
    
    def _determine_alert_level(self, violation: Dict) -> str:
        """Determine alert level from violation"""
        rule_name = violation.get('rule', '')
        
        # Critical level violations
        if 'MaxDrawdown' in rule_name or 'MaxDailyLoss' in rule_name:
            return 'critical'
        
        # Warning level violations
        if 'MaxPositionSize' in rule_name or 'StopLoss' in rule_name:
            return 'warning'
        
        # Info level violations
        return 'info'
    
    def _trigger_callbacks(self, alert: RiskAlert):
        """Trigger all alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {str(e)}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[RiskAlert]:
        """Get alerts from last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff_time
        ]
    
    def get_critical_alerts(self) -> List[RiskAlert]:
        """Get all critical alerts"""
        return [
            alert for alert in self.alerts
            if alert.level == 'critical' and not alert.acknowledged
        ]
    
    def acknowledge_alert(self, alert_index: int):
        """Acknowledge an alert"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index].acknowledged = True
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []
    
    def get_risk_summary(self) -> Dict:
        """
        Get comprehensive risk summary
        """
        recent_alerts = self.get_recent_alerts(24)
        critical_alerts = self.get_critical_alerts()
        
        # Count alerts by level
        alert_counts = {
            'critical': len([a for a in recent_alerts if a.level == 'critical']),
            'warning': len([a for a in recent_alerts if a.level == 'warning']),
            'info': len([a for a in recent_alerts if a.level == 'info'])
        }
        
        # Get portfolio risk
        portfolio_risk = self.position_manager.get_portfolio_risk()
        
        # Get rule violations
        violations = self.rules_engine.get_all_violations()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'alerts_24h': {
                'total': len(recent_alerts),
                'by_level': alert_counts
            },
            'unacknowledged_critical': len(critical_alerts),
            'portfolio_risk': portfolio_risk,
            'rule_violations': {
                'total': len(violations),
                'by_rule': self._count_violations_by_rule(violations)
            }
        }
    
    def _count_violations_by_rule(self, violations: List[Dict]) -> Dict:
        """Count violations by rule name"""
        counts = {}
        
        for violation in violations:
            rule_name = violation.get('rule', 'Unknown')
            counts[rule_name] = counts.get(rule_name, 0) + 1
        
        return counts
    
    def print_risk_summary(self):
        """Print risk summary"""
        summary = self.get_risk_summary()
        
        print("\n" + "=" * 60)
        print("风险监控报告")
        print("=" * 60)
        
        # Alerts
        alerts_24h = summary['alerts_24h']
        print(f"\n过去24小时告警:")
        print(f"  总数: {alerts_24h['total']}")
        print(f"  严重: {alerts_24h['by_level']['critical']}")
        print(f"  警告: {alerts_24h['by_level']['warning']}")
        print(f"  信息: {alerts_24h['by_level']['info']}")
        
        # Unacknowledged critical
        unack = summary['unacknowledged_critical']
        print(f"\n未确认严重告警: {unack}")
        
        # Portfolio risk
        port_risk = summary['portfolio_risk']
        print(f"\n组合风险:")
        print(f"  总风险: ${port_risk['total_risk']:,.2f}")
        print(f"  风险比例: {port_risk['risk_percent']:.2f}%")
        print(f"  总敞口: ${port_risk['total_exposure']:,.2f}")
        print(f"  敞口比例: {port_risk['exposure_percent']:.2f}%")
        
        # Rule violations
        violations = summary['rule_violations']
        print(f"\n规则违规:")
        print(f"  总数: {violations['total']}")
        print(f"  按规则:")
        for rule_name, count in violations['by_rule'].items():
            print(f"    {rule_name}: {count}")
        
        print("\n" + "=" * 60)
    
    def enable_monitoring(self):
        """Enable risk monitoring"""
        print("✓ 风险监控已启用")
    
    def disable_monitoring(self):
        """Disable risk monitoring"""
        print("✓ 风险监控已禁用")
    
    def set_check_interval(self, minutes: int):
        """Set check interval in minutes"""
        self.check_interval = timedelta(minutes=minutes)
        print(f"✓ 检查间隔设置为 {minutes} 分钟")
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        max_daily_loss_rule = self.rules_engine.get_rule('MaxDailyLossRule')
        if max_daily_loss_rule:
            max_daily_loss_rule.reset_day()
        
        max_drawdown_rule = self.rules_engine.get_rule('MaxDrawdownRule')
        if max_drawdown_rule:
            max_drawdown_rule.reset_peak()
        
        print("✓ 每日统计已重置")


class RiskDashboard:
    """
    Risk Dashboard - Real-time risk display
    """
    
    def __init__(self, risk_monitor: RiskMonitor):
        self.risk_monitor = risk_monitor
        self.update_callbacks: List[Callable] = []
    
    def add_update_callback(self, callback: Callable):
        """Add update callback"""
        self.update_callbacks.append(callback)
    
    def refresh(self):
        """Refresh dashboard data"""
        # Check risk
        new_alerts = self.risk_monitor.check_risk()
        
        # Get summary
        summary = self.risk_monitor.get_risk_summary()
        
        # Trigger callbacks
        for callback in self.update_callbacks:
            try:
                callback(summary, new_alerts)
            except Exception as e:
                print(f"Error in dashboard callback: {str(e)}")
        
        return summary, new_alerts
    
    def get_display_data(self) -> Dict:
        """Get data for display"""
        return self.risk_monitor.get_risk_summary()