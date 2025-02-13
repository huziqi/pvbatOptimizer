import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List

class OptimizerUtils:
    @staticmethod
    def calculate_crf(discount_rate: float, years: int) -> float:
        """计算资本回收系数"""
        return (discount_rate * (1 + discount_rate)**years) / ((1 + discount_rate)**years - 1)

    @staticmethod
    def validate_input_data(
        load_profile: pd.Series,
        pv_profile: pd.Series
    ) -> bool:
        """验证输入数据的有效性"""
        # 检查数据长度是否相同
        if len(load_profile) != len(pv_profile):
            raise ValueError("负荷曲线和PV出力曲线长度不一致")
        
        # 检查是否有缺失值
        if load_profile.isnull().any() or pv_profile.isnull().any():
            raise ValueError("输入数据存在缺失值")
        
        # 检查数据是否为负
        if (load_profile < 0).any() or (pv_profile < 0).any():
            raise ValueError("输入数据存在负值")
        
        return True

    @staticmethod
    def plot_optimization_results(
        results: Dict,
        load_profile: pd.Series,
        pv_profile: pd.Series,
        save_path: str = None
    ):
        """绘制优化结果图表"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 功率平衡图
        ax1.plot(load_profile.index, load_profile, label='Load', color='red')
        ax1.plot(pv_profile.index, pv_profile, label='PV Generation', color='green')
        ax1.plot(results['grid_import'], label='Grid Import', color='blue')
        ax1.set_title('Power Balance')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Power (kW)')
        ax1.legend()
        ax1.grid(True)

        # 电池运行状态图
        ax2.plot(results['battery_energy'], label='Battery Energy', color='orange')
        ax2.set_title('Battery State')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Energy (kWh)')
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()

    @staticmethod
    def calculate_system_metrics(
        results: Dict,
        load_profile: pd.Series,
        pv_profile: pd.Series,
        config: 'OptimizerConfig'
    ) -> Dict:
        """计算系统性能指标"""
        total_load = load_profile.sum()
        total_pv_generation = pv_profile.sum()
        total_grid_import = sum(results['grid_import'])
        total_grid_export = sum(results['grid_export'])
        
        metrics = {
            "self_consumption_rate": (total_pv_generation - total_grid_export) / total_pv_generation,
            "self_sufficiency_rate": (total_load - total_grid_import) / total_load,
            "battery_cycles": sum(results['battery_charge']) / results['battery_capacity'],
            "lcoe": results['total_cost'] / (total_load - total_grid_import),
            "pv_utilization_rate": (total_pv_generation - total_grid_export) / total_pv_generation
        }
        
        return metrics