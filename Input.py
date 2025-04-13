import csv

def initialize_data(file_path):
    Netload_values = []
    Tou_price = []

    # Input data
    battery_cost = 200
    roundtrip_efficiency = 0.95
    Rate = 0.07
    self_discharge = 0.000002 
    Projectlife = 25
    charge_power_capacity = 0.25    # Maximum charge power to capacity ratio
    discharge_power_capacity = 0.25  # Maximum discharge power to capacity ratio
    electricity_sell_price_ratio = 0.6  # Electricity sell price ratio
    CRF = (Rate * ((1 + Rate) ** Projectlife)) / (((1 + Rate) ** Projectlife) - 1)
    PD_rate = 18 #Peak demand charge rate
    # Importing Net load and TOU price from CSV
    with open(file_path, newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            Netload_values.append(float(row[2])) 
            Tou_price.append(float(row[3])) 

    return (Netload_values, Tou_price, battery_cost, roundtrip_efficiency, 
            self_discharge, charge_power_capacity, discharge_power_capacity, 
            electricity_sell_price_ratio, CRF, PD_rate)

# Main code
file_path = 'data.csv'
Netload_values, Tou_price, battery_cost, roundtrip_efficiency, self_discharge, \
 charge_power_capacity, discharge_power_capacity, electricity_sell_price_ratio, CRF , PD_rate = initialize_data(file_path)