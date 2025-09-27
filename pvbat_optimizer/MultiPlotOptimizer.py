import pandas as pd
import gurobipy as gp
from typing import Dict, List, Tuple
from .config import OptimizerConfig
from .utils import OptimizerUtils
from gurobipy import GRB
import numpy as np
from .PVBatOptimizer_linearProg import PVBatOptimizer_linearProg, OptimizationError


class MultiPlotOptimizer:
    """Multi-plot battery capacity optimization with total capacity constraint"""
    
    def __init__(self, config: OptimizerConfig, total_battery_capacity: float, force: bool = False):
        """
        Initialize multi-plot optimizer
        
        Args:
            config: Optimizer configuration
            total_battery_capacity: Total battery capacity constraint (kWh)
        """
        self.config = config
        self.total_battery_capacity = total_battery_capacity
        self.force = force
        self.single_optimizer = PVBatOptimizer_linearProg(config)
    
    def optimize_multi_plots(self, net_loads: Dict[str, pd.Series]) -> Dict:
        """
        Optimize battery capacity allocation across multiple plots
        
        Args:
            net_loads: Dictionary mapping plot names to net load time series
            
        Returns:
            Dictionary containing optimization results for all plots
        """
        model = self._create_multi_plot_model(net_loads)
        model.optimize()
        return self._extract_multi_plot_results(model, net_loads)
    
    def _create_multi_plot_model(self, net_loads: Dict[str, pd.Series]) -> gp.Model:
        """Create multi-plot optimization model"""
        model = gp.Model("MultiPlot_LP_Model")
        
        # Set Gurobi optimization parameters
        model.setParam('OutputFlag', 0)
        model.setParam('Method', 3)
        
        plots = list(net_loads.keys())
        T = len(next(iter(net_loads.values())))  # Assume all series have same length
        
        # Verify all net_loads have the same time index
        time_index = next(iter(net_loads.values())).index
        for plot_name, net_load in net_loads.items():
            if len(net_load) != T or not net_load.index.equals(time_index):
                raise ValueError(f"All net load series must have the same time index. Plot {plot_name} has different index.")
        
        # Decision variables for each plot
        battery_capacity = {}
        battery_charge = {}
        battery_discharge = {}
        battery_energy = {}
        grid_import = {}
        grid_export = {}
        
        for plot in plots:
            battery_capacity[plot] = model.addVar(
                name=f"battery_capacity_{plot}",
                lb=0,
                ub=self.total_battery_capacity  # Individual plot can't exceed total
            )
            
            battery_charge[plot] = model.addVars(T, name=f"battery_charge_{plot}", lb=0)
            battery_discharge[plot] = model.addVars(T, name=f"battery_discharge_{plot}", lb=0)
            battery_energy[plot] = model.addVars(T, name=f"battery_energy_{plot}", lb=0)
            grid_import[plot] = model.addVars(T, name=f"grid_import_{plot}", lb=0)
            grid_export[plot] = model.addVars(T, name=f"grid_export_{plot}", lb=0)
        
        # Total capacity constraint
        if self.force:
            model.addConstr(
                gp.quicksum(battery_capacity[plot] for plot in plots) == self.total_battery_capacity,
            name="total_capacity_constraint"
            )
        else:
            model.addConstr(
                gp.quicksum(battery_capacity[plot] for plot in plots) <= self.total_battery_capacity,
                name="total_capacity_constraint"
            )
        
        # Get billing periods for demand charge (using first plot's time index)
        billing_periods = self.single_optimizer._get_billing_periods(time_index)
        
        # Add demand charge variables for each plot
        peak_demand = {}
        for plot in plots:
            peak_demand[plot] = {}
            for period_id in billing_periods.keys():
                peak_demand[plot][period_id] = model.addVar(
                    name=f"peak_demand_{plot}_{period_id}", lb=0
                )
        
        # Add constraints for each plot
        for plot in plots:
            net_load = net_loads[plot]
            
            # Load balance constraints
            model.addConstrs(
                (battery_discharge[plot][t] - battery_charge[plot][t] + 
                 grid_import[plot][t] - grid_export[plot][t] == net_load.iloc[t]
                 for t in range(T)),
                name=f"load_balance_{plot}"
            )
            
            # Battery SOC constraints
            model.addConstr(
                battery_energy[plot][0] == 0.5 * battery_capacity[plot],
                name=f"initial_soc_{plot}"
            )
            model.addConstr(
                battery_energy[plot][T-1] == 0.5 * battery_capacity[plot],
                name=f"final_soc_{plot}"
            )
            
            model.addConstrs(
                (battery_energy[plot][t] <= battery_capacity[plot] * self.config.soc_max
                 for t in range(T)),
                name=f"soc_upper_{plot}"
            )
            
            model.addConstrs(
                (battery_energy[plot][t] >= battery_capacity[plot] * self.config.soc_min
                 for t in range(T)),
                name=f"soc_lower_{plot}"
            )
            
            # Charge and discharge power constraints
            model.addConstrs(
                (battery_charge[plot][t] <= 
                 battery_capacity[plot] * self.config.charge_power_capacity * self.config.decision_step
                 for t in range(T)),
                name=f"charge_power_{plot}"
            )
            
            model.addConstrs(
                (battery_discharge[plot][t] <= 
                 battery_capacity[plot] * self.config.discharge_power_capacity * self.config.decision_step
                 for t in range(T)),
                name=f"discharge_power_{plot}"
            )
            
            # Battery energy balance constraints
            model.addConstrs(
                (battery_energy[plot][t] == 
                 (1 - self.config.self_discharge_rate) * battery_energy[plot][t-1] +
                 self.config.battery_charge_efficiency * battery_charge[plot][t] * self.config.decision_step -
                 battery_discharge[plot][t] * self.config.decision_step / self.config.battery_discharge_efficiency
                 for t in range(1, T)),
                name=f"energy_balance_{plot}"
            )
            
            # Demand charge constraints
            for period_id, period_indices in billing_periods.items():
                for t in period_indices:
                    model.addConstr(
                        peak_demand[plot][period_id] >= grid_import[plot][t],
                        name=f"demand_charge_{plot}_{period_id}_{t}"
                    )
        
        # Construct objective function
        crf = OptimizerUtils.calculate_crf(self.config.discount_rate, self.config.years)
        
        # Battery construction cost
        obj = gp.quicksum(
            self.config.battery_cost_per_kwh * battery_capacity[plot] * crf
            for plot in plots
        )
        
        # Energy cost for all plots
        for plot in plots:
            for t in range(T):
                timestamp = time_index[t]
                price = self.config.get_price_for_time(timestamp)
                
                obj += grid_import[plot][t] * price * self.config.decision_step
                obj -= (grid_export[plot][t] * price * 
                       self.config.electricity_sell_price_ratio * self.config.decision_step)
        
        # Demand charge cost for all plots
        if self.config.demand_charge_rate > 0:
            for plot in plots:
                for period_id in billing_periods.keys():
                    obj += peak_demand[plot][period_id] * self.config.demand_charge_rate
        
        model.setObjective(obj, gp.GRB.MINIMIZE)
        
        return model
    
    def _extract_multi_plot_results(self, model: gp.Model, net_loads: Dict[str, pd.Series]) -> Dict:
        """Extract multi-plot optimization results"""
        if model.Status != GRB.OPTIMAL:
            raise OptimizationError(f"Multi-plot optimization failed, status code: {model.Status}")
        
        print("Multi-plot optimization successful")
        
        plots = list(net_loads.keys())
        time_index = next(iter(net_loads.values())).index
        T = len(time_index)
        
        results = {
            "total_cost": model.objVal,
            "plots": {},
            "total_battery_capacity": 0,
            "capacity_allocation": {}
        }
        
        # Extract results for each plot
        for plot in plots:
            # Get battery capacity
            battery_capacity = model.getVarByName(f"battery_capacity_{plot}").x
            results["capacity_allocation"][plot] = battery_capacity
            results["total_battery_capacity"] += battery_capacity
            
            # Get time series variables
            grid_import = np.zeros(T)
            grid_export = np.zeros(T)
            battery_charge = np.zeros(T)
            battery_discharge = np.zeros(T)
            battery_energy = np.zeros(T)
            
            for t in range(T):
                grid_import[t] = model.getVarByName(f"grid_import_{plot}[{t}]").x
                grid_export[t] = model.getVarByName(f"grid_export_{plot}[{t}]").x
                battery_charge[t] = model.getVarByName(f"battery_charge_{plot}[{t}]").x
                battery_discharge[t] = model.getVarByName(f"battery_discharge_{plot}[{t}]").x
                battery_energy[t] = model.getVarByName(f"battery_energy_{plot}[{t}]").x
            
            # Get peak demand values
            billing_periods = self.single_optimizer._get_billing_periods(time_index)
            peak_demand = {}
            
            if self.config.demand_charge_rate > 0:
                for period_id in billing_periods.keys():
                    try:
                        peak_var = model.getVarByName(f"peak_demand_{plot}_{period_id}")
                        peak_demand[period_id] = peak_var.x
                    except Exception as e:
                        print(f"Warning: Could not extract peak demand for plot {plot}, period {period_id}: {e}")
                
                demand_charges = OptimizerUtils.calculate_demand_charges(
                    peak_demand, self.config.demand_charge_rate)
            else:
                demand_charges = {"by_period": {}, "total": 0}
            
            # Calculate cost savings for this plot
            net_load = net_loads[plot]
            original_grid_import = pd.Series(np.maximum(net_load.values, 0), index=time_index)
            original_energy_cost = 0
            new_energy_cost = 0
            
            for t in range(T):
                timestamp = time_index[t]
                price = self.config.get_price_for_time(timestamp)
                
                original_energy_cost += original_grid_import[t] * price * self.config.decision_step
                new_energy_cost += grid_import[t] * price * self.config.decision_step
                new_energy_cost -= (grid_export[t] * price * 
                                  self.config.electricity_sell_price_ratio * self.config.decision_step)
            
            # Calculate original and new demand costs
            original_demand_cost = 0
            new_demand_cost = demand_charges["total"]
            
            if self.config.demand_charge_rate > 0:
                original_peak_demand = {}
                for period_id, period_indices in billing_periods.items():
                    period_peak = 0
                    for t in period_indices:
                        period_peak = max(period_peak, original_grid_import[t])
                    original_peak_demand[period_id] = period_peak
                
                original_demand_charges = OptimizerUtils.calculate_demand_charges(
                    original_peak_demand, self.config.demand_charge_rate)
                original_demand_cost = original_demand_charges["total"]
            
            annual_savings = (original_energy_cost + original_demand_cost) - (new_energy_cost + new_demand_cost)
            battery_construction_cost = battery_capacity * self.config.battery_cost_per_kwh
            
            results["plots"][plot] = {
                "battery_capacity": battery_capacity,
                "grid_import": pd.Series(grid_import, index=time_index),
                "grid_export": pd.Series(grid_export, index=time_index),
                "battery_charge": pd.Series(battery_charge, index=time_index),
                "battery_discharge": pd.Series(battery_discharge, index=time_index),
                "battery_energy": pd.Series(battery_energy, index=time_index),
                "peak_demand": peak_demand,
                "demand_charges": demand_charges,
                "annual_savings": annual_savings,
                "battery_construction_cost": battery_construction_cost,
                "original_total_cost": original_energy_cost + original_demand_cost,
                "optimized_total_cost": new_energy_cost + new_demand_cost
            }
        
        # Print summary
        print(f"\nMulti-plot Optimization Results:")
        print(f"Total battery capacity constraint: {self.total_battery_capacity:.2f} kWh")
        print(f"Total allocated capacity: {results['total_battery_capacity']:.2f} kWh")
        print(f"Total optimization cost: {results['total_cost']:.2f}")
        
        print(f"\nCapacity allocation:")
        for plot, capacity in results["capacity_allocation"].items():
            percentage = (capacity / results['total_battery_capacity']) * 100
            print(f"  {plot}: {capacity:.2f} kWh ({percentage:.1f}%)")
        
        return results
