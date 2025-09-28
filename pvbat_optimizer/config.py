from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd

@dataclass
class OptimizerConfig:
    """PV-Battery system optimization configuration"""
    
    # Required economic parameters
    tou_prices: Dict[int, float] = None    # Original format of time-of-use prices {hour: price} 
    """ For an example:
    tou_prices = {  # Time-of-use prices, refer to UCSD data
        0: 0.152, 1: 0.143, 2: 0.137, 3: 0.137, 4: 0.145, 5: 0.172,
        6: 0.204, 7: 0.185, 8: 0.144, 9: 0.123, 10: 0.113, 11: 0.109,
        12: 0.110, 13: 0.116, 14: 0.127, 15: 0.148, 16: 0.181, 17: 0.244,
        18: 0.279, 19: 0.294, 20: 0.249, 21: 0.213, 22: 0.181, 23: 0.163
    }
    """
    
    # New price format (optional)
    peak_price: Optional[float] = 1.39     # Peak price
    high_price: Optional[float] = 1.16     # High price
    flat_price: Optional[float] = 0.70     # Flat price
    valley_price: Optional[float] = 0.30   # Valley price
    
    pv_capacity: float = 0          # Installed PV capacity
    battery_cost_per_kwh: float = 0    # Battery cost per CNY/kWh
    
    # Project parameters
    years: int = 25                # Project years
    discount_rate: float = 0.07    # Discount rate
    electricity_sell_price_ratio: float = 0.7  # Electricity sell price ratio
    
    # Battery parameters
    soc_max: float = 0.8          # Maximum state of charge
    soc_min: float = 0.2          # Minimum state of charge
    charge_power_capacity: float = 0.25    # Maximum charge power to capacity ratio
    discharge_power_capacity: float = 0.25  # Maximum discharge power to capacity ratio
    battery_charge_efficiency: float = 0.9    # Battery charge efficiency
    battery_discharge_efficiency: float = 0.9  # Battery discharge efficiency
    self_discharge_rate: float = 0.000002  # Self-discharge rate per time step
    max_battery_capacity: float = 100000  # Maximum battery capacity
    
    # Optional parameters
    battery_replacement_year: Optional[int] = 10  # Battery replacement year
    om_cost_ratio: float = 0.02  # O&M cost ratio
    
    # Demand charge parameters
    demand_charge_rate: float = 0.0  # Demand charge rate (CNY/kW)
    billing_period: str = 'monthly'  # Billing period for demand charge ('monthly', 'daily', etc.)
    
    # Set whether to use seasonal prices
    use_seasonal_prices: bool = False  # Default to using original tou_prices format

    # decision step
    decision_step: float = 0.25  # Decision step

    # pv cost
    pv_cost: float = 0  # PV cost
    
    def __post_init__(self):
        """Validate configuration parameters"""
        # Check price format
        if self.use_seasonal_prices:
            # When using seasonal prices, all prices must be provided
            if None in [self.peak_price, self.high_price, self.flat_price, self.valley_price]:
                raise ValueError("When using seasonal prices, all price tiers must be provided")
            if not all(p > 0 for p in [self.peak_price, self.high_price, self.flat_price, self.valley_price] if p is not None):
                raise ValueError("All price values must be positive")
        else:
            # When using the original format, tou_prices must be provided
            if not self.tou_prices:
                raise ValueError("Time-of-use prices must be provided when not using seasonal prices")
            if not all(0 <= h <= 23 for h in self.tou_prices.keys()):
                raise ValueError("Time-of-use prices must include valid hours (0-23)")
            if not all(p >= 0 for p in self.tou_prices.values()):
                raise ValueError("Prices must be non-negative")
            
        # Validate cost parameters
        if self.pv_capacity < 0:
            raise ValueError("PV capacity must be positive")
            
        if self.battery_cost_per_kwh <= 0:
            raise ValueError("Battery cost must be positive")
            
        # Validate project parameters
        if self.years <= 0:
            raise ValueError("Project years must be positive")
            
        if not 0 < self.discount_rate < 1:
            raise ValueError("Discount rate must be between 0 and 1")
            
        if not 0 <= self.electricity_sell_price_ratio <= 1:
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
    
    def get_price_for_time(self, timestamp: pd.Timestamp) -> float:
        """Get the corresponding price based on time
        
        Args:
            timestamp: Timestamp
            
        Returns:
            Corresponding price for the time period
        """
        # If not using seasonal prices, use the original tou_prices
        if not self.use_seasonal_prices:
            hour = timestamp.hour
            return self.tou_prices[hour]
        
        # Using seasonal prices
        month = timestamp.month
        hour = timestamp.hour
        
        # Determine price based on month
        if month in [7, 8]:  # July, August - Peak months type 1
            return self._get_peak_month_type1_price(hour)
        elif month in [1, 12]:  # January, December - Peak months type 2
            return self._get_peak_month_type2_price(hour)
        else:  # Other months - Non-peak months
            return self._get_non_peak_month_price(hour)
    
    def _get_peak_month_type1_price(self, hour: int) -> float:
        """Get price for July, August (Peak months type 1)
        
        Args:
            hour: Hour (0-23)
            
        Returns:
            Corresponding price for the time period
        """
        if 20 <= hour <= 23:  # Peak: 18:00-22:00
            return self.peak_price
        elif 16 <= hour < 19:  # High: 11:00-14:00, 22:00-23:00
            return self.high_price
        elif 6 <= hour < 11 or 14 <= hour < 15:  # Flat: 7:00-11:00, 14:00-18:00
            return self.flat_price
        else:  # Valley: 23:00-next day 7:00 (i.e., 23:00-0:00, 0:00-7:00)
            return self.valley_price
    
    def _get_peak_month_type2_price(self, hour: int) -> float:
        """Get price for January, December (Peak months type 2)
        
        Args:
            hour: Hour (0-23)
            
        Returns:
            Corresponding price for the time period
        """
        if 18 <= hour <= 21:  # Peak: 18:00-22:00
            return self.peak_price
        elif 16 <= hour <= 17 or 22 <= hour <= 23:  # High: 11:00-14:00, 22:00-23:00
            return self.high_price
        elif 6 <= hour <= 11 or 12 <= hour <= 13:  # Flat: 7:00-11:00, 14:00-18:00
            return self.flat_price
        else:  # Valley: 23:00-next day 7:00 (i.e., 23:00-0:00, 0:00-7:00)
            return self.valley_price
    
    def _get_non_peak_month_price(self, hour: int) -> float:
        """Get price for non-peak months (February, March, April, May, June, September, October, November)
        
        Args:
            hour: Hour (0-23)
            
        Returns:
            Corresponding price for the time period
        """
        if 16 <= hour <= 23:  # High: 18:00-23:00
            return self.high_price
        elif 6 <= hour <= 11 or 14 <= hour <= 15:  # Flat: 7:00-11:00, 14:00-18:00
            return self.flat_price
        else:  # Valley: 23:00-next day 7:00 (i.e., 23:00-0:00, 0:00-7:00)
            return self.valley_price