from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd

@dataclass
class OptimizerConfig:
    """PV-Battery system optimization configuration"""
    
    # Required economic parameters
    tou_prices: Dict[int, float] = None    # Original format of time-of-use prices {hour: price}
    
    # New price format (optional)
    peak_price: Optional[float] = 1.20081     # Peak price
    flat_price: Optional[float] = 0.76785     # Flat price
    valley_price: Optional[float] = 0.33489   # Valley price
    
    pv_capacity: float = 0          # Installed PV capacity
    battery_cost_per_kwh: float = 0    # Battery cost per kWh
    
    # Project parameters
    years: int = 25                # Project years
    discount_rate: float = 0.07    # Discount rate
    electricity_sell_price_ratio: float = 0.7  # Electricity sell price ratio
    
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
    battery_replacement_year: Optional[int] = 10  # Battery replacement year
    om_cost_ratio: float = 0.02  # O&M cost ratio
    
    # Set whether to use seasonal prices
    use_seasonal_prices: bool = False  # Default to using original tou_prices format
    
    def __post_init__(self):
        """Validate configuration parameters"""
        # Check price format
        if self.use_seasonal_prices:
            # When using seasonal prices, all three prices must be provided
            if None in [self.peak_price, self.flat_price, self.valley_price]:
                raise ValueError("When using seasonal prices, all three price tiers must be provided")
            if not all(p > 0 for p in [self.peak_price, self.flat_price, self.valley_price] if p is not None):
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
        
        # Determine if it's summer, winter, or other months
        if month in [7, 8]:  # Summer months (July-August)
            return self._get_summer_price(hour)
        elif month in [1, 12]:  # Winter months (January, December)
            return self._get_winter_price(hour)
        else:  # Other months
            return self._get_other_price(hour)
    
    def _get_summer_price(self, hour: int) -> float:
        """Get summer price
        
        Args:
            hour: Hour (0-23)
            
        Returns:
            Corresponding price for the time period
        """
        if 20 <= hour <= 23:  # Peak: 20:00-24:00
            return self.peak_price
        elif 16 <= hour < 20:  # High: 16:00-20:00
            return self.peak_price
        elif hour == 0 or 6 <= hour < 12 or 15 <= hour < 16:  # Flat: 24:00-1:00, 6:00-12:00, 15:00-16:00
            return self.flat_price
        else:  # Valley: 1:00-6:00, 12:00-15:00
            return self.valley_price
    
    def _get_winter_price(self, hour: int) -> float:
        """Get winter price
        
        Args:
            hour: Hour (0-23)
            
        Returns:
            Corresponding price for the time period
        """
        if 18 <= hour < 21:  # Peak: 18:00-21:00
            return self.peak_price
        elif 15 <= hour < 18 or 21 <= hour < 23:  # High: 15:00-18:00, 21:00-23:00
            return self.peak_price
        elif 7 <= hour < 15:  # Flat: 7:00-15:00
            return self.flat_price
        else:  # Valley: 23:00-7:00
            return self.valley_price
    
    def _get_other_price(self, hour: int) -> float:
        """Get price for other months
        
        Args:
            hour: Hour (0-23)
            
        Returns:
            Corresponding price for the time period
        """
        if 17 <= hour < 23:  # High: 17:00-23:00
            return self.peak_price
        elif 6 <= hour < 12 or 15 <= hour < 17 or hour == 23 or hour == 0:  # Flat: 6:00-12:00, 15:00-17:00, 23:00-0:00
            return self.flat_price
        else:  # Valley: 0:00-6:00, 12:00-15:00
            return self.valley_price