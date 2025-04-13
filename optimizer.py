import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
from pyomo.opt import SolverFactory
def optimizer(Netload_values, Tou_price, battery_cost, roundtrip_efficiency, 
                     self_discharge, charge_power_capacity, 
                     discharge_power_capacity, electricity_sell_price_ratio, CRF, PD_rate):

    # Pyomo optimizer
    model = pyo.ConcreteModel()

    time_periods = [t for t in range(len(Netload_values))]
    months = [m for m in range(12)]

    # Initialize Sets and Parameters 
    model.T = pyo.Set(initialize=time_periods) 
    model.M = pyo.Set(initialize=months) 
    model.Tou_price = pyo.Param(model.T, initialize=Tou_price)
    model.Netload = pyo.Param(model.T, initialize=Netload_values)

    # Variables
    model.Max_Cap = pyo.Var(within=pyo.NonNegativeReals)  # Battery size
    model.B_State = pyo.Var(model.T, within=pyo.NonNegativeReals)  # Electricity inside battery at each time step
    model.Charge_R = pyo.Var(model.T, within=pyo.NonNegativeReals)  # Electricity charged in battery at each time step
    model.Discharge_R = pyo.Var(model.T, within=pyo.NonNegativeReals)  # Electricity discharged from battery at each time step
    model.Grid_I = pyo.Var(model.T, within=pyo.NonNegativeReals)  # Electricity imported from grid at each time step
    model.Grid_E = pyo.Var(model.T, within=pyo.NonNegativeReals)  # Electricity exported to grid at each time step

    model.Grid_IMax  = pyo.Var(model.M,within=pyo.NonNegativeReals) # Peak demand charge at each time month

    # Objective function
    def obj_rule(model):
        # Investment cost
        first_part = (CRF * battery_cost * model.Max_Cap) 

        # Operation cost: sum over time periods
        second_part = sum((Tou_price[t] * model.Grid_I[t] - 
                        Tou_price[t] * electricity_sell_price_ratio * model.Grid_E[t]) for t in model.T)

        # Peak demand charge: sum over months
        third_part = sum(PD_rate * model.Grid_IMax[m] for m in model.M)

        # Combine all parts
        return first_part + second_part
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Constraints
    def batteryConstraint(model, t):
        if t == 0:
            return model.B_State[t] == model.B_State[t + len(Netload_values) - 1]
        else:
            return model.B_State[t] == (1 - self_discharge) * model.B_State[t - 1] + \
                   roundtrip_efficiency * model.Charge_R[t] - model.Discharge_R[t] / roundtrip_efficiency

    model.state_constr = pyo.Constraint(model.T, rule=batteryConstraint) 

    def stateMaxCharge(model, t):
        return model.B_State[t] <= model.Max_Cap

    model.state_max_c_constr = pyo.Constraint(model.T, rule=stateMaxCharge)

    def gridConstraint(model, t):
        return model.Grid_I[t] + model.Discharge_R[t] - model.Charge_R[t] - model.Grid_E[t] >= model.Netload[t]

    model.grid_import_constr = pyo.Constraint(model.T, rule=gridConstraint)

    def chargeMaxConstraint(model, t):
        return model.Charge_R[t] <= model.Max_Cap * charge_power_capacity

    model.charge_Max_constr = pyo.Constraint(model.T, rule=chargeMaxConstraint)

    def dischargeMaxConstraint(model, t):
        return model.Discharge_R[t] <= model.Max_Cap * discharge_power_capacity

    model.discharge_Max_constr = pyo.Constraint(model.T, rule=dischargeMaxConstraint)

    # Solve the model
    solver = pyo.SolverFactory('glpk')
    solver.options['log'] = 'grid.log'
    results = solver.solve(model, tee=True, keepfiles=True)
    pyo.assert_optimal_termination(results)

    return model
