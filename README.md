# PV-Battery Optimizer

PV-Battery Optimizer is a photovoltaic energy storage system optimization tool based on the Gurobi optimizer. It calculates optimal battery capacity configurations based on load profiles, photovoltaic generation, and time-of-use electricity prices to minimize total system costs.

## Key Features

- **Single Plot Optimization**: Optimize PV-battery systems for individual plots to determine optimal battery capacity and operation strategy
- **Multi-Plot Collaborative Optimization**: Optimize battery capacity allocation across multiple plots under total capacity constraints
- **Flexible Pricing Models**: Support both time-of-use pricing and seasonal pricing modes
- **Demand Charge Calculation**: Support monthly or daily demand charge calculations
- **Economic Analysis**: Calculate payback period, net present value, internal rate of return and other economic indicators
- **Visualization Analysis**: Provide comprehensive result visualization and seasonal comparison analysis

## System Requirements

- Python >= 3.8
- Gurobi Optimizer (valid license required)

## Installation

### 1. Clone the Repository (Please use the branch `clean`)
```bash
git clone -b clean https://github.com/yourusername/pvbatOpt.git
cd pvbatOpt
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Package
```bash
pip install -e .
```

## Project Structure

```
pvbatOpt/
├── pvbat_optimizer/           # Main package files
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration class definitions
│   ├── utils.py              # Utility functions
│   ├── PVBatOptimizer_linearProg.py  # Single plot linear programming optimizer
│   └── MultiPlotOptimizer.py         # Multi-plot collaborative optimizer
├── examples/                  # Example code
│   └── demo.py               # Usage examples
├── Data/                     # Data folder
├── tests/                    # Test files
├── setup.py                  # Installation configuration
├── requirements.txt          # Dependency list
└── README.md                # Documentation
```

## Quick Start

### 1. Single Plot Optimization Example

```python
from pvbat_optimizer import PVBatOptimizer_linearProg, OptimizerConfig, OptimizerUtils

# 1. Load data (net load = load - PV generation)
net_load = OptimizerUtils.net_profiles(
    "building_load.csv",  # Building load file
    "pv_generation.csv"   # PV generation file (optional, None for no PV)
)

# 2. Configure optimization parameters
config = OptimizerConfig(
    battery_cost_per_kwh=1000,           # Battery cost ($/kWh)
    electricity_sell_price_ratio=0.0,    # Electricity selling price ratio
    use_seasonal_prices=True,             # Use seasonal pricing
    years=15,                            # Project lifetime
    discount_rate=0.13,                  # Discount rate
    demand_charge_rate=33.8,             # Demand charge rate ($/kW)
    peak_price=1.61,                     # Peak price ($/kWh)
    high_price=1.34,                     # High price ($/kWh)
    flat_price=0.81,                     # Flat price ($/kWh)
    valley_price=0.35                    # Valley price ($/kWh)
)

# 3. Create optimizer and run optimization
optimizer = PVBatOptimizer_linearProg(config)
result = optimizer.optimize(net_load)

# 4. View results
print(f"Optimal battery capacity: {result['battery_capacity']:.2f} kWh")
print(f"Annual savings: {result['annual_savings']:.2f} $")
print(f"Battery construction cost: {result['battery_construction_cost']:.2f} $")
```

### 2. Multi-Plot Collaborative Optimization Example

```python
from pvbat_optimizer import MultiPlotOptimizer

# 1. Load data for multiple plots
net_loads = {
    "Plot A": OptimizerUtils.net_profiles("load_A.csv", None),
    "Plot B": OptimizerUtils.net_profiles("load_B.csv", None),
    "Plot C": OptimizerUtils.net_profiles("load_C.csv", None)
}

# 2. Configure parameters (same as single plot configuration)
config = OptimizerConfig(
    battery_cost_per_kwh=1000,
    use_seasonal_prices=True,
    years=15,
    discount_rate=0.13
    # ... other parameters
)

# 3. Set total capacity constraint and create multi-plot optimizer
total_battery_capacity = 10000  # Total capacity constraint (kWh)
multi_optimizer = MultiPlotOptimizer(config, total_battery_capacity)

# 4. Run multi-plot optimization
multi_result = multi_optimizer.optimize_multi_plots(net_loads)

# 5. View results
print(f"Total battery capacity: {multi_result['total_battery_capacity']:.2f} kWh")
for plot_name, capacity in multi_result['capacity_allocation'].items():
    print(f"{plot_name}: {capacity:.2f} kWh")
```

## Data Format Requirements

### Net Load Data Format
CSV files should contain the following columns:
- First column: Time index (DateTime format)
- Second column: Load values (kW)

```csv
DateTime,Total Power (kW)
2022-01-01 00:00:00,1000.5
2022-01-01 00:15:00,1050.2
2022-01-01 00:30:00,980.7
...
```

## Configuration Parameters

### Basic Economic Parameters
- `battery_cost_per_kwh`: Battery cost ($/kWh)
- `years`: Project lifetime (default: 25 years)
- `discount_rate`: Discount rate (default: 0.07)
- `electricity_sell_price_ratio`: Electricity selling price ratio (default: 0.7)

### Pricing Settings
Two pricing modes are supported:

#### Mode 1: Traditional Time-of-Use Pricing
```python
config = OptimizerConfig(
    use_seasonal_prices=False,
    tou_prices={  # 24-hour price dictionary
        0: 0.152, 1: 0.143, 2: 0.137, # ... prices for 24 hours
        # ...
        23: 0.163
    }
)
```

#### Mode 2: Seasonal Four-Tier Pricing
```python
config = OptimizerConfig(
    use_seasonal_prices=True,
    peak_price=1.61,     # Peak price ($/kWh)
    high_price=1.34,     # High price ($/kWh)
    flat_price=0.81,     # Flat price ($/kWh)
    valley_price=0.35    # Valley price ($/kWh)
)
```

### Battery Technical Parameters
- `soc_max`: Maximum state of charge (default: 0.8)
- `soc_min`: Minimum state of charge (default: 0.2)
- `charge_power_capacity`: Maximum charge power ratio (default: 0.25)
- `discharge_power_capacity`: Maximum discharge power ratio (default: 0.25)
- `battery_charge_efficiency`: Charging efficiency (default: 0.9)
- `battery_discharge_efficiency`: Discharging efficiency (default: 0.9)

### Demand Charge Settings
- `demand_charge_rate`: Demand charge rate ($/kW, default: 0)
- `billing_period`: Billing period ('monthly' or 'daily', default: 'monthly')

### Other Parameters
- `decision_step`: Decision time step (hours, default: 0.25 i.e., 15 minutes)
- `max_battery_capacity`: Maximum battery capacity constraint (kWh, default: 100000)

## Result Analysis

### Optimization Results Include
- `battery_capacity`: Optimal battery capacity (kWh)
- `total_cost`: Total cost ($)
- `annual_savings`: Annual savings ($)
- `battery_construction_cost`: Battery construction cost ($)
- `grid_import`: Grid import power time series
- `grid_export`: Grid export power time series
- `battery_charge`: Battery charging time series
- `battery_discharge`: Battery discharging time series
- `battery_energy`: Battery energy state time series

### Economic Indicators Calculation
```python
# Calculate economic metrics
economic_metrics = OptimizerUtils.calculate_economic_metrics(
    total_cost=result['total_cost'],
    annual_savings=result['annual_savings'],
    project_lifetime=config.years,
    discount_rate=0.08,
    battery_construction_cost=result['battery_construction_cost']
)

print(f"Payback period: {economic_metrics['payback_period']:.2f} years")
print(f"Net present value: {economic_metrics['npv']:.2f} $")
print(f"Internal rate of return: {economic_metrics['irr']:.2f}%")
```

## Visualization Features

### Seasonal Comparison Analysis
```python
# Compare operational performance across different months
OptimizerUtils.plot_seasonal_comparison(
    result,
    net_load,
    months=[3, 8],  # Compare March and August
    save_dir='seasonal_comparison'
)
```

### Battery Cycle Analysis
```python
# Analyze daily battery cycle distribution
cycle_analysis = OptimizerUtils.calculate_daily_battery_cycles(
    result,
    save_path='battery_cycles.png'
)
```

## Running Examples

### Single Plot Optimization
```bash
cd examples
python demo.py
```

### Multi-Plot Optimization
```bash
cd examples
python demo.py multi
```

## Important Notes

1. **Gurobi License**: This tool requires a valid Gurobi optimizer license
2. **Data Time Resolution**: 15-minute time resolution data is recommended
3. **Data Integrity**: Ensure load and PV data have completely consistent time indices
4. **Memory Usage**: Large-scale optimization may require significant memory, recommend at least 8GB RAM

## License

This project is licensed under the GNU License. For details, please refer to the [LICENSE](LICENSE) file.

## Technical Support

For questions or suggestions, please contact:
- Email: gabriel.hu@connect.ust.hk
- GitHub Issues: [Submit Issues](https://github.com/yourusername/pvbatOpt/issues)
