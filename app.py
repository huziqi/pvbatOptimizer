from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import tempfile
import json
import time
from datetime import datetime
import traceback
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from pvbat_optimizer import PVBatOptimizer_linearProg, OptimizerConfig, OptimizerUtils

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle CSV file upload and validation"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        
        # Clean up old temporary files
        import glob
        old_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], 'temp_*'))
        for old_file in old_files:
            try:
                os.remove(old_file)
            except:
                pass

        # Save file temporarily
        filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Validate CSV structure
        try:
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            if len(df) == 0:
                return jsonify({'error': 'CSV file is empty'}), 400
            
            # Check if it's a valid time series
            if not isinstance(df.index, pd.DatetimeIndex):
                return jsonify({'error': 'First column must be datetime index'}), 400
            
            # Get basic info about the data
            data_info = {
                'filename': filename,
                'rows': len(df),
                'columns': list(df.columns),
                'start_date': df.index.min().strftime('%Y-%m-%d %H:%M:%S'),
                'end_date': df.index.max().strftime('%Y-%m-%d %H:%M:%S'),
                'sample_data': df.head(10).to_dict('records')
            }
            
            return jsonify({'success': True, 'data_info': data_info}), 200
            
        except Exception as e:
            os.remove(filepath)  # Clean up file
            return jsonify({'error': f'Invalid CSV format: {str(e)}'}), 400
    
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/optimize', methods=['POST'])
def optimize_battery():
    """Run battery optimization with user parameters"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['filename', 'column_name', 'parameters']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Load the CSV file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        
        # Get the net load column
        column_name = data['column_name']
        if column_name not in df.columns:
            return jsonify({'error': f'Column {column_name} not found in CSV'}), 400
        
        net_load = df[column_name]
        
        # Create optimizer configuration
        params = data['parameters']
        config = OptimizerConfig(
            battery_cost_per_kwh=params.get('battery_cost_per_kwh', 1300),
            electricity_sell_price_ratio=params.get('electricity_sell_price_ratio', 0.6),
            battery_charge_efficiency=params.get('battery_charge_efficiency', 0.913),
            battery_discharge_efficiency=params.get('battery_discharge_efficiency', 0.913),
            charge_power_capacity=params.get('charge_power_capacity', 0.5),
            discharge_power_capacity=params.get('discharge_power_capacity', 0.5),
            use_seasonal_prices=params.get('use_seasonal_prices', True),
            years=params.get('years', 15),
            discount_rate=params.get('discount_rate', 0.13),
            decision_step=params.get('decision_step', 0.25),
            demand_charge_rate=params.get('demand_charge_rate', 0),
            max_battery_capacity=params.get('max_battery_capacity', 1000),
            # ToU Pricing Parameters
            peak_price=params.get('peak_price', 1.44097),
            high_price=params.get('high_price', 1.20081),
            flat_price=params.get('flat_price', 0.76785),
            valley_price=params.get('valley_price', 0.33489)
        )
        
        # Create optimizer and run optimization
        optimizer = PVBatOptimizer_linearProg(config)
        
        # Record optimization start time
        optimization_start_time = time.time()
        result = optimizer.optimize(net_load)
        optimization_end_time = time.time()
        
        # Calculate optimization duration
        optimization_duration = optimization_end_time - optimization_start_time
        
        # Calculate KPIs
        kpis = OptimizerUtils.calculate_system_metrics(result, net_load)
        
        # Calculate economic metrics
        economic_metrics = OptimizerUtils.calculate_economic_metrics(
            total_cost=result['total_cost'],
            annual_savings=result['annual_savings'],
            project_lifetime=config.years,
            discount_rate=0.01,
            battery_construction_cost=result['battery_construction_cost']
        )
        
        # Generate plots
        plots = generate_plots(result, net_load, config)
        
        # Generate monthly data for month selector
        monthly_data = get_monthly_data(result, net_load)
        
        # Prepare response data
        response_data = {
            'success': True,
            'results': {
                'battery_capacity': float(result['battery_capacity']),
                'total_cost': float(result['total_cost']),
                'battery_construction_cost': float(result['battery_construction_cost']),
                'annual_savings': float(result['annual_savings']),
                'operational_cost_saving_ratio': float(result['operational_cost_saving_ratio']),
                'sell_energy_profit': float(result['sell_energy_profit']),
                'sell_energy_profit_ratio': float(result['sell_energy_profit_ratio']),
                'optimization_duration': float(optimization_duration),
                'demand_cost': float(result['demand_charges']['total']),
                'energy_cost': float(result['new_energy_cost_without_demand_charge']),
                'kpis': {k: float(v) if isinstance(v, (int, float, np.number)) else v for k, v in kpis.items()},
                'economic_metrics': {
                    'payback_period': float(economic_metrics['payback_period']),
                    'npv': float(economic_metrics['npv']),
                    'irr': float(economic_metrics['irr']),
                    'operational_cost_saving_ratio': float(result['operational_cost_saving_ratio']),
                    'sell_energy_profit': float(result['sell_energy_profit'])
                },
                'plots': plots,
                'monthly_data': monthly_data
            }
        }
        
        # Keep the file for potential month-specific plot generation
        # The file will be cleaned up when a new file is uploaded
        
        return jsonify(response_data), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Optimization failed: {str(e)}'}), 500

def get_monthly_data(result, net_load):
    """Get available months from the data"""
    monthly_data = {}
    
    # Get unique months
    months = sorted(net_load.index.to_period('M').unique())
    
    for month in months:
        month_str = str(month)
        monthly_data[month_str] = {
            'year': month.year,
            'month': month.month,
            'month_name': month.strftime('%B %Y')
        }
    
    return monthly_data

@app.route('/api/generate_monthly_plots', methods=['POST'])
def generate_monthly_plots():
    """Generate plots for a specific month"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        column_name = data.get('column_name')
        parameters = data.get('parameters')
        selected_month = data.get('selected_month')  # Format: 'YYYY-MM'
        
        if not all([filename, column_name, parameters]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Load the CSV file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        net_load = df[column_name]
        
        # Create optimizer configuration
        config = OptimizerConfig(
            battery_cost_per_kwh=parameters.get('battery_cost_per_kwh', 1300),
            electricity_sell_price_ratio=parameters.get('electricity_sell_price_ratio', 0.6),
            battery_charge_efficiency=parameters.get('battery_charge_efficiency', 0.913),
            battery_discharge_efficiency=parameters.get('battery_discharge_efficiency', 0.913),
            charge_power_capacity=parameters.get('charge_power_capacity', 0.5),
            discharge_power_capacity=parameters.get('discharge_power_capacity', 0.5),
            use_seasonal_prices=parameters.get('use_seasonal_prices', True),
            years=parameters.get('years', 15),
            discount_rate=parameters.get('discount_rate', 0.13),
            decision_step=parameters.get('decision_step', 0.25),
            demand_charge_rate=parameters.get('demand_charge_rate', 0),
            max_battery_capacity=parameters.get('max_battery_capacity', 1000),
            # ToU Pricing Parameters
            peak_price=parameters.get('peak_price', 1.44097),
            high_price=parameters.get('high_price', 1.20081),
            flat_price=parameters.get('flat_price', 0.76785),
            valley_price=parameters.get('valley_price', 0.33489)
        )
        
        # Create optimizer and run optimization
        optimizer = PVBatOptimizer_linearProg(config)
        result = optimizer.optimize(net_load)
        
        # Generate plots for specific month
        plots = generate_plots(result, net_load, config, selected_month)
        
        return jsonify({'success': True, 'plots': plots}), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate plots: {str(e)}'}), 500

def generate_plots(result, net_load, config, selected_month=None):
    """Generate optimization result plots"""
    plots = {}
    
    # Set matplotlib parameters for large font size
    plt.rcParams.update({'font.size': 20})
    
    try:
        # Always generate daily profile analysis (not affected by month selection)
        if selected_month is None:  # Only generate for initial optimization
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Create DataFrame with hour information
            df = pd.DataFrame({'net_load': net_load.values}, index=net_load.index)
            df['hour'] = df.index.hour
            df['minute'] = df.index.minute
            df['time_of_day'] = df['hour'] + df['minute'] / 60.0
            
            # Group by time of day and calculate statistics
            hourly_stats = df.groupby('time_of_day')['net_load'].agg([
                'mean', 'std', 'min', 'max', 'count'
            ]).fillna(0)
            
            # Create time array for plotting
            time_hours = hourly_stats.index.values
            mean_load = hourly_stats['mean'].values
            std_load = hourly_stats['std'].values
            min_load = hourly_stats['min'].values
            max_load = hourly_stats['max'].values
            
            # Plot min-max range (lightest shade)
            ax.fill_between(time_hours, min_load, max_load, alpha=0.2, color='blue', label='Min-Max Range')
            
            # Plot ±1 standard deviation range (medium shade)
            ax.fill_between(time_hours, mean_load - std_load, mean_load + std_load, 
                           alpha=0.4, color='blue', label='±1 Standard Deviation')
            
            # Plot mean line
            ax.plot(time_hours, mean_load, color='blue', linewidth=3, label='Average Power')
            
            # Formatting
            ax.set_title('Daily Net Load Power Profile - Annual Average', fontsize=24, pad=20)
            ax.set_xlabel('Time of Day (Hours)', fontsize=20)
            ax.set_ylabel('Power (kW)', fontsize=20)
            ax.legend(fontsize=18)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='both', which='major', labelsize=18)
            
            # Set x-axis to show 24 hours
            ax.set_xlim(0, 24)
            ax.set_xticks(range(0, 25, 4))
            ax.set_xticklabels([f'{h:02d}:00' for h in range(0, 25, 4)])
            
            # Add horizontal line at y=0
            ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            plots['daily_profile'] = base64.b64encode(img_buffer.read()).decode()
            plt.close()

        # Filter data by month if specified
        if selected_month:
            try:
                # Parse selected month (format: 'YYYY-MM')
                year, month = map(int, selected_month.split('-'))
                
                # Filter all data for the selected month
                month_mask = (net_load.index.year == year) & (net_load.index.month == month)
                
                # Filter result data
                battery_energy_filtered = result['battery_energy'][month_mask]
                grid_import_filtered = result['grid_import'][month_mask]
                battery_charge_filtered = result['battery_charge'][month_mask]
                battery_discharge_filtered = result['battery_discharge'][month_mask]
                
                # Update titles with month info
                month_name = pd.Timestamp(year, month, 1).strftime('%B %Y')
                title_suffix = f' - {month_name}'
            except:
                # If month filtering fails, use all data
                battery_energy_filtered = result['battery_energy']
                grid_import_filtered = result['grid_import']
                battery_charge_filtered = result['battery_charge']
                battery_discharge_filtered = result['battery_discharge']
                title_suffix = ''
        else:
            # Use all data
            battery_energy_filtered = result['battery_energy']
            grid_import_filtered = result['grid_import']
            battery_charge_filtered = result['battery_charge']
            battery_discharge_filtered = result['battery_discharge']
            title_suffix = ''
        
        # 1. Grid Import plot
        fig, ax = plt.subplots(figsize=(12, 8))
        grid_import_filtered.plot(ax=ax, linewidth=2, color='red')
        ax.set_title(f'Grid Import{title_suffix}', fontsize=24)
        ax.set_xlabel('Time', fontsize=20)
        ax.set_ylabel('Power (kW)', fontsize=20)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=18)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plots['grid_import'] = base64.b64encode(img_buffer.read()).decode()
        plt.close()
        
        # 2. Battery Energy plot
        fig, ax = plt.subplots(figsize=(12, 8))
        battery_energy_filtered.plot(ax=ax, linewidth=2, color='blue')
        ax.set_title(f'Battery Energy{title_suffix}', fontsize=24)
        ax.set_xlabel('Time', fontsize=20)
        ax.set_ylabel('Battery Energy (kWh)', fontsize=20)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=18)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plots['battery_energy'] = base64.b64encode(img_buffer.read()).decode()
        plt.close()
        
        # 3. Charging Power plot
        fig, ax = plt.subplots(figsize=(12, 8))
        battery_charge_filtered.plot(ax=ax, linewidth=2, color='orange')
        ax.set_title(f'Charging Power{title_suffix}', fontsize=24)
        ax.set_xlabel('Time', fontsize=20)
        ax.set_ylabel('Charging Power (kW)', fontsize=20)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=18)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plots['charging_power'] = base64.b64encode(img_buffer.read()).decode()
        plt.close()
        
        # 4. Discharging Power plot
        fig, ax = plt.subplots(figsize=(12, 8))
        battery_discharge_filtered.plot(ax=ax, linewidth=2, color='purple')
        ax.set_title(f'Discharging Power{title_suffix}', fontsize=24)
        ax.set_xlabel('Time', fontsize=20)
        ax.set_ylabel('Discharging Power (kW)', fontsize=20)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=18)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plots['discharging_power'] = base64.b64encode(img_buffer.read()).decode()
        plt.close()
        
    except Exception as e:
        print(f"Error generating plots: {e}")
    
    return plots

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 