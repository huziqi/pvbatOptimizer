import pandas as pd
import gurobipy as gp
from typing import Dict, Tuple
from .config import OptimizerConfig
from .utils import OptimizerUtils
from gurobipy import GRB
import numpy as np

class OptimizationError(Exception):
    """优化求解失败时的自定义异常"""
    pass

class PVBatOptimizer:
    def __init__(self, config: OptimizerConfig):
        self.config = config

    def optimize(
        self,
        load_profile: pd.Series,    # Load profile
        pv_profile: pd.Series,      # PV generation profile  
        battery_capacity_range: Tuple[float, float] = (0, 100000) # Todo: Max battery capacity need to let user set
    ) -> Dict:
        """Optimize battery capacity"""
        model = self._create_model(load_profile, pv_profile, battery_capacity_range)
        model.optimize()
        
        # 直接返回结果，如果优化失败会在 _extract_results 中抛出异常
        return self._extract_results(model, load_profile.index)

    def _create_model(self, load_profile: pd.Series, pv_profile: pd.Series, 
                     battery_capacity_range: Tuple[float, float]) -> gp.Model:
        """Create optimization model"""
        model = gp.Model("PV_Battery_Optimization")
        
        # 设置Gurobi求解参数
        model.setParam('OutputFlag', 0)  # 关闭输出，减少IO开销
        # 选择优化方法
        # -1 = 自动选择
        #  0 = primal simplex
        #  1 = dual simplex
        #  2 = barrier
        #  3 = concurrent (多种方法并行)
        #  4 = deterministic concurrent
        #  5 = deterministic concurrent simplex
        model.setParam('Method', 3)  # 使用 barrier 方法
            
        T = len(load_profile)
        
        # Decision variables
        battery_capacity = model.addVar(
            name="battery_capacity",
            lb=battery_capacity_range[0],
            ub=battery_capacity_range[1]
        )
        
        # 批量创建变量
        battery_charge = model.addVars(T, name="battery_charge", lb=0)
        battery_discharge = model.addVars(T, name="battery_discharge", lb=0)
        battery_energy = model.addVars(T, name="battery_energy", lb=0)
        grid_import = model.addVars(T, name="grid_import", lb=0)
        grid_export = model.addVars(T, name="grid_export", lb=0)
        b_battery = model.addVars(T, vtype=gp.GRB.BINARY, name="b_battery")
        b_grid = model.addVars(T, vtype=gp.GRB.BINARY, name="b_grid")
        
        # 提前计算常量
        M = max(load_profile.max(), pv_profile.max()) * 2  # 更精确的大M值
        
        # 批量添加约束
        model.addConstrs(
            (pv_profile[t] * self.config.pv_capcity + battery_discharge[t] - battery_charge[t] +
             grid_import[t] - grid_export[t] >= load_profile[t]
             for t in range(T)),
            name="load_balance"
        )
        
        # 电池SOC约束
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
        
        # 充放电功率约束
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
        
        # 互斥约束
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
        
        # 电池能量平衡约束
        model.addConstrs(
            (battery_energy[t] == (1 - self.config.self_discharge_rate) * battery_energy[t-1] +
             self.config.battery_charge_efficiency * battery_charge[t] -
             battery_discharge[t] / self.config.battery_discharge_efficiency
             for t in range(1, T)),
            name="energy_balance"
        )
        
        crf = OptimizerUtils.calculate_crf(self.config.discount_rate, self.config.years)
        
        # 使用LinExpr构建目标函数
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
        # 检查模型是否成功求解
        if model.Status != GRB.OPTIMAL:
            raise OptimizationError(f"优化求解失败，状态码：{model.Status}，请检查模型设置和输入数据")
        else:
            print("优化求解成功")

        T = len(time_index)
        
        # 获取电池容量
        battery_capacity = model.getVarByName("battery_capacity").x
        
        # 获取时间序列变量
        grid_import = np.zeros(T)
        grid_export = np.zeros(T)
        battery_charge = np.zeros(T)
        battery_discharge = np.zeros(T)
        battery_energy = np.zeros(T)
        b_battery = np.zeros(T)
        b_grid = np.zeros(T)
        
        # 提取每个时间步的变量值
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