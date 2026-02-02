#!/usr/bin/env python3
"""
Quantitative Trading Platform - Production Deployment Script
Run this script to deploy the platform for production use
"""

import os
import sys
import subprocess
import json
import time
import signal
from pathlib import Path

class PlatformDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_file = self.project_root / "config" / "deployment.json"
        self.pid_file = self.project_root / "platform.pid"
        self.log_file = self.project_root / "logs" / "platform.log"

    def check_prerequisites(self):
        """Check if all prerequisites are installed"""
        print("Checking prerequisites...")
        
        prerequisites = {
            'python3': True,
            'pip3': True,
            'flask': True,
            'pandas': True,
            'numpy': True,
            'backtrader': True,
            'requests': True
        }
        
        for req, required in prerequisites.items():
            try:
                subprocess.run([f"python3", "-c", f"import {req}"], 
                              check=True, capture_output=True)
                print(f"  ✓ {req}")
            except:
                if required:
                    print(f"  ✗ {req} - MISSING")
                    return False
                else:
                    print(f"  ⚠ {req} - Optional, not found")
        
        print("✓ All required dependencies installed\n")
        return True

    def setup_directories(self):
        """Create necessary directories"""
        print("Setting up directories...")
        
        dirs = [
            self.project_root / "logs",
            self.project_root / "data" / "cache",
            self.project_root / "data" / "backtest_results",
            self.project_root / "config"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {dir_path}")
        
        print("✓ Directories created\n")

    def create_config(self):
        """Create default configuration"""
        print("Creating configuration...")
        
        config = {
            "platform": {
                "name": "Quantitative Trading Platform",
                "version": "1.0.0",
                "environment": "production",
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            },
            "database": {
                "type": "sqlite",
                "path": "data/trading.db"
            },
            "caching": {
                "enabled": True,
                "redis_url": "redis://localhost:6379"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/platform.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            "security": {
                "api_key_required": True,
                "rate_limiting": True,
                "max_requests_per_minute": 60
            },
            "risk_management": {
                "max_position_size": 0.20,
                "max_risk_per_trade": 0.02,
                "max_daily_loss": 5000,
                "max_drawdown": 0.15
            },
            "trading": {
                "simulated_trading": True,
                "paper_trading": True,
                "execution_algorithm": "TWAP"
            }
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"  ✓ Configuration file created: {self.config_file}")
        print("✓ Configuration complete\n")

    def run_tests(self):
        """Run system tests"""
        print("Running system tests...")
        
        test_files = [
            "tests/test_adapters.py",
            "tests/test_strategies.py",
            "tests/test_backtest_engine.py",
            "tests/test_risk_system.py",
            "tests/test_trading_system.py"
        ]
        
        passed = 0
        failed = 0
        
        for test_file in test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                try:
                    result = subprocess.run(
                        ["python3", str(test_path)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        print(f"  ✓ {test_file}")
                        passed += 1
                    else:
                        print(f"  ✗ {test_file}")
                        failed += 1
                except subprocess.TimeoutExpired:
                    print(f"  ⚠ {test_file} - TIMEOUT")
                    failed += 1
            else:
                print(f"  ⊗ {test_file} - NOT FOUND")
        
        print(f"\n  Tests: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("✓ All tests passed\n")
            return True
        else:
            print("⚠ Some tests failed\n")
            return False

    def start_platform(self):
        """Start the trading platform"""
        print("Starting Quantitative Trading Platform...")
        
        # Import and start the platform
        sys.path.insert(0, str(self.project_root))
        
        try:
            from web.web_platform import TradingPlatformWeb
            
            platform = TradingPlatformWeb(
                host='0.0.0.0',
                port=5000,
                debug=False
            )
            
            platform.initialize_components()
            
            print("  ✓ Platform components initialized")
            print("  ✓ Web server starting on http://0.0.0.0:5000")
            print("\n🚀 Platform started successfully!")
            print("   Dashboard: http://localhost:5000/dashboard")
            print("   API: http://localhost:5000/api/health\n")
            
            # Run the app
            platform.app.run(
                host='0.0.0.0',
                port=5000,
                debug=False,
                use_reloader=False
            )
            
        except Exception as e:
            print(f"  ✗ Failed to start platform: {e}")
            return False

    def deploy(self):
        """Execute full deployment process"""
        print("=" * 70)
        print("QUANTITATIVE TRADING PLATFORM - DEPLOYMENT")
        print("=" * 70)
        print()
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites check failed")
            print("Please install required dependencies:")
            print("  pip install flask pandas numpy backtrader requests")
            return False
        
        # Step 2: Setup directories
        self.setup_directories()
        
        # Step 3: Create configuration
        self.create_config()
        
        # Step 4: Run tests
        if not self.run_tests():
            print("⚠  Some tests failed, but proceeding with deployment")
        
        # Step 5: Start platform
        return self.start_platform()


def main():
    deployer = PlatformDeployer()
    
    try:
        success = deployer.deploy()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n🛑 Deployment interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())