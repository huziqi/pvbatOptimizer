import dis
import pandas as pd
from pvbat_optimizer import PVBatOptimizer_linearProg, OptimizerConfig, OptimizerUtils
import time
from datetime import datetime

def run_basic_example():
    # Load example data
    net_load=OptimizerUtils.net_profiles("data/net_load/roof_PartFacade/15min/net_load_E39.csv",None)

    
    config = OptimizerConfig(
        battery_cost_per_kwh=1300,
        electricity_sell_price_ratio=0.6,
        battery_charge_efficiency=0.913,
        battery_discharge_efficiency=0.913,
        charge_power_capacity=0.5,
        discharge_power_capacity=0.5,
        use_seasonal_prices=True,
        years=15,
        discount_rate=0.13,
        decision_step=0.25,
        # demand_charge_rate=33.8
        demand_charge_rate=0
    )
    
    # Create optimizer
    optimizer = PVBatOptimizer_linearProg(config)
    
    # Run optimization
    start_time = time.time()
    result = optimizer.optimize(net_load)
    end_time = time.time()
    
    
    # Print results
    print("Optimization results:")
    print(f"Optimal battery capacity: {result['battery_capacity']:.2f} kWh")
    print(f"Total cost: {result['total_cost']:.2f} currency")
    print(f"Battery construction cost: {result['battery_construction_cost']:.2f} currency")
    print(f"\nOptimization duration: {end_time - start_time:.2f} seconds")
    
    # Plot results
    # OptimizerUtils.plot_seasonal_comparison(
    #     result,
    #     net_load,
    #     months=(1,6),
    #     save_dir='seasonal_comparison'
    # )

    # Save results to CSV
    result_df = pd.DataFrame(result)
    result_df.to_csv('seasonal_comparison/optimization_results.csv', index=False)
    print("Optimization results saved to 'optimization_results.csv'")

    # Calculate KPIs
    kpis = OptimizerUtils.calculate_system_metrics(result, net_load)
    print("\nKPIs:")
    for kpi, value in kpis.items():
        print(f"{kpi}: {value}")

    # 计算并打印经济性指标
    economic_metrics = OptimizerUtils.calculate_economic_metrics(
        total_cost=result['total_cost'],
        annual_savings=result['annual_savings'],
        project_lifetime=config.years,
        discount_rate=0.01,
        battery_construction_cost=result['battery_construction_cost']
    )
    
    print("\n经济性指标:")
    print(f"静态投资回收期: {economic_metrics['payback_period']:.2f}年")
    print(f"净现值: {economic_metrics['npv']:.2f}元")
    print(f"内部收益率: {economic_metrics['irr']:.2f}%")
    # OptimizerUtils.plot_single_fig(result['grid_export'], "Time", "Grid Export (kWh)", "seasonal_comparison/grid_export.png")

    # OptimizerUtils.calculate_daily_battery_cycles(result,save_path='seasonal_comparison/daily_battery_cycles.png')


if __name__ == '__main__':
    run_basic_example()