import unittest
import pandas as pd
import numpy as np
from pvbat_optimizer.optimizer import PVBatOptimizer
from pvbat_optimizer.config import OptimizerConfig

class TestPVBatOptimizer(unittest.TestCase):
    def setUp(self):
        # 创建测试数据
        self.tou_prices = {i: 1.0 for i in range(24)}  # 统一电价
        self.config = OptimizerConfig(
            tou_prices=self.tou_prices,
            pv_cost_per_kw=800,
            battery_cost_per_kwh=400
        )
        
        # 创建24小时测试数据
        self.test_index = pd.date_range('2024-01-01', periods=24, freq='H')
        self.load_profile = pd.Series(
            np.ones(24) * 100,  # 恒定负荷100kW
            index=self.test_index
        )
        self.pv_profile = pd.Series(
            np.concatenate([
                np.zeros(6),           # 0-6点无出力
                np.ones(12) * 120,     # 6-18点满出力
                np.zeros(6)            # 18-24点无出力
            ]),
            index=self.test_index
        )

    def test_basic_optimization(self):
        """测试基本优化功能"""
        optimizer = PVBatOptimizer(self.config)
        result = optimizer.optimize(
            self.load_profile,
            self.pv_profile,
            battery_capacity_range=(0, 1000)
        )
        
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result["battery_capacity"], 0)
        self.assertLessEqual(result["battery_capacity"], 1000)

    def test_no_pv_scenario(self):
        """测试无PV情况"""
        optimizer = PVBatOptimizer(self.config)
        no_pv_profile = pd.Series(np.zeros(24), index=self.test_index)
        
        result = optimizer.optimize(
            self.load_profile,
            no_pv_profile,
            battery_capacity_range=(0, 1000)
        )
        
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["battery_capacity"], 0, places=2)

    def test_high_battery_cost(self):
        """测试高电池成本情况"""
        config_high_cost = OptimizerConfig(
            tou_prices=self.tou_prices,
            pv_cost_per_kw=800,
            battery_cost_per_kwh=10000  # 很高的电池成本
        )
        
        optimizer = PVBatOptimizer(config_high_cost)
        result = optimizer.optimize(
            self.load_profile,
            self.pv_profile,
            battery_capacity_range=(0, 1000)
        )
        
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["battery_capacity"], 0, places=2)

if __name__ == '__main__':
    unittest.main()