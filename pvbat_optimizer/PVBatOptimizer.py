from abc import ABC, abstractmethod
from typing import Dict, Tuple, List
import pandas as pd

class PVBatOptimizer(ABC):
    """Abstract base class for PV-Battery optimization.
    
    This class defines the interface that all PV-Battery optimizers must implement.
    Different optimization methods (e.g., using different solvers or algorithms) can
    inherit from this class and implement their own optimization logic.
    """
    def __init__(self, config):
        self.config = config

    def _get_billing_periods(self, time_index: pd.DatetimeIndex) -> Dict[str, List[int]]:
        """Divide time steps into billing periods for demand charge calculation.
        
        Args:
            time_index: DatetimeIndex of the time series data
            
        Returns:
            Dictionary mapping period IDs to lists of time indices
        """
        pass
    
    @abstractmethod
    def optimize(
        self,
        net_load: pd.Series
    ) -> Dict:
        """
        Performs optimization to determine optimal battery capacity and operation strategy.
        
        Parameters
        ----------
        net_load : pd.Series
            The net load profile (load minus PV generation) time series data with shape of (n,2) and n is the number of time steps.
            The first column is the time index and the second column is the net load profile with time resolution of 1 hour.
            A pandas Series with DatetimeIndex is used for time series data.
        
        Returns
        -------
        results : Dict
            A dictionary containing optimization results including:
            - battery_capacity: Optimal battery capacity in kWh
            - operation_strategy: Optimal battery operation strategy time series

        Instructions
        ------------
        Implement the optimization logic to minimize electricity costs by:
        1. Determining optimal battery capacity
        2. Determining optimal battery operation strategy
        
        The specific optimization method depends on the implementing class.
        """
        pass
    
    def _create_model(self, load_profile: pd.Series, pv_profile: pd.Series,
                     battery_capacity_range: Tuple[float, float]):
        """Create the optimization model.
        
        Args:
            load_profile: Load profile time series
            pv_profile: PV generation profile time series
            battery_capacity_range: Tuple of (min, max) battery capacity
        """
        pass
    
    def _extract_results(self, model, time_index: pd.DatetimeIndex) -> Dict:
        """Extract results from the optimized model.
        
        Args:
            model: The optimized model
            time_index: Time index for the results series
            
        Returns:
            Dictionary containing extracted results
        """
        pass