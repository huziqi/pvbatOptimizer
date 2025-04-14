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
        demand_charge_rate=33.8
        # demand_charge_rate=0
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

if __name__ == '__main__':
    run_basic_example()