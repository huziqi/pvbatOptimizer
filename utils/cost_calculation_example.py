#!/usr/bin/env python3
"""
电费计算示例脚本
演示如何使用ElectricityCostCalculator计算建筑负荷的电费
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.scripts.electricity_cost_calculator import ElectricityCostCalculator

def run_cost_calculation_example():
    """运行电费计算示例"""
    
    # 数据文件路径
    csv_file = "data/net_load/roof_PartFacade/total_net_load_15min2.csv"
    
    print("电费计算示例")
    print("="*50)
    
    # 创建电费计算器，使用默认电价
    calculator = ElectricityCostCalculator(
        peak_price=1.61,      # 峰时电价
        high_price=1.34,      # 高峰电价  
        flat_price=0.81,      # 平时电价
        valley_price=0.35,    # 谷时电价
        demand_charge_rate=0,  # 需量电费
        billing_period='monthly',  # 按月计费
        decision_step=0.25    # 15分钟时间步长
    )
    
    try:
        # 加载负荷数据
        print(f"正在加载数据文件: {csv_file}")
        load_data = calculator.load_csv_data(csv_file)
        
        # 计算电费
        print("正在计算电费...")
        results = calculator.calculate_electricity_costs(load_data)
        
        # 显示结果
        calculator.print_results(results)
        
        # 额外分析
        print("\n" + "="*60)
        print("额外分析")
        print("="*60)
        
        # 计算单位电费
        total_energy = results['statistics']['total_energy_kwh']
        unit_cost = results['total_cost'] / total_energy
        print(f"平均单位电费: {unit_cost:.4f} 元/kWh")
        
        # 分析需量电费占比
        demand_ratio = results['demand_cost'] / results['total_cost'] * 100
        print(f"需量电费占比: {demand_ratio:.1f}%")
        
        if demand_ratio > 30:
            print("提示: 需量电费占比较高，建议考虑削峰填谷策略")
        
        # 分析不同时段用电占比
        energy_breakdown = results['energy_cost_breakdown']
        total_energy_cost = results['energy_cost']
        
        print(f"\n各时段电费占比:")
        for period, cost in energy_breakdown.items():
            ratio = cost / total_energy_cost * 100 if total_energy_cost > 0 else 0
            period_names = {'peak': '峰时', 'high': '高峰', 'flat': '平时', 'valley': '谷时'}
            print(f"  {period_names[period]}: {ratio:.1f}%")
        
    except FileNotFoundError:
        print(f"错误: 找不到数据文件 '{csv_file}'")
        print("请确保数据文件存在，或修改csv_file路径")
    except Exception as e:
        print(f"计算过程中出现错误: {e}")

if __name__ == "__main__":
    run_cost_calculation_example()
