from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class OptimizerConfig:
    """PV-Battery system optimization configuration"""
    
    # Required economic parameters
    tou_prices: Dict[int, float]    # Time-of-use prices {hour: price}
    pv_capcity: float          # Installed PV capacity
    battery_cost_per_kwh: float    # Battery cost per kWh
    
    # Project parameters
    years: int = 25                # Project years
    discount_rate: float = 0.07    # Discount rate
    electricity_sell_price_ratio: float = 0.6  # Electricity sell price ratio
    
    # Battery parameters
    soc_max: float = 0.9          # Maximum state of charge
    soc_min: float = 0.2          # Minimum state of charge
    charge_power_capacity: float = 0.25    # Maximum charge power to capacity ratio
    discharge_power_capacity: float = 0.25  # Maximum discharge power to capacity ratio
    battery_charge_efficiency: float = 0.95    # Battery charge efficiency
    battery_discharge_efficiency: float = 0.95  # Battery discharge efficiency
    self_discharge_rate: float = 0.000002  # Self-discharge rate per time step
    max_battery_capacity: float = 100000  # Maximum battery capacity
    
    # Optional parameters
    pv_degradation_rate: float = 0.005  # PV degradation rate
    battery_replacement_year: Optional[int] = 10  # Battery replacement year
    om_cost_ratio: float = 0.02  # O&M cost ratio
    
    def __post_init__(self):
        """Validate configuration parameters"""
        # Validate time-of-use prices
        if not self.tou_prices or not all(0 <= h <= 23 for h in self.tou_prices.keys()):
            raise ValueError("Time-of-use prices must include valid hours (0-23)")
        
        if not all(p >= 0 for p in self.tou_prices.values()):
            raise ValueError("Prices must be non-negative")
            
        # Validate cost parameters
        if self.pv_capcity <= 0:
            raise ValueError("PV capacity must be positive")
            
        if self.battery_cost_per_kwh <= 0:
            raise ValueError("Battery cost must be positive")
            
        # Validate project parameters
        if self.years <= 0:
            raise ValueError("Project years must be positive")
            
        if not 0 < self.discount_rate < 1:
            raise ValueError("Discount rate must be between 0 and 1")
            
        if not 0 < self.electricity_sell_price_ratio <= 1:
            raise ValueError("Electricity sell price ratio must be between 0 and 1")
            
        # Validate battery parameters
        if not 0 <= self.soc_min < self.soc_max <= 1:
            raise ValueError("SOC range must be between 0 and 1, and min must be less than max")
            
        if not 0 < self.charge_power_capacity <= 1:
            raise ValueError("Charge power ratio must be between 0 and 1")
            
        if not 0 < self.discharge_power_capacity <= 1:
            raise ValueError("Discharge power ratio must be between 0 and 1")
            
        if not 0 < self.battery_charge_efficiency <= 1:
            raise ValueError("Battery charge efficiency must be between 0 and 1")
            
        if not 0 < self.battery_discharge_efficiency <= 1:
            raise ValueError("Battery discharge efficiency must be between 0 and 1")
            
        if not 0 <= self.self_discharge_rate < 1:
            raise ValueError("Self-discharge rate must be between 0 and 1")
            
        # Validate optional parameters
        if not 0 <= self.pv_degradation_rate < 1:
            raise ValueError("PV degradation rate must be between 0 and 1")
            
        if self.battery_replacement_year is not None and self.battery_replacement_year <= 0:
            raise ValueError("Battery replacement year must be positive")
            
        if not 0 <= self.om_cost_ratio < 1:
            raise ValueError("O&M cost ratio must be between 0 and 1")

    @property
    def battery_params(self) -> dict:
        """Return a dictionary of battery-related parameters (for backward compatibility)"""
        return {
            "soc_max": self.soc_max,
            "soc_min": self.soc_min,
            "charge_power_capacity": self.charge_power_capacity,
            "discharge_power_capacity": self.discharge_power_capacity,
            "charge_efficiency": self.battery_charge_efficiency,
            "discharge_efficiency": self.battery_discharge_efficiency,
            "self_discharge_rate": self.self_discharge_rate,
        }