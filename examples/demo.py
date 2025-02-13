import pandas as pd
from pvbat_optimizer import PVBatOptimizer, OptimizerConfig, OptimizerUtils
import time
from datetime import datetime

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
    
    # 绘制结果
    OptimizerUtils.plot_optimization_results(
        result,
        load_profile,
        pv_profile,
        save_path='optimization_results.png'
    )

if __name__ == '__main__':
    # 记录开始时间
    start_time = time.time()
    print(f"\n优化开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    run_basic_example()
    # 记录结束时间
    end_time = time.time()
    print(f"\n优化结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n优化用时: {end_time - start_time:.2f} 秒")