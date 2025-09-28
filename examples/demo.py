import dis
from re import T
import pandas as pd
from pvbat_optimizer import PVBatOptimizer_linearProg, OptimizerConfig, OptimizerUtils, MultiPlotOptimizer
import time
from datetime import datetime

def run_basic_example():
    # Load example data
    net_load=OptimizerUtils.net_profiles("data/net_load/roof_PartFacade/15min/net_load_E13.csv",None)
    building_load=OptimizerUtils.net_profiles("data/load_raw_data/15min/load_E13.csv",None)


    config = OptimizerConfig(
        battery_cost_per_kwh=1000,
        electricity_sell_price_ratio=0.6,
        battery_charge_efficiency=0.913,
        battery_discharge_efficiency=0.913,
        charge_power_capacity=0.45,
        discharge_power_capacity=0.45,
        use_seasonal_prices=True,
        years=15,
        discount_rate=0.13,
        decision_step=0.25,
        max_battery_capacity=2743,
        pv_cost=1761845,
        # pv_cost=0,
        # peak_price=1.61,
        # high_price=1.34,
        # flat_price=0.81,
        # valley_price=0.35,
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
    print(f"Battery construction cost: {result['battery_construction_cost']:.2f} currency")
    print(f"\nOptimization duration: {end_time - start_time:.2f} seconds")
    
    # Save results to CSV
    # result_df = pd.DataFrame(result)
    # result_df.to_csv('seasonal_comparison/optimization_results.csv', index=False)
    # print("Optimization results saved to 'optimization_results.csv'")


    # 计算建筑负荷的总电费
    building_load_cost = OptimizerUtils.calculate_building_load_cost(building_load, config)
    
    print("\n建筑负荷电费分析:")
    print(f"总电能费用: {building_load_cost['total_energy_cost']:.2f}元")
    print(f"总需量费用: {building_load_cost['total_demand_cost']:.2f}元")
    print(f"建筑负荷总电费: {building_load_cost['total_cost']:.2f}元")

    annual_savings = building_load_cost['total_cost'] - result['optimized_total_cost']
    # 计算并打印经济性指标
    economic_metrics = OptimizerUtils.calculate_economic_metrics(
        annual_savings=annual_savings,
        project_lifetime=config.years,
        discount_rate=0.0155,
        battery_construction_cost=result['battery_construction_cost'],
        pv_cost=config.pv_cost
    )
    
    print("\n经济性指标:")
    print(f"静态投资回收期: {economic_metrics['payback_period']:.2f}年")
    print(f"净现值: {economic_metrics['npv']:.2f}元")
    print(f"内部收益率: {economic_metrics['irr']:.2f}%")



def run_multi_plot_example():
    """Run multi-plot battery capacity optimization example"""
    print("=== Multi-Plot Battery Capacity Optimization ===")
    
    # Load net load data for multiple plots
    net_loads = {
        "E13": OptimizerUtils.net_profiles("data/net_load/roof_PartFacade/15min/net_load_E13.csv", None),
        "E25": OptimizerUtils.net_profiles("data/net_load/roof_PartFacade/15min/net_load_E25_2.csv", None),
        "E37": OptimizerUtils.net_profiles("data/net_load/roof_PartFacade/15min/net_load_E37.csv", None),
        "E39": OptimizerUtils.net_profiles("data/net_load/roof_PartFacade/15min/net_load_E39.csv", None)
    }

    building_loads = {
        "E13": OptimizerUtils.net_profiles("data/load_raw_data/15min/load_E13.csv", None),
        "E25": OptimizerUtils.net_profiles("data/load_raw_data/15min/load_E25_2.csv", None),
        "E37": OptimizerUtils.net_profiles("data/load_raw_data/15min/load_E37.csv", None),
        "E39": OptimizerUtils.net_profiles("data/load_raw_data/15min/load_E39.csv", None)
    }
    
    # Configuration for multi-plot optimization
    config = OptimizerConfig(
        battery_cost_per_kwh=1000,
        electricity_sell_price_ratio=0.0,
        battery_charge_efficiency=0.913,
        battery_discharge_efficiency=0.913,
        charge_power_capacity=0.45,
        discharge_power_capacity=0.45,
        use_seasonal_prices=True,
        years=15,
        discount_rate=0.13,
        decision_step=0.25,
        pv_cost=7867584,
        # pv_cost=0,
        peak_price=1.61,
        high_price=1.34,
        flat_price=0.81,
        valley_price=0.35,
        # demand_charge_rate=33.8
        demand_charge_rate=0
    )
    
    # Total battery capacity constraint (10MW = 10000kWh)
    total_battery_capacity = 10000  # kWh
    
    # Create multi-plot optimizer
    multi_optimizer = MultiPlotOptimizer(config, total_battery_capacity, force=False)
    
    # Run multi-plot optimization
    print(f"Starting multi-plot optimization with total capacity constraint: {total_battery_capacity} kWh")
    start_time = time.time()
    
    try:
        multi_result = multi_optimizer.optimize_multi_plots(net_loads)
        end_time = time.time()
        
        print(f"\nMulti-plot optimization completed in {end_time - start_time:.2f} seconds")
        
        # Print detailed results for each plot
        print(f"\n=== Detailed Results by Plot ===")
        total_optimization_cost = 0
        total_construction_cost = 0
        
        for plot_name, plot_result in multi_result["plots"].items():
            print(f"\n--- Plot {plot_name} ---")
            print(f"Allocated battery capacity: {plot_result['battery_capacity']:.2f} kWh")
            print(f"Battery construction cost: {plot_result['battery_construction_cost']:.2f}")
            print(f"Annual savings: {plot_result['annual_savings']:.2f}")
            print(f"Original total cost: {plot_result['original_total_cost']:.2f}")
            print(f"Optimized total cost: {plot_result['optimized_total_cost']:.2f}")
            
            total_optimization_cost += plot_result['optimized_total_cost']
            total_construction_cost += plot_result['battery_construction_cost']
        
        print(f"\n=== Overall Summary ===")
        print(f"Total battery capacity used: {multi_result['total_battery_capacity']:.2f} / {total_battery_capacity:.2f} kWh")
        print(f"Total construction cost: {total_construction_cost:.2f}")
        print(f"Total optimization cost: {total_optimization_cost:.2f}")

        # 计算各建筑的负荷电费
        print(f"\n=== Building Load Electricity Cost Analysis ===")
        total_building_cost = 0
        for plot_name, load_data in building_loads.items():
            building_cost = OptimizerUtils.calculate_building_load_cost(load_data, config)
            total_building_cost += building_cost['total_cost']
            
            print(f"\n--- Plot {plot_name} Building Load Cost ---")
            print(f"总电能费用: {building_cost['total_energy_cost']:.2f}元")
            print(f"总需量费用: {building_cost['total_demand_cost']:.2f}元")
            print(f"建筑负荷总电费: {building_cost['total_cost']:.2f}元")
            
        
        print(f"\n=== Total Building Load Cost Summary ===")
        print(f"所有建筑负荷总电费: {total_building_cost:.2f}元")

        total_annual_savings = total_building_cost - total_optimization_cost
        # Calculate and print economic metrics for multi-plot system
        economic_metrics = OptimizerUtils.calculate_economic_metrics(
            annual_savings=total_annual_savings,
            project_lifetime=config.years,
            discount_rate=0.0155,
            battery_construction_cost=total_construction_cost,
            pv_cost=config.pv_cost
        )
        
        print(f"\n=== Multi-Plot Economic Metrics ===")
        print(f"Payback period: {economic_metrics['payback_period']:.2f} years")
        print(f"NPV: {economic_metrics['npv']:.2f}")
        print(f"IRR: {economic_metrics['irr']:.2f}%")
        
        
        
        # Save multi-plot results
        multi_result_summary = pd.DataFrame({
            'Plot': list(multi_result['capacity_allocation'].keys()),
            'Battery_Capacity_kWh': list(multi_result['capacity_allocation'].values()),
            'Capacity_Percentage': [cap/total_battery_capacity*100 for cap in multi_result['capacity_allocation'].values()],
            'Annual_Savings': [multi_result['plots'][plot]['annual_savings'] for plot in multi_result['capacity_allocation'].keys()],
            'Construction_Cost': [multi_result['plots'][plot]['battery_construction_cost'] for plot in multi_result['capacity_allocation'].keys()]
        })
        
        multi_result_summary.to_csv('seasonal_comparison/multi_plot_optimization_summary.csv', index=False)
        print(f"\nMulti-plot results saved to 'multi_plot_optimization_summary.csv'")
        
        return multi_result
        
    except Exception as e:
        print(f"Multi-plot optimization failed: {e}")
        return None


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'multi':
        # Run multi-plot optimization
        run_multi_plot_example()
    else:
        # Run single-plot optimization (original functionality)
        print("=== Single-Plot Battery Optimization (Original) ===")
        run_basic_example()