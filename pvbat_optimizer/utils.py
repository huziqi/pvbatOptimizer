import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, TYPE_CHECKING
import os
import matplotlib.dates as mdates

if TYPE_CHECKING:
    from .config import OptimizerConfig

class OptimizerUtils:
    @staticmethod
    def calculate_crf(discount_rate: float, years: int) -> float:
        """Calculate Capital Recovery Factor"""
        return (discount_rate * (1 + discount_rate)**years) / ((1 + discount_rate)**years - 1)
        
    @staticmethod
    def calculate_demand_charges(peak_demand: Dict, demand_charge_rate: float) -> Dict:
        """Calculate demand charges for each billing period
        
        Args:
            peak_demand: Dictionary mapping period IDs to peak demand values
            demand_charge_rate: Demand charge rate ($/kW)
            
        Returns:
            Dictionary mapping period IDs to demand charge costs
        """
        demand_charges = {}
        total_demand_charge = 0
        
        for period_id, peak in peak_demand.items():
            charge = peak * demand_charge_rate
            demand_charges[period_id] = charge
            total_demand_charge += charge
            
        return {
            "by_period": demand_charges,
            "total": total_demand_charge
        }

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
        axs[0].set_title('Building Load')
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

        axs[5].plot(results['battery_charge'], label='Battery Charge', color='green')
        axs[5].set_title('Battery Charge')
        axs[5].set_xlabel('Time')
        axs[5].set_ylabel('Power (kW)')
        axs[5].legend()
        axs[5].grid(True)

        axs[6].plot(results['battery_discharge'], label='Battery Discharge', color='brown')
        axs[6].set_title('Battery Discharge')
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
        net_load: pd.Series,
        config: 'OptimizerConfig'
    ) -> Dict:
        """Calculate system performance metrics"""
        total_load = net_load.sum()
        total_grid_import = sum(results['grid_import'])
        total_grid_export = sum(results['grid_export'])
        
        metrics = {
            "self_sufficiency_rate": (total_load - total_grid_import) / total_load,
            "battery_cycles": sum(results['battery_charge']) / results['battery_capacity'],
            "lcoe": results['total_cost'] / (total_load - total_grid_import)       
            }
        
        return metrics

    @staticmethod
    def plot_seasonal_comparison(
        results: Dict,
        load_profile: pd.Series,
        save_dir: str = 'seasonal_comparison',
        plot: bool = False
    ):
        """
        Plot comparison between March and August for each metric in separate figures
        
        Args:
            results: Dictionary containing optimization results
            load_profile: Series containing load data
            pv_profile: Series containing PV generation data
            save_dir: Directory to save the plots (default: 'seasonal_comparison')
            plot: Whether to display the plots
        """
        # Create folder if it doesn't exist
        if save_dir:
            # Handle the case where save_dir is actually a file with extension
            if '.' in os.path.basename(save_dir):
                # Extract directory part
                save_dir = os.path.dirname(save_dir)
                # If empty, use current directory
                if not save_dir:
                    save_dir = 'seasonal_comparison'
            
            # Create directory if it doesn't exist
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
        
        # Filter data for March and August
        march_filter = load_profile.index.month == 3
        august_filter = load_profile.index.month == 8
        
        # Check if there is data for both months
        if not any(march_filter) or not any(august_filter):
            print("Warning: No data available for either March or August. Cannot create seasonal comparison.")
            return
        
        # List of metrics to plot with their properties
        metrics = [
            {
                'title': 'Building Load',
                'data': load_profile,
                'label': 'Load',
                'color': 'red',
                'ylabel': 'Power (kW)',
                'filename': 'load_comparison.png'
            },
            {
                'title': 'Battery State',
                'data': results['battery_energy'],
                'label': 'Battery Energy',
                'color': 'orange',
                'ylabel': 'Energy (kWh)',
                'filename': 'battery_state_comparison.png'
            },
            {
                'title': 'Grid Import',
                'data': results['grid_import'],
                'label': 'Grid Import',
                'color': 'blue',
                'ylabel': 'Power (kW)',
                'filename': 'grid_import_comparison.png'
            },
            {
                'title': 'Grid Export',
                'data': results['grid_export'],
                'label': 'Grid Export',
                'color': 'purple',
                'ylabel': 'Power (kW)',
                'filename': 'grid_export_comparison.png'
            },
            {
                'title': 'Battery Charge',
                'data': results['battery_charge'],
                'label': 'Battery Charge',
                'color': 'green',
                'ylabel': 'Power (kW)',
                'filename': 'battery_charge_comparison.png'
            },
            {
                'title': 'Battery Discharge',
                'data': results['battery_discharge'],
                'label': 'Battery Discharge',
                'color': 'brown',
                'ylabel': 'Power (kW)',
                'filename': 'battery_discharge_comparison.png'
            }
        ]
        
        # Create and save each plot
        for metric in metrics:
            try:
                # Create figure with 2 rows and 1 column
                fig, axs = plt.subplots(2, 1, figsize=(12, 10))
                
                # Plot for March
                march_data = metric['data'][march_filter]
                if not march_data.empty:
                    axs[0].plot(march_data.index, march_data, label=metric['label'], color=metric['color'])
                    axs[0].set_title(f"March - {metric['title']}")
                    axs[0].set_xlabel('Time')
                    axs[0].set_ylabel(metric['ylabel'])
                    axs[0].legend()
                    axs[0].grid(True)
                    
                    # Format x-axis for better readability - 每隔2天显示一个日期
                    axs[0].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                    axs[0].xaxis.set_major_locator(mdates.DayLocator(interval=2))
                else:
                    axs[0].text(0.5, 0.5, 'No data available for March', 
                              horizontalalignment='center', verticalalignment='center',
                              transform=axs[0].transAxes)
                
                # Plot for August
                august_data = metric['data'][august_filter]
                if not august_data.empty:
                    axs[1].plot(august_data.index, august_data, label=metric['label'], color=metric['color'])
                    axs[1].set_title(f"August - {metric['title']}")
                    axs[1].set_xlabel('Time')
                    axs[1].set_ylabel(metric['ylabel'])
                    axs[1].legend()
                    axs[1].grid(True)
                    
                    # Format x-axis for better readability - 每隔2天显示一个日期
                    axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                    axs[1].xaxis.set_major_locator(mdates.DayLocator(interval=2))
                else:
                    axs[1].text(0.5, 0.5, 'No data available for August', 
                              horizontalalignment='center', verticalalignment='center',
                              transform=axs[1].transAxes)
                
                # Add main title
                fig.suptitle(f"{metric['title']}: March vs August Comparison", fontsize=16)
                
                plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to make room for suptitle
                
                # Save figure if directory is provided
                if save_dir:
                    save_path = os.path.join(save_dir, metric['filename'])
                    plt.savefig(save_path, dpi=300, bbox_inches='tight')
                    print(f"Saved {metric['title']} comparison to {save_path}")
                
                # Show plot if requested
                if plot:
                    plt.show()
                else:
                    plt.close(fig)
                
            except Exception as e:
                print(f"Error creating {metric['title']} comparison plot: {e}")

    @staticmethod
    def net_profiles(load_profile_path: str, pv_profile_path: str = None) -> pd.Series:
        """Load load profile and PV profile from CSV files and calculate net load
        
        Args:
            load_profile_path: Path to the load profile CSV file
            pv_profile_path: Path to the PV profile CSV file, if None, assumes no PV generation
            
        Returns:
            pd.Series: Net load profile (load - pv) with datetime index
        """
        # Read load profile CSV file
        try:
            load_profile = pd.read_csv(load_profile_path, index_col=0, parse_dates=True)
            if not isinstance(load_profile.index, pd.DatetimeIndex):
                raise ValueError("Load profile must have datetime index")
        except Exception as e:
            raise ValueError(f"Error reading load profile: {str(e)}")
            
        # Handle PV profile
        if pv_profile_path is None:
            pv_profile = pd.Series(0, index=load_profile.index)
        else:
            try:
                pv_profile = pd.read_csv(pv_profile_path, index_col=0, parse_dates=True)
                if not isinstance(pv_profile.index, pd.DatetimeIndex):
                    raise ValueError("PV profile must have datetime index")
            except Exception as e:
                raise ValueError(f"Error reading PV profile: {str(e)}")
        
        # Convert to Series if DataFrame
        if isinstance(load_profile, pd.DataFrame):
            if load_profile.shape[1] > 1:
                print("Warning: Multiple columns in load profile, using first column")
            load_profile = load_profile.iloc[:, 0]
        if isinstance(pv_profile, pd.DataFrame):
            if pv_profile.shape[1] > 1:
                print("Warning: Multiple columns in PV profile, using first column")
            pv_profile = pv_profile.iloc[:, 0]
        
        # Validate input data
        OptimizerUtils.validate_input_data(load_profile, pv_profile)
        
        # Calculate net load (positive means import from grid, negative means export to grid)
        return load_profile - pv_profile