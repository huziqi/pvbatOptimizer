import pandas as pd
import numpy as np
from pvbat_optimizer import PVBatOptimizer, OptimizerConfig, OptimizerUtils
import time
from datetime import datetime
import matplotlib.pyplot as plt
import multiprocessing as mp
from functools import partial

def run_basic_example():
    # Load example data
    df = pd.read_csv('/home/user/huziqi/pvbatOpt/examples/data.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])  # Convert time strings to datetime format
    df = df.set_index('datetime')  # Set datetime as index
    
    # Extract load and PV data
    load_profile = df['load_kW']  # Ensure column names match the CSV file
    pv_profile = df['PV_power_rate']  # Ensure column names match the CSV file
    
    # Create configuration
    tou_prices = {  # Time-of-use prices, set according to actual conditions
        0: 0.152, 1: 0.143, 2: 0.137, 3: 0.137, 4: 0.145, 5: 0.172,
        6: 0.204, 7: 0.185, 8: 0.144, 9: 0.123, 10: 0.113, 11: 0.109,
        12: 0.110, 13: 0.116, 14: 0.127, 15: 0.148, 16: 0.181, 17: 0.244,
        18: 0.279, 19: 0.294, 20: 0.249, 21: 0.213, 22: 0.181, 23: 0.163
    }
    
    config = OptimizerConfig(
        tou_prices=tou_prices,
        pv_capacity=500,
        battery_cost_per_kwh=400
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
    print(f"Total cost: {result['total_cost']:.2f} CNY")
    print("\nSystem performance metrics:")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.2%}")

def _run_single_optimization(battery_cost: float, pv_capacity: float,
                           load_profile: pd.Series, pv_profile: pd.Series, 
                           tou_prices: dict) -> dict:
    """Run single optimization case"""
    config = OptimizerConfig(
        tou_prices=tou_prices,
        pv_capacity=pv_capacity,
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

    tou_prices = {  # Time-of-use prices, set according to actual conditions
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
    """Main function"""
    # Load data
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