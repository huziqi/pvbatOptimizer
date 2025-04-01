import pandas as pd
import gurobipy as gp
from typing import Dict, Tuple
from .config import OptimizerConfig
from .utils import OptimizerUtils
from gurobipy import GRB
import numpy as np

class OptimizationError(Exception):
    """Custom exception for optimization failure"""
    pass

class PVBatOptimizer:
    def __init__(self, config: OptimizerConfig):
        self.config = config

    def optimize(
        self,
        load_profile: pd.Series,    # Load profile
        pv_profile: pd.Series,      # PV generation profile  
        battery_capacity_range: Tuple[float, float] = (0, 100000) # Max battery capacity set by user
    ) -> Dict:
        """Optimize battery capacity"""
        model = self._create_model(load_profile, pv_profile, battery_capacity_range)
        model.optimize()
        
        # Return results directly; if optimization fails, an exception will be raised in _extract_results
        return self._extract_results(model, load_profile.index)

    def _create_model(self, load_profile: pd.Series, pv_profile: pd.Series, 
                     battery_capacity_range: Tuple[float, float]) -> gp.Model:
        """Create optimization model"""
        model = gp.Model("PV_Battery_Optimization")
        
        # Set Gurobi optimization parameters
        model.setParam('OutputFlag', 0)  # Disable output to reduce IO overhead
        model.setParam('Method', 3)  # Use barrier method
            
        T = len(load_profile)
        
        # Decision variables
        battery_capacity = model.addVar(
            name="battery_capacity",
            lb=battery_capacity_range[0],
            ub=battery_capacity_range[1]
        )
        
        # Create variables in bulk
        battery_charge = model.addVars(T, name="battery_charge", lb=0)
        battery_discharge = model.addVars(T, name="battery_discharge", lb=0)
        battery_energy = model.addVars(T, name="battery_energy", lb=0)
        grid_import = model.addVars(T, name="grid_import", lb=0)
        grid_export = model.addVars(T, name="grid_export", lb=0)
        b_battery = model.addVars(T, vtype=gp.GRB.BINARY, name="b_battery")
        b_grid = model.addVars(T, vtype=gp.GRB.BINARY, name="b_grid")
        
        # Pre-calculate constants
        M = max(load_profile.max(), pv_profile.max()) * 2  # More accurate big M value
        
        # Add constraints in bulk
        model.addConstrs(
            (pv_profile[t] * self.config.pv_capcity + battery_discharge[t] - battery_charge[t] +
             grid_import[t] - grid_export[t] >= load_profile[t]
             for t in range(T)),
            name="load_balance"
        )
        
        # Battery SOC constraints
        model.addConstr(battery_energy[0] == 0.5 * battery_capacity, name="initial_soc")
        
        model.addConstrs(
            (battery_energy[t] <= battery_capacity * self.config.soc_max
             for t in range(T)),
            name="soc_upper"
        )
        
        model.addConstrs(
            (battery_energy[t] >= battery_capacity * self.config.soc_min
             for t in range(T)),
            name="soc_lower"
        )
        
        # Charge and discharge power constraints
        model.addConstrs(
            (battery_charge[t] <= battery_capacity * self.config.charge_power_capacity
             for t in range(T)),
            name="charge_power"
        )
        
        model.addConstrs(
            (battery_discharge[t] <= battery_capacity * self.config.discharge_power_capacity
             for t in range(T)),
            name="discharge_power"
        )
        
        # Mutual exclusion constraints
        model.addConstrs(
            (battery_charge[t] <= b_battery[t] * M for t in range(T)),
            name="charge_binary"
        )
        model.addConstrs(
            (battery_discharge[t] <= (1 - b_battery[t]) * M for t in range(T)),
            name="discharge_binary"
        )
        
        model.addConstrs(
            (grid_import[t] <= b_grid[t] * M for t in range(T)),
            name="import_binary"
        )
        model.addConstrs(
            (grid_export[t] <= (1 - b_grid[t]) * M for t in range(T)),
            name="export_binary"
        )
        
        # Battery energy balance constraints
        model.addConstrs(
            (battery_energy[t] == (1 - self.config.self_discharge_rate) * battery_energy[t-1] +
             self.config.battery_charge_efficiency * battery_charge[t] -
             battery_discharge[t] / self.config.battery_discharge_efficiency
             for t in range(1, T)),
            name="energy_balance"
        )
        
        crf = OptimizerUtils.calculate_crf(self.config.discount_rate, self.config.years)
        
        # Construct objective function using LinExpr
        obj = self.config.battery_cost_per_kwh * battery_capacity * crf
        for t in range(T):
            hour = load_profile.index[t].hour
            price = self.config.tou_prices[hour]
            obj += grid_import[t] * price
            obj -= grid_export[t] * price * self.config.electricity_sell_price_ratio
        
        model.setObjective(obj, gp.GRB.MINIMIZE)
        
        return model

    def _extract_results(self, model: gp.Model, time_index: pd.DatetimeIndex) -> Dict:
        """Extract optimization results"""
        # Check if the model was solved successfully
        if model.Status != GRB.OPTIMAL:
            raise OptimizationError(f"Optimization failed, status code: {model.Status}, please check model settings and input data")
        else:
            print("Optimization successful")

        T = len(time_index)
        
        # Get battery capacity
        battery_capacity = model.getVarByName("battery_capacity").x
        
        # Get time series variables
        grid_import = np.zeros(T)
        grid_export = np.zeros(T)
        battery_charge = np.zeros(T)
        battery_discharge = np.zeros(T)
        battery_energy = np.zeros(T)
        b_battery = np.zeros(T)
        b_grid = np.zeros(T)
        
        # Extract variable values for each time step
        for t in range(T):
            grid_import[t] = model.getVarByName(f"grid_import[{t}]").x
            grid_export[t] = model.getVarByName(f"grid_export[{t}]").x
            battery_charge[t] = model.getVarByName(f"battery_charge[{t}]").x
            battery_discharge[t] = model.getVarByName(f"battery_discharge[{t}]").x
            battery_energy[t] = model.getVarByName(f"battery_energy[{t}]").x
            b_battery[t] = model.getVarByName(f"b_battery[{t}]").x
            b_grid[t] = model.getVarByName(f"b_grid[{t}]").x
        
        return {
            "battery_capacity": battery_capacity,
            "total_cost": model.objVal,
            "grid_import": pd.Series(grid_import, index=time_index),
            "grid_export": pd.Series(grid_export, index=time_index),
            "battery_charge": pd.Series(battery_charge, index=time_index),
            "battery_discharge": pd.Series(battery_discharge, index=time_index),
            "battery_energy": pd.Series(battery_energy, index=time_index),
            "b_battery": pd.Series(b_battery, index=time_index),
            "b_grid": pd.Series(b_grid, index=time_index)
        }