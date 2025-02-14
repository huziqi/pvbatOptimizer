import pandas as pd
import numpy as np
from pvbat_optimizer import PVBatOptimizer, OptimizerConfig, OptimizerUtils
import time
from datetime import datetime
import matplotlib.pyplot as plt
import multiprocessing as mp
from functools import partial

def run_basic_example():
    # 加载示例数据
    df = pd.read_csv('/home/user/huziqi/pvbatOpt/examples/data.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])  # 将时间字符串转换为datetime格式
    df = df.set_index('datetime')  # 设置datetime为索引
    
    # 提取负载和光伏数据
    load_profile = df['load_kW']  # 注意列名与CSV文件对应
    pv_profile = df['PV_power_rate']  # 注意列名与CSV文件对应
    
    # 创建配置
    tou_prices = {  # 分时电价，根据实际情况设置
        0: 0.152, 1: 0.143, 2: 0.137, 3: 0.137, 4: 0.145, 5: 0.172,
        6: 0.204, 7: 0.185, 8: 0.144, 9: 0.123, 10: 0.113, 11: 0.109,
        12: 0.110, 13: 0.116, 14: 0.127, 15: 0.148, 16: 0.181, 17: 0.244,
        18: 0.279, 19: 0.294, 20: 0.249, 21: 0.213, 22: 0.181, 23: 0.163
    }
    
    config = OptimizerConfig(
        tou_prices=tou_prices,
        pv_capcity=500,
        battery_cost_per_kwh=400
    )
    
    # 创建优化器
    optimizer = PVBatOptimizer(config)
    
    # 运行优化
    result = optimizer.optimize(load_profile, pv_profile)
    
    # 计算系统指标
    metrics = OptimizerUtils.calculate_system_metrics(
        result,
        load_profile,
        pv_profile,
        config
    )
    
    # 打印结果
    print("优化结果：")
    print(f"最优电池容量: {result['battery_capacity']:.2f} kWh")
    print(f"总成本: {result['total_cost']:.2f} 元")
    print("\n系统性能指标：")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.2%}")

def _run_single_optimization(battery_cost: float, pv_capacity: float,
                           load_profile: pd.Series, pv_profile: pd.Series, 
                           tou_prices: dict) -> dict:
    """Run single optimization case"""
    config = OptimizerConfig(
        tou_prices=tou_prices,
        pv_capcity=pv_capacity,
        battery_cost_per_kwh=battery_cost
    )
    
    optimizer = PVBatOptimizer(config)
    result = optimizer.optimize(load_profile, pv_profile)
    
    return {
        'battery_cost': battery_cost,
        'pv_capacity': pv_capacity,
        'battery_capacity': result['battery_capacity']
    }

def run_pv_sensitivity_analysis(
    load_profile: pd.Series,
    pv_profile: pd.Series,
    battery_costs: tuple = (300, 400, 500),
    pv_capacities: tuple = (100, 300, 500, 1000, 2000, 5000)
) -> pd.DataFrame:
    """Run sensitivity analysis for different battery costs and PV capacities"""
    
    # Create results storage
    results = []

    tou_prices = {  # 分时电价，根据实际情况设置
        0: 0.152, 1: 0.143, 2: 0.137, 3: 0.137, 4: 0.145, 5: 0.172,
        6: 0.204, 7: 0.185, 8: 0.144, 9: 0.123, 10: 0.113, 11: 0.109,
        12: 0.110, 13: 0.116, 14: 0.127, 15: 0.148, 16: 0.181, 17: 0.244,
        18: 0.279, 19: 0.294, 20: 0.249, 21: 0.213, 22: 0.181, 23: 0.163
    }
    
    # Iterate through different battery costs
    total_runs = len(battery_costs) * len(pv_capacities)
    print(f"\nStarting sensitivity analysis...")
    print(f"PV capacity range: {pv_capacities[0]}kW - {pv_capacities[-1]}kW")
    print(f"Battery costs: {battery_costs}")
    print(f"Total runs: {total_runs}\n")
    
    # Create partial function with fixed arguments
    run_opt = partial(_run_single_optimization, 
                     load_profile=load_profile,
                     pv_profile=pv_profile,
                     tou_prices=tou_prices)
    
    # Prepare optimization cases
    cases = [(battery_cost, pv_capacity) 
             for battery_cost in battery_costs 
             for pv_capacity in pv_capacities]
    
    # Run parallel optimization
    with mp.Pool() as pool:
        results = []
        for i, result in enumerate(pool.starmap(run_opt, cases), 1):
            results.append(result)
            print(f"\nProgress: {i}/{total_runs}")
            print(f"Battery Cost: {result['battery_cost']}, "
                  f"PV: {result['pv_capacity']}kW")
            print(f"Optimal battery capacity: {result['battery_capacity']:.2f}kWh")
    
    return pd.DataFrame(results)

def main():
    """主函数"""
    # 加载数据
    df = pd.read_csv('/home/user/huziqi/pvbatOpt/examples/data.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime')
    
    # Extract load and PV profiles
    load_profile = df['load_kW']
    pv_profile = df['PV_power_rate']
    
    # Run sensitivity analysis
    start_time = time.time()
    print(f"Analysis start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results_df = run_pv_sensitivity_analysis(
        load_profile=load_profile,
        pv_profile=pv_profile,
        battery_costs=(300, 400, 500),
        pv_capacities=(100, 300, 500, 1000, 2000, 5000)
    )
    
    # Save results
    results_df.to_csv('pv_sensitivity_results.csv', index=False)
    OptimizerUtils.plot_sensitivity_results(results_df)
    
    print(f"\nAnalysis end time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time: {time.time() - start_time:.2f}s")

if __name__ == '__main__':
    main()