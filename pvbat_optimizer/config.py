class OptimizerConfig:
    def __init__(
        self,
        tou_prices: dict,          # 分时电价 {hour: price}
        pv_cost_per_kw: float,     # 光伏单位千瓦成本
        battery_cost_per_kwh: float,# 电池单位千瓦时成本
        years: int = 25,           # 项目年限
        discount_rate: float = 0.07,# 贴现率
        electricity_sell_price_ratio: float = 0.6, # 上网电价比例
    ):
        self.tou_prices = tou_prices
        self.pv_cost_per_kw = pv_cost_per_kw
        self.battery_cost_per_kwh = battery_cost_per_kwh
        self.years = years
        self.discount_rate = discount_rate
        self.electricity_sell_price_ratio = electricity_sell_price_ratio
        
        # 电池参数默认值
        self.battery_params = {
            "min_soc": 0.1,
            "charge_efficiency": 0.95,
            "discharge_efficiency": 0.95,
            "charge_power_capacity": 0.25,
            "discharge_power_capacity": 0.25,
            "soc_max": 0.9,
            "soc_min": 0.2,
            "self_discharge_rate": 0.000002,
        }