import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import OptimizerConfig

class OptimizerUtils:
    @staticmethod
    def calculate_crf(discount_rate: float, years: int) -> float:
        """Calculate Capital Recovery Factor"""
        return (discount_rate * (1 + discount_rate)**years) / ((1 + discount_rate)**years - 1)

    @staticmethod
    def validate_input_data(
        load_profile: pd.Series,
        pv_profile: pd.Series
    ) -> bool:
        """Validate the input data"""
        # Check if the lengths of the data are the same
        if len(load_profile) != len(pv_profile):
            raise ValueError("Load profile and PV generation profile lengths do not match")
        
        # Check for missing values
        if load_profile.isnull().any() or pv_profile.isnull().any():
            raise ValueError("Input data contains missing values")
        
        # Check if data contains negative values
        if (load_profile < 0).any() or (pv_profile < 0).any():
            raise ValueError("Input data contains negative values")
        
        return True

    @staticmethod
    def plot_optimization_results(
        results: Dict,
        load_profile: pd.Series,
        pv_profile: pd.Series,
        save_path: str = None,
        plot: bool = False
    ):
        """Plot optimization results"""
        fig, axs = plt.subplots(7, 1, figsize=(12, 12))
        
        # Power balance plot
        axs[0].plot(load_profile.index, load_profile, label='Load', color='red')
        axs[0].set_title('Power Balance')
        axs[0].set_xlabel('Time')
        axs[0].set_ylabel('Power (kW)')
        axs[0].legend()
        axs[0].grid(True)

        # PV generation plot
        axs[1].plot(pv_profile.index, pv_profile, label='PV Generation', color='green')
        axs[1].set_title('PV Generation')
        axs[1].set_xlabel('Time')
        axs[1].set_ylabel('Power (kW)')
        axs[1].legend()
        axs[1].grid(True)

        # Battery state plot
        axs[2].plot(results['battery_energy'], label='Battery Energy', color='orange')
        axs[2].set_title('Battery State')
        axs[2].set_xlabel('Time')
        axs[2].set_ylabel('Energy (kWh)')
        axs[2].legend()
        axs[2].grid(True)

        # Other possible subplots
        axs[3].plot(results['grid_import'], label='Grid Import', color='blue')
        axs[3].set_title('Grid Import')
        axs[3].set_xlabel('Time')
        axs[3].set_ylabel('Power (kW)')
        axs[3].legend()
        axs[3].grid(True)

        axs[4].plot(results['grid_export'], label='Grid Export', color='purple')
        axs[4].set_title('Grid Export')
        axs[4].set_xlabel('Time')
        axs[4].set_ylabel('Power (kW)')
        axs[4].legend()
        axs[4].grid(True)

        axs[5].plot(results['battery_charge'], label='Battery Charge', color='yellow')
        axs[5].set_title('Battery Charge/Discharge')
        axs[5].set_xlabel('Time')
        axs[5].set_ylabel('Power (kW)')
        axs[5].legend()
        axs[5].grid(True)

        axs[6].plot(results['battery_discharge'], label='Battery Discharge', color='brown')
        axs[6].set_title('Battery Charge/Discharge')
        axs[6].set_xlabel('Time')
        axs[6].set_ylabel('Power (kW)')
        axs[6].legend()
        axs[6].grid(True)

        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        if plot:
            plt.show()

    @staticmethod
    def plot_sensitivity_results(results_df: pd.DataFrame):
        
        """Plot sensitivity analysis results for different battery costs"""
        fig, axs = plt.subplots(len(sorted(results_df['battery_cost'].unique())), 1, figsize=(10, 6 * len(sorted(results_df['battery_cost'].unique()))))
        
        # Plot lines for each battery cost
        for i, battery_cost in enumerate(sorted(results_df['battery_cost'].unique())):
            df_cost = results_df[results_df['battery_cost'] == battery_cost]
            axs[i].plot(df_cost['pv_capacity'], df_cost['battery_capacity'], 
                        marker='o', linewidth=2, markersize=6, 
                        label=f'Battery Cost: {battery_cost} CNY/kWh')
            axs[i].set_title(f'Battery Cost: {battery_cost} CNY/kWh')
            axs[i].set_xlabel('PV Capacity (kW)')
            axs[i].set_ylabel('Optimal Battery Capacity (kWh)')
            axs[i].grid(True, linestyle='--', alpha=0.7)
            axs[i].legend()
            
            # Set actual data points as y-axis ticks
            y_values = sorted(df_cost['battery_capacity'].unique())
            axs[i].set_yticks(y_values)
            
            # Set x-axis ticks
            axs[i].set_xticks(sorted(df_cost['pv_capacity'].unique()))
        
        plt.tight_layout()
        plt.savefig('pv_battery_capacity_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def calculate_system_metrics(
        results: Dict,
        load_profile: pd.Series,
        pv_profile: pd.Series,
        config: 'OptimizerConfig'
    ) -> Dict:
        """Calculate system performance metrics"""
        total_load = load_profile.sum()
        total_pv_generation = pv_profile.sum()
        total_grid_import = sum(results['grid_import'])
        total_grid_export = sum(results['grid_export'])
        
        metrics = {
            "self_consumption_rate": (total_pv_generation - total_grid_export) / total_pv_generation,
            "self_sufficiency_rate": (total_load - total_grid_import) / total_load,
            "battery_cycles": sum(results['battery_charge']) / results['battery_capacity'],
            "lcoe": results['total_cost'] / (total_load - total_grid_import),
            "pv_utilization_rate": (total_pv_generation - total_grid_export) / total_pv_generation
        }
        
        return metrics