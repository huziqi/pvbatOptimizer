# PV-Battery Optimizer
## Introduction

PV-Battery Optimizer is a photovoltaic energy storage system optimization tool based on the Gurobi optimizer. It can calculate the optimal battery capacity configuration based on load profiles, photovoltaic output, and time-of-use electricity prices, achieving the minimization of the total system cost.

## Features

- Supports time-of-use electricity price optimization
- Considers battery charging and discharging efficiency and self-discharge
- Supports parallel computing for sensitivity analysis
- Calculates detailed system performance metrics
- Visualizes optimization results and sensitivity analysis

## Dependencies

- Python >= 3.8
- pandas
- numpy
- matplotlib
- gurobipy
- multiprocessing

## Installation
```bash
git clone https://github.com/yourusername/pvbat-optimizer.git
cd pvbat-optimizer
pip install -e .
```

## Usage

### Basic Optimization Example

```python
from pvbat_optimizer import PVBatOptimizer, OptimizerConfig

# Load data
df = pd.read_csv('data.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.set_index('datetime')

# Create configuration
config = OptimizerConfig(
    tou_prices={0: 0.152, 1: 0.143, ...},  # Time-of-use electricity prices
    pv_capcity=500,                         # Photovoltaic capacity
    battery_cost_per_kwh=400                # Battery unit cost
)

# Run optimization
optimizer = PVBatOptimizer(config)
result = optimizer.optimize(df['load_kW'], df['PV_power_rate'])

# Output results
print(f"Optimal battery capacity: {result['battery_capacity']:.2f} kWh")
print(f"Total cost: {result['total_cost']:.2f} yuan")
```

## Configuration Parameters

### Required Parameters
- `tou_prices`: Time-of-use electricity prices (Dict[int, float])
- `pv_capcity`: Photovoltaic installed capacity (float)
- `battery_cost_per_kwh`: Battery unit cost (float)

### Optional Parameters
- `years`: Project duration (default: 25)
- `discount_rate`: Discount rate (default: 0.07)
- `electricity_sell_price_ratio`: Electricity selling price ratio (default: 0.7)
- `soc_max`: Maximum charging state (default: 0.9)
- `soc_min`: Minimum charging state (default: 0.2)
- `charge_power_capacity`: Maximum charging power ratio (default: 0.25)
- `discharge_power_capacity`: Maximum discharging power ratio (default: 0.25)
- `battery_charge_efficiency`: Charging efficiency (default: 0.95)
- `battery_discharge_efficiency`: Discharging efficiency (default: 0.95)

## System Metrics

- Self-consumption rate
- Self-sufficiency rate
- Battery cycle times
- Levelized cost of electricity (LCOE)
- Photovoltaic utilization rate

## Development

### Running Tests
```bash
python -m unittest tests/test_optimizer.py
```

## License

This project is licensed under the MIT License. Please refer to the [LICENSE](LICENSE) file for details.

## Todo:
- [ ] 检查电池容量变化不明显可能是由于以下原因：
1. **优化目标**：如果优化目标主要是最小化成本，电池容量可能不会显著变化，除非 PV 容量对成本有很大影响。
2. 约束条件：电池容量可能受到其他约束的限制，比如最大充放电功率、SOC 限制等。
3. PV 影响：PV 容量的变化可能对系统的整体影响较小，特别是在电网价格和电池成本主导的情况下。