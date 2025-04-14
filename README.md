# PV-Battery Optimizer
## Introduction

PV-Battery Optimizer is a photovoltaic energy storage system optimization tool based on the Gurobi optimizer. It can calculate the optimal battery capacity configuration based on load profiles, photovoltaic output, and time-of-use electricity prices, achieving the minimization of the total system cost.

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
### Project Structure

```
├── pvbat_optimizer/
│   ├── __init__.py
│   ├── PVBatOptimizer.py
│   ├── PVBatOptimizer_linearProg.py
│   ├── config.py
│   └── utils.py
├── examples/
│   ├── data.csv
│   ├── demo.py
├── tests/
│   ├── __init__.py
│   └── test_optimizer.py
├── utils/
├── LICENSE
├── README.md
└── setup.py
```
### Basic Optimization Example

```python
from pvbat_optimizer import PVBatOptimizer, OptimizerConfig

# Load data
net_load=OptimizerUtils.net_profiles("builing_load.csv","PV_generation.csv")
    
    config = OptimizerConfig(
        battery_cost_per_kwh=890,
        electricity_sell_price_ratio=0.6,
        use_seasonal_prices=True,
        years=10,
        discount_rate=0.10,
        demand_charge_rate=33.8
    )
    
    # Create optimizer
    optimizer = PVBatOptimizer_linearProg(config)
    
    # Run optimization
    result = optimizer.optimize(net_load)
```

### Data Format
The data should be in a CSV file with the following columns:
- `datetime`: Date and time (datetime)
- `load`: load for buildings (float)
```
datetime,building_load
2022-01-01 00:00:00,1000
2022-01-01 01:00:00,1050
```
If PV genertation data is available, it should also have the same format.
## Configuration Parameters

### Required Parameters
- `tou_prices`: Time-of-use electricity prices (Dict[int, float])
- `net_load`: Net load for buildings (float)
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

## Software Scalability	
The optimization part can be implemented using different optimization algorithms. The current implementation uses the Gurobi optimizer. However, it can be easily extended to other optimization algorithms.
### Implement guidance
The base class `PVBatOptimizer` is an abstract class that defines the interface for the optimization algorithms. The methods `optimize` has to be implemented by the user.
```python
@abstractmethod
def optimize(self, net_load: pd.Series) -> Dict:
"""
Performs optimization to determine optimal battery capacity and operation strategy.

Parameters
----------
net_load : pd.Series
    The net load profile (load minus PV generation) time series data with shape of (n,2) and n is the number of time steps.
    The first column is the time index and the second column is the net load profile with time resolution of 1 hour.
    A pandas Series with DatetimeIndex is used for time series data.

Returns
-------
results : Dict
    A dictionary containing optimization results including:
    - battery_capacity: Optimal battery capacity in kWh
    - operation_strategy: Optimal battery operation strategy time series

Instructions
------------
Implement the optimization logic to minimize electricity costs by:
1. Determining optimal battery capacity
2. Determining optimal battery operation strategy

The specific optimization method depends on the implementing class.
"""
pass        
```
## Development

### Running Tests
```bash
python -m unittest tests/test_optimizer.py
```

## License

This project is licensed under the MIT License. Please refer to the [LICENSE](LICENSE) file for details.
