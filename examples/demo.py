import pandas as pd
from pvbat_optimizer import PVBatOptimizer, OptimizerConfig, OptimizerUtils
import time
from datetime import datetime

def run_basic_example():
    # Load example data
    df = pd.read_csv('/home/user/huziqi/pvbatOpt/examples/data.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])  # Convert time strings to datetime format
    df = df.set_index('datetime')  # Set datetime as index
    
    # Extract load and PV data
    load_profile = df['load_kW']  # Ensure column names match the CSV file
    pv_profile = df['PV_power_rate']  # Ensure column names match the CSV file
    
    # Create configuration
    tou_prices = {  # Time-of-use prices, set according to actual situation
        0: 0.152, 1: 0.143, 2: 0.137, 3: 0.137, 4: 0.145, 5: 0.172,
        6: 0.204, 7: 0.185, 8: 0.144, 9: 0.123, 10: 0.113, 11: 0.109,
        12: 0.110, 13: 0.116, 14: 0.127, 15: 0.148, 16: 0.181, 17: 0.244,
        18: 0.279, 19: 0.294, 20: 0.249, 21: 0.213, 22: 0.181, 23: 0.163
    }
    
    config = OptimizerConfig(
        tou_prices=tou_prices,
        pv_capcity=0,
        battery_cost_per_kwh=400,
        electricity_sell_price_ratio=0.99
    )
    
    # Create optimizer
    optimizer = PVBatOptimizer(config)
    
    # Run optimization
    result = optimizer.optimize(load_profile, pv_profile)
    
    # Calculate system metrics
    metrics = OptimizerUtils.calculate_system_metrics(
        result,
        load_profile,
        pv_profile,
        config
    )
    
    # Print results
    print("Optimization results:")
    print(f"Optimal battery capacity: {result['battery_capacity']:.2f} kWh")
    print(f"Total cost: {result['total_cost']:.2f} currency")
    # print("\nSystem performance metrics:")
    # for metric, value in metrics.items():
    #     print(f"{metric}: {value:.2%}")
    
    # Plot results
    OptimizerUtils.plot_optimization_results(
        result,
        load_profile,
        pv_profile,
        save_path='optimization_results.png'
    )

if __name__ == '__main__':
    # Record start time
    start_time = time.time()
    print(f"\nOptimization start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    run_basic_example()
    # Record end time
    end_time = time.time()
    print(f"\nOptimization end time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nOptimization duration: {end_time - start_time:.2f} seconds")