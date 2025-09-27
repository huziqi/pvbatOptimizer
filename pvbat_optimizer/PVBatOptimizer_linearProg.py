from operator import ne
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
        net_load: pd.Series
    ) -> Dict:
        """Optimize battery capacity"""
        model = self._create_model(net_load)
        model.optimize()
        return self._extract_results(model, net_load.index, net_load)

    def _create_model(self, net_load: pd.Series) -> gp.Model:
        """Create optimization model"""
        model = gp.Model("LP_Model")
        
        # Set Gurobi optimization parameters
        model.setParam('OutputFlag', 0)  # Disable output to reduce IO overhead
        model.setParam('Method', 3)  # Use barrier method
        # model.setParam("NonConvex", 0)  # Force linear algorithm (disable quadratic/nonlinear terms)
            
        T = len(net_load)
        
        # Decision variables
        battery_capacity = model.addVar(
            name="battery_capacity",
            lb=0,
            ub=self.config.max_battery_capacity
        )
        
        # Create variables in bulk
        battery_charge = model.addVars(T, name="battery_charge", lb=0)
        battery_discharge = model.addVars(T, name="battery_discharge", lb=0)
        battery_energy = model.addVars(T, name="battery_energy", lb=0)
        grid_import = model.addVars(T, name="grid_import", lb=0)
        grid_export = model.addVars(T, name="grid_export", lb=0)
        
        # Get billing periods for demand charge
        billing_periods = self._get_billing_periods(net_load.index)
        
        # Add demand charge variables
        peak_demand = {}
        for period_id, period_indices in billing_periods.items():
            peak_demand[period_id] = model.addVar(name=f"peak_demand_{period_id}", lb=0)
        
        
        # Add constraints in bulk
        model.addConstrs(
            (battery_discharge[t] - battery_charge[t] + grid_import[t] - grid_export[t] == net_load[t]
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
            (battery_charge[t] <= battery_capacity * self.config.charge_power_capacity * self.config.decision_step
             for t in range(T)),
            name="charge_power"
        )
        
        model.addConstrs(
            (battery_discharge[t] <= battery_capacity * self.config.discharge_power_capacity * self.config.decision_step
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
             self.config.battery_charge_efficiency * battery_charge[t] * self.config.decision_step -
             battery_discharge[t] * self.config.decision_step / self.config.battery_discharge_efficiency    
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
            timestamp = net_load.index[t]
            price = self.config.get_price_for_time(timestamp)
            
            obj += grid_import[t] * price * self.config.decision_step       
            obj -= grid_export[t] * price * self.config.electricity_sell_price_ratio * self.config.decision_step
        
        # Demand charge cost
        if self.config.demand_charge_rate > 0:
            for period_id in billing_periods.keys():
                obj += peak_demand[period_id] * self.config.demand_charge_rate
        
        model.setObjective(obj, gp.GRB.MINIMIZE)
        
        return model
    def _extract_results(self, model: gp.Model, time_index: pd.DatetimeIndex, net_load: pd.Series) -> Dict:
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
        
        # Calculate annual cost savings
        # 1. Calculate original energy cost (without battery system)
        original_grid_import = pd.Series(np.maximum(net_load.values, 0), index=time_index)
        original_energy_cost = 0
        new_energy_cost = 0
        new_energy_cost_without_demand_charge = 0
        sell_energy_profit = 0

        for t in range(T):
            timestamp = time_index[t]
            price = self.config.get_price_for_time(timestamp)

            original_energy_cost += original_grid_import[t] * price * self.config.decision_step

            new_energy_cost += grid_import[t] * price * self.config.decision_step
            new_energy_cost_without_demand_charge += grid_import[t] * price * self.config.decision_step
            new_energy_cost -= grid_export[t] * price * self.config.electricity_sell_price_ratio * self.config.decision_step
            sell_energy_profit += grid_export[t] * price * self.config.electricity_sell_price_ratio * self.config.decision_step
        # 2. Calculate original demand charges (without battery system)
        original_demand_cost = 0
        new_demand_cost = demand_charges["total"]
        
        if self.config.demand_charge_rate > 0:
            # Calculate original peak demand for each billing period
            original_peak_demand = {}
            # print("\nBilling Periods Information:")
            for period_id, period_indices in billing_periods.items():
                # print(f"Period ID: {period_id}")
                # print(f"Period Indices: {period_indices[:10]}...")  # 只显示前10个索引
                # print(f"Number of time points in period: {len(period_indices)}")
                period_peak = 0
                for t in period_indices:
                    period_peak = max(period_peak, original_grid_import[t])
                original_peak_demand[period_id] = period_peak
                # print(f"Peak demand for period {period_id}: {period_peak:.2f} kW")
            
            # Calculate original demand charges
            original_demand_charges = OptimizerUtils.calculate_demand_charges(
                original_peak_demand, self.config.demand_charge_rate)
            original_demand_cost = original_demand_charges["total"]
        
        # Print cost comparison
        print("\nElectricity Cost Comparison:")
        print(f"Original usage cost: {original_energy_cost:.2f}")
        print(f"Optimized usage cost: {new_energy_cost:.2f}")
        print(f"Original demand cost: {original_demand_cost:.2f}")
        print(f"Optimized demand cost: {new_demand_cost:.2f}")
        print(f"Total original cost: {original_energy_cost + original_demand_cost:.2f}")
        print(f"Total optimized cost: {new_energy_cost + new_demand_cost:.2f}")
        print(f"usage cost savings: {original_energy_cost - new_energy_cost:.2f}")
        print(f"Demand cost savings: {original_demand_cost - new_demand_cost:.2f}")
        print(f"Total cost savings: {(original_energy_cost + original_demand_cost) - (new_energy_cost + new_demand_cost):.2f}")
        print(f"Total cost ratio: {((original_energy_cost + original_demand_cost) - (new_energy_cost + new_demand_cost))/(original_energy_cost + original_demand_cost)*100:.2f}%")
        print(f"Sell energy profit: {sell_energy_profit:.2f}")
        print(f"Sell energy profit ratio: {sell_energy_profit/(original_energy_cost+original_demand_cost)*100:.2f}%")
        print(f"Optimized energy cost without demand charge: {new_energy_cost_without_demand_charge:.2f}")
        print(f"profit: {new_energy_cost_without_demand_charge+new_demand_cost+sell_energy_profit:.2f}")
        # 3. Calculate annual savings (including both energy and demand savings)
        annual_savings = (original_energy_cost + original_demand_cost) - (new_energy_cost + new_demand_cost) 

        # 4. Battery construction cost
        battery_construction_cost = battery_capacity * self.config.battery_cost_per_kwh
        
        return {
            "battery_capacity": battery_capacity,
            "total_cost": model.objVal,
            "grid_import": pd.Series(grid_import, index=time_index),
            "grid_export": pd.Series(grid_export, index=time_index),
            "battery_charge": pd.Series(battery_charge, index=time_index),
            "battery_discharge": pd.Series(battery_discharge, index=time_index),
            "battery_energy": pd.Series(battery_energy, index=time_index),
            "peak_demand": peak_demand,
            "demand_charges": demand_charges,
            "annual_savings": annual_savings,
            "battery_construction_cost": battery_construction_cost,
            "operational_cost_saving_ratio": (original_energy_cost+original_demand_cost - new_energy_cost - new_demand_cost)/(original_energy_cost+original_demand_cost),
            "sell_energy_profit": sell_energy_profit,
            "sell_energy_profit_ratio": sell_energy_profit/(original_energy_cost+original_demand_cost),
            "new_energy_cost_without_demand_charge": new_energy_cost_without_demand_charge,
            "optimized_energy_cost": new_energy_cost,
            "optimized_demand_cost": new_demand_cost,
            "optimized_total_cost": new_energy_cost + new_demand_cost
            }