import pandas as pd
from pvbat_optimizer import PVBatOptimizer, OptimizerConfig, OptimizerUtils

def run_basic_example():
    # 加载示例数据
    load_profile = pd.read_csv('example_data/load.csv')['load']
    pv_profile = pd.read_csv('example_data/pv.csv')['generation']
    
    # 创建配置
    tou_prices = {i: 1.0 for i in range(24)}  # 示例电价
    config = OptimizerConfig(
        tou_prices=tou_prices,
        pv_cost_per_kw=800,
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
    
    # 绘制结果
    OptimizerUtils.plot_optimization_results(
        result,
        load_profile,
        pv_profile,
        save_path='optimization_results.png'
    )

if __name__ == '__main__':
    run_basic_example()