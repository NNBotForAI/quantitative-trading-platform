"""
Test Risk Management System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
from data_interface_framework import Position, AssetType
from risk import PositionManager, RiskRulesEngine, RiskMonitor


def test_position_manager():
    """Test position manager"""
    print("\n" + "=" * 60)
    print("测试仓位管理器")
    print("=" * 60)
    
    # Create position manager
    pm = PositionManager(
        initial_capital=100000.0,
        max_position_size=0.2,
        max_risk_per_trade=0.02
    )
    
    # Test position size calculation
    print("\n1. 测试仓位大小计算")
    symbol = "AAPL"
    entry_price = 150.0
    stop_loss = 145.0
    
    position_size = pm.calculate_position_size(
        symbol,
        entry_price,
        stop_loss
    )
    
    print(f"  符号: {symbol}")
    print(f"  入场价: ${entry_price}")
    print(f"  止损价: ${stop_loss}")
    print(f"  计算仓位: {position_size} 股")
    
    # Test opening position
    print("\n2. 测试开仓")
    position = pm.open_position(
        symbol=symbol,
        side='buy',
        quantity=position_size,
        entry_price=entry_price,
        stop_loss=stop_loss
    )
    
    print(f"  仓位已开: {symbol} {position.side} {position.quantity} @ ${entry_price}")
    print(f"  止损: ${position.stop_loss}")
    
    # Test updating position price
    print("\n3. 测试更新价格")
    new_price = 155.0
    pm.update_position_price(symbol, new_price)
    position = pm.get_position(symbol)
    
    print(f"  新价格: ${new_price}")
    print(f"  当前持仓价: ${position.current_price}")
    
    # Test portfolio value
    print("\n4. 测试组合价值")
    portfolio_value = pm.get_portfolio_value()
    portfolio_risk = pm.get_portfolio_risk()
    
    print(f"  组合价值: ${portfolio_value:,.2f}")
    print(f"  总风险: ${portfolio_risk['total_risk']:,.2f}")
    print(f"  风险比例: {portfolio_risk['risk_percent']:.2f}%")
    
    # Test closing position
    print("\n5. 测试平仓")
    exit_price = 160.0
    profit_loss = pm.close_position(symbol, exit_price)
    
    print(f"  平仓价格: ${exit_price}")
    print(f"  盈亏: ${profit_loss:,.2f}")
    
    # Test limits
    print("\n6. 测试仓位限制")
    can_open = pm.check_position_limits("GOOGL", 1000, 100.0)
    print(f"  可开1000股GOOGL: {can_open}")
    
    # Test summary
    print("\n7. 测试摘要")
    summary = pm.get_summary()
    
    print(f"  初始资金: ${summary['initial_capital']:,.2f}")
    print(f"  当前资金: ${summary['current_capital']:,.2f}")
    print(f"  总仓位: {summary['total_positions']}")
    print(f"  总交易: {summary['total_trades']}")
    print(f"  胜率: {summary['win_rate']:.2f}%")
    
    print("\n✓ 仓位管理器测试完成")
    return True


def test_risk_rules():
    """Test risk rules engine"""
    print("\n" + "=" * 60)
    print("测试风险规则引擎")
    print("=" * 60)
    
    # Create rules engine
    engine = RiskRulesEngine()
    
    # Create default rules
    print("\n1. 创建默认风险规则")
    engine.create_default_rules(
        max_position_size=10000.0,
        max_daily_loss=5000.0,
        max_drawdown=10.0
    )
    
    print(f"  已创建 {len(engine.rules)} 条规则")
    
    # Test max position size rule
    print("\n2. 测试最大仓位规则")
    context = {
        'position_size': 15000.0,
        'symbol': 'AAPL'
    }
    
    violations = engine.check_rules(context)
    print(f"  测试仓位大小 15000:")
    print(f"  违规数: {len(violations)}")
    
    # Test max drawdown rule
    print("\n3. 测试最大回撤规则")
    context = {
        'portfolio_value': 90000.0
    }
    
    # Simulate peak value first
    max_drawdown_rule = engine.get_rule('MaxDrawdownRule')
    max_drawdown_rule.peak_value = 100000.0
    
    violations = engine.check_rules(context)
    print(f"  当前价值: $90,000 (峰值: $100,000)")
    print(f"  回撤: 10%")
    print(f"  违规数: {len(violations)}")
    
    # Test stop loss rule
    print("\n4. 测试止损规则")
    position = Position(
        symbol="AAPL",
        quantity=100,
        avg_entry_price=150.0,
        current_price=145.0,
        asset_type=AssetType.STOCK
    )
    
    # Add attributes not in constructor
    position.stop_loss = 146.0
    position.side = 'buy'
    
    context = {
        'positions': [position]
    }
    
    violations = engine.check_rules(context)
    print(f"  当前价格: $145.0")
    print(f"  止损价: $146.0")
    print(f"  触发止损: {'是' if violations else '否'}")
    
    print("\n✓ 风险规则引擎测试完成")
    return True


def test_risk_monitor():
    """Test risk monitor"""
    print("\n" + "=" * 60)
    print("测试风险监控器")
    print("=" * 60)
    
    # Create components
    pm = PositionManager(initial_capital=100000.0)
    engine = RiskRulesEngine()
    monitor = RiskMonitor(pm, engine)
    
    # Create rules
    engine.create_default_rules()
    
    # Add test alert callback
    alert_count = [0]
    def alert_callback(alert):
        alert_count[0] +=1
        print(f"  告警: {alert.level} - {alert.message}")
    
    monitor.add_alert_callback(alert_callback)
    
    # Open some positions
    print("\n1. 开测试仓位")
    pm.open_position("AAPL", 'buy', 50, 150.0, stop_loss=145.0)
    pm.open_position("GOOGL", 'buy', 30, 100.0, stop_loss=95.0)
    print(f"  已开 {len(pm.positions)} 个仓位")
    
    # Check risk
    print("\n2. 检查风险")
    new_alerts = monitor.check_risk()
    print(f"  新告警: {len(new_alerts)}")
    
    # Print risk summary
    print("\n3. 风险摘要")
    monitor.print_risk_summary()
    
    # Simulate price drop
    print("\n4. 模拟价格下跌")
    pm.update_position_price("AAPL", 144.0)  # Below stop loss
    new_alerts = monitor.check_risk()
    print(f"  AAPL价格跌至 $144.0")
    print(f"  新告警: {len(new_alerts)}")
    
    print("\n✓ 风险监控器测试完成")
    return True


def test_integration():
    """Test full risk management integration"""
    print("\n" + "=" * 60)
    print("测试完整风控系统集成")
    print("=" * 60)
    
    # Create full system
    pm = PositionManager(
        initial_capital=100000.0,
        max_position_size=0.2,
        max_risk_per_trade=0.02
    )
    
    engine = RiskRulesEngine()
    engine.create_default_rules()
    
    monitor = RiskMonitor(pm, engine)
    monitor.set_check_interval(1)  # 1 minute for testing
    
    print("\n1. 系统初始化")
    print(f"  仓位管理器: 初始资金 $100,000")
    print(f"  规则引擎: {len(engine.rules)} 条规则")
    print(f"  监控器: 检查间隔 1分钟")
    
    # Simulate trading day
    print("\n2. 模拟交易日")
    
    # Open positions
    pos1_size = pm.calculate_position_size("AAPL", 150.0, 145.0)
    pm.open_position("AAPL", 'buy', pos1_size, 150.0, stop_loss=145.0, take_profit=160.0)
    
    pos2_size = pm.calculate_position_size("GOOGL", 100.0, 95.0)
    pm.open_position("GOOGL", 'buy', pos2_size, 100.0, stop_loss=95.0)
    
    # Update prices
    pm.update_position_price("AAPL", 152.0)
    pm.update_position_price("GOOGL", 102.0)
    
    # Check risk
    monitor.check_risk()
    
    # Get summary
    print("\n3. 当前状态")
    summary = monitor.get_risk_summary()
    
    print(f"  总仓位: {summary['rule_violations']['total']} 个")
    print(f"  组合价值: ${summary['portfolio_risk']['portfolio_value']:,.2f}")
    print(f"  风险比例: {summary['portfolio_risk']['risk_percent']:.2f}%")
    
    # Close one position
    print("\n4. 平仓操作")
    pnl = pm.close_position("AAPL", 158.0)
    print(f"  AAPL平仓: 盈亏 ${pnl:,.2f}")
    
    # Final check
    monitor.check_risk()
    monitor.print_risk_summary()
    
    print("\n✓ 集成测试完成")
    return True


def run_all_risk_tests():
    """Run all risk management tests"""
    print("\n" + "=" * 60)
    print("风控系统测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # Test position manager
        all_passed &= test_position_manager()
        
        # Test risk rules
        all_passed &= test_risk_rules()
        
        # Test risk monitor
        all_passed &= test_risk_monitor()
        
        # Test integration
        all_passed &= test_integration()
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if all_passed:
        print("✓ 所有的控系统测试通过！")
        return True
    else:
        print("✗ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_all_risk_tests()
    exit(0 if success else 1)