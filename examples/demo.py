import dis
import pandas as pd
from pvbat_optimizer import PVBatOptimizer_linearProg, OptimizerConfig, OptimizerUtils
import time
from datetime import datetime

def run_basic_example():
    # Load example data
    net_load=OptimizerUtils.net_profiles("data/load_E13_hourly.csv",None)
    
    config = OptimizerConfig(
        battery_cost_per_kwh=890,
        electricity_sell_price_ratio=0.6,
        use_seasonal_prices=True,
        years=10,
        discount_rate=0.10,
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
    print(f"\nOptimization duration: {end_time - start_time:.2f} seconds")
    
    # Plot results
    OptimizerUtils.plot_seasonal_comparison(
        result,
        net_load,
        save_dir='optimization_results.png'
    )

    # Save results to CSV
    result_df = pd.DataFrame(result)
    result_df.to_csv('seasonal_comparison/optimization_results.csv', index=False)
    print("Optimization results saved to 'optimization_results.csv'")

    # Calculate KPIs
    kpis = OptimizerUtils.calculate_system_metrics(result, net_load)
    print("\nKPIs:")
    for kpi, value in kpis.items():
        print(f"{kpi}: {value}")

    OptimizerUtils.plot_single_fig(result['grid_export'], "Time", "Grid Export (kWh)", "seasonal_comparison/grid_export.png")

if __name__ == '__main__':
    run_basic_example()