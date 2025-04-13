# Imports
import pyomo.environ as pyo
import time
from Input import initialize_data
from optimizer import optimizer
from Output import save_and_plot_results

# import data
file_path = 'data.csv'
Netload_values, Tou_price, battery_cost, roundtrip_efficiency, self_discharge, \
 charge_power_capacity, discharge_power_capacity, electricity_sell_price_ratio, CRF, PD_rate = initialize_data(file_path)

if __name__ == "__main__":
    # Import data
    file_path = 'data.csv'
    Netload_values, Tou_price, battery_cost, roundtrip_efficiency, self_discharge, \
    charge_power_capacity, discharge_power_capacity, electricity_sell_price_ratio, CRF, PD_rate = initialize_data(file_path)

    # Start time
    start_time = time.time()

    # Call the optimizer
    model = optimizer(Netload_values, Tou_price, battery_cost, roundtrip_efficiency, 
                               self_discharge, charge_power_capacity, discharge_power_capacity, electricity_sell_price_ratio, CRF, PD_rate)

    # End time
    end_time = time.time()

    # Calculate the total execution time
    execution_time = time.time() - start_time

    # Print objective function value, battery capacity, Grid_IMax values and running time
    objective_value  = pyo.value(model.obj)
    battery_capacity = pyo.value(model.Max_Cap)
#    Grid_IMax_values = [pyo.value(model.Grid_IMax[m]) for m in model.M]
    
    print(f"Objective Function Value: {objective_value:.1f} $")
    print(f"Battery Capacity: {battery_capacity:.1f} kWh")
    print(f"Running Time: {execution_time:.2f} seconds")


    # Save results and plot
    save_and_plot_results(model)



