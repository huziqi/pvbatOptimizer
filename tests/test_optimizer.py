import unittest
import pandas as pd
import numpy as np
from pvbat_optimizer.optimizer import PVBatOptimizer
from pvbat_optimizer.config import OptimizerConfig

class TestPVBatOptimizer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # 创建测试数据
        self.constant_tou_prices = {i: 1.0 for i in range(24)}  # 统一电价
        self.tou_prices = {  # 分时电价，根据实际情况设置
        0: 0.152, 1: 0.143, 2: 0.137, 3: 0.137, 4: 0.145, 5: 0.172,
        6: 0.204, 7: 0.185, 8: 0.144, 9: 0.123, 10: 0.113, 11: 0.109,
        12: 0.110, 13: 0.116, 14: 0.127, 15: 0.148, 16: 0.181, 17: 0.244,
        18: 0.279, 19: 0.294, 20: 0.249, 21: 0.213, 22: 0.181, 23: 0.163
        }
        self.config = OptimizerConfig(
            tou_prices=self.tou_prices,
            pv_capcity=500,
            battery_cost_per_kwh=400
        )
        
        # simple test data
        self.load_profile = pd.Series([
            13983.17, 9790.90, 12048.80, 10690.62, 14023.50, 10746.43,  # 0-5点
            9950.53, 11328.19, 11551.15, 10326.99, 13252.53, 12240.30,  # 6-11点
            17207.70, 12101.74, 15967.69, 19851.62, 15332.47, 12845.18,  # 12-17点
            11537.30, 10397.30, 9313.35, 10860.78, 8289.51, 7590.15     # 18-23点
        ])
        
        self.pv_profile = pd.Series([
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,                               # 0-5点
            0.0, 0.00403, 0.03152, 0.05065, 0.04911, 0.07998,          # 6-11点
            0.10127, 0.10713, 0.12189, 0.11025, 0.07684, 0.00421,      # 12-17点
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0                               # 18-23点
        ])
    
    def test_config_validation(self):
        """Test configuration validation"""

        # 测试无效的分时电价
        with self.assertRaises(ValueError):
            OptimizerConfig(
                tou_prices={},
                pv_capcity=500,
                battery_cost_per_kwh=400
            )
        
        # 测试无效的PV容量
        with self.assertRaises(ValueError):
            OptimizerConfig(
                tou_prices=self.tou_prices,
                pv_capcity=-100,  # 负值
                battery_cost_per_kwh=400
            )
        
        # 测试无效的电池成本
        with self.assertRaises(ValueError):
            OptimizerConfig(
                tou_prices=self.tou_prices,
                pv_capcity=500,
                battery_cost_per_kwh=0  # 零值
            )
        with self.assertRaises(ValueError):
            OptimizerConfig(
                tou_prices=self.tou_prices,
                pv_capcity=500,
                battery_cost_per_kwh=-100  # 负值
            )
    
    def test_tou_prices_validation(self):
        """Test input data validation"""
        df = pd.read_csv('examples/data.csv')
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')
        
        load_profile = df['load_kW']
        pv_profile = df['PV_power_rate']
        
        config = OptimizerConfig(
                tou_prices=self.constant_tou_prices,
                pv_capcity=500,
                battery_cost_per_kwh=400
            )
        optimizer = PVBatOptimizer(config)
        result = optimizer.optimize(load_profile, pv_profile)
        self.assertEqual(result['battery_capacity'], 0)
    
    def test_extreme_cases(self):
        """Test extreme cases"""
        df = pd.read_csv('examples/data.csv')
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')
        
        load_profile = df['load_kW']
        pv_profile = df['PV_power_rate']
        optimizer = PVBatOptimizer(self.config)
        
        # 测试零负荷情况
        zero_load = pd.Series(np.zeros(len(load_profile)), index=load_profile.index)
        result = optimizer.optimize(zero_load, pv_profile)
        self.assertAlmostEqual(result['battery_capacity'], 0, places=2)
        
        # 测试零PV情况
        # zero_pv = pd.Series(np.zeros(len(pv_profile)), index=pv_profile.index)
        # result = optimizer.optimize(load_profile, zero_pv)
        # self.assertAlmostEqual(result['battery_capacity'], 0, places=2)
        
        # 测试高电池成本情况
        high_cost_config = OptimizerConfig(
            tou_prices=self.tou_prices,
            pv_capcity=500,
            battery_cost_per_kwh=10000  # 很高的电池成本
        )
        optimizer = PVBatOptimizer(high_cost_config)
        result = optimizer.optimize(load_profile, pv_profile)
        self.assertAlmostEqual(result['battery_capacity'], 0, places=2)

if __name__ == '__main__':
    unittest.main()