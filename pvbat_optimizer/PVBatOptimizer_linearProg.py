import pandas as pd
import gurobipy as gp
from typing import Dict, Tuple, List
from .config import OptimizerConfig
from .utils import OptimizerUtils
from gurobipy import GRB
import numpy as np
from datetime import datetime
from .PVBatOptimizer import PVBatOptimizer

class OptimizationError(Exception):
    """Custom exception for optimization failure"""
    pass

class PVBatOptimizer_linearProg(PVBatOptimizer):
    def __init__(self, config: OptimizerConfig):
        self.config = config
        
    def _get_billing_periods(self, time_index: pd.DatetimeIndex) -> Dict[str, List[int]]:
        """Divide time steps into billing periods for demand charge calculation
        
        This method groups time steps into billing periods (e.g., monthly, daily) for demand charge calculation.
        Demand charges are typically assessed based on the maximum power demand during each billing period.
        
        Args:
            time_index: DatetimeIndex of the time series data
            
        Returns:
            Dictionary mapping period IDs (e.g., '2023-01' for January 2023) to lists of time indices
        """
        billing_periods = {}
        
        if self.config.demand_charge_rate <= 0:
            # If demand charge rate is 0 or negative, return a single period
            billing_periods['all'] = list(range(len(time_index)))
            return billing_periods
        
        if self.config.billing_period == 'monthly':
            # Group by year and month
            current_period = None
            current_indices = []
            
            for i, timestamp in enumerate(time_index):
                period_id = f"{timestamp.year}-{timestamp.month}"
                
                if period_id != current_period:
                    if current_period is not None:
                        billing_periods[current_period] = current_indices
                    current_period = period_id
                    current_indices = [i]
                else:
                    current_indices.append(i)
            
            # Add the last period
            if current_period is not None and current_indices:
                billing_periods[current_period] = current_indices
                
        elif self.config.billing_period == 'daily':
            # Group by day
            for i, timestamp in enumerate(time_index):
                period_id = f"{timestamp.year}-{timestamp.month}-{timestamp.day}"
                if period_id not in billing_periods:
                    billing_periods[period_id] = []
                billing_periods[period_id].append(i)
                
        else:  # Default: treat all as one period
            billing_periods['all'] = list(range(len(time_index)))
            
        return billing_periods

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
        
        # Get billing periods for demand charge
        billing_periods = self._get_billing_periods(load_profile.index)
        
        # Add demand charge variables
        peak_demand = {}
        for period_id, period_indices in billing_periods.items():
            peak_demand[period_id] = model.addVar(name=f"peak_demand_{period_id}", lb=0)
        
        
        # Add constraints in bulk
        model.addConstrs(
            (pv_profile[t] * self.config.pv_capacity + battery_discharge[t] - battery_charge[t] +
             grid_import[t] - grid_export[t] >= load_profile[t]
             for t in range(T)),
            name="load_balance"
        )
        
        # Battery SOC constraints
        model.addConstr(battery_energy[0] == 0.5 * battery_capacity, name="initial_soc")
        model.addConstr(battery_energy[T-1] == 0.5 * battery_capacity, name="final_soc")
        
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
        
        # model.addConstrs(
        #     (battery_charge[t] * battery_discharge[t] == 0
        #      for t in range(T)),
        #     name="battery_power"
        # )

        
        # Battery energy balance constraints
        model.addConstrs(
            (battery_energy[t] == (1 - self.config.self_discharge_rate) * battery_energy[t-1] +
             self.config.battery_charge_efficiency * battery_charge[t] -
             battery_discharge[t] / self.config.battery_discharge_efficiency
             for t in range(1, T)),
            name="energy_balance"
        )
        
        crf = OptimizerUtils.calculate_crf(self.config.discount_rate, self.config.years)
        
        # Add demand charge constraints
        # Demand charge is based on the maximum power drawn from the grid in each billing period
        for period_id, period_indices in billing_periods.items():
            for t in period_indices:
                model.addConstr(peak_demand[period_id] >= grid_import[t], name=f"demand_charge_{period_id}_{t}")
        
        # Construct objective function using LinExpr
        obj = self.config.battery_cost_per_kwh * battery_capacity * crf
        
        # Energy cost
        for t in range(T):
            timestamp = load_profile.index[t]
            price = self.config.get_price_for_time(timestamp)
            
            obj += grid_import[t] * price
            obj -= grid_export[t] * price * self.config.electricity_sell_price_ratio
        
        # Demand charge cost
        if self.config.demand_charge_rate > 0:
            for period_id in billing_periods.keys():
                obj += peak_demand[period_id] * self.config.demand_charge_rate
        
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
        
        # Extract variable values for each time step
        for t in range(T):
            grid_import[t] = model.getVarByName(f"grid_import[{t}]").x
            grid_export[t] = model.getVarByName(f"grid_export[{t}]").x
            battery_charge[t] = model.getVarByName(f"battery_charge[{t}]").x
            battery_discharge[t] = model.getVarByName(f"battery_discharge[{t}]").x
            battery_energy[t] = model.getVarByName(f"battery_energy[{t}]").x
        
        # Get peak demand values
        billing_periods = self._get_billing_periods(time_index)
        peak_demand = {}
        
        if self.config.demand_charge_rate > 0:
            for period_id in billing_periods.keys():
                try:
                    peak_var = model.getVarByName(f"peak_demand_{period_id}")
                    peak_demand[period_id] = peak_var.x
                except Exception as e:
                    print(f"Warning: Could not extract peak demand for period {period_id}: {e}")
            
            # Calculate demand charges using utility function
            demand_charges = OptimizerUtils.calculate_demand_charges(
                peak_demand, self.config.demand_charge_rate)
        else:
            demand_charges = {"by_period": {}, "total": 0}
        
        return {
            "battery_capacity": battery_capacity,
            "total_cost": model.objVal,
            "grid_import": pd.Series(grid_import, index=time_index),
            "grid_export": pd.Series(grid_export, index=time_index),
            "battery_charge": pd.Series(battery_charge, index=time_index),
            "battery_discharge": pd.Series(battery_discharge, index=time_index),
            "battery_energy": pd.Series(battery_energy, index=time_index),
            "peak_demand": peak_demand,
            "demand_charges": demand_charges
        }