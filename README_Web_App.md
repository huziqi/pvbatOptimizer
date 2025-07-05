# PV Battery Optimizer Web Application

A modern web-based interface for optimizing photovoltaic battery storage systems. This application provides an intuitive way to upload load data, configure optimization parameters, and visualize results.

## Features

- **File Upload**: Upload CSV files with net load data
- **Parameter Configuration**: Interactive forms for setting optimization parameters
- **Real-time Optimization**: Backend processing using linear programming
- **Results Visualization**: Interactive charts and economic metrics
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Method 1: Using the Batch File (Windows)
1. Double-click `start_app.bat`
2. The application will automatically start and open in your browser

### Method 2: Using Python Script
1. Activate your virtual environment:
   ```bash
   conda activate ecogrid
   ```
2. Run the startup script:
   ```bash
   python run_web_app.py
   ```

### Method 3: Direct Flask Run
1. Activate your virtual environment:
   ```bash
   conda activate ecogrid
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements_web.txt
   ```
3. Run the Flask app:
   ```bash
   python app.py
   ```

## Using the Application

### Step 1: Upload Data
1. Click "Select CSV File" or drag and drop your CSV file
2. The file should have:
   - First column: DateTime index
   - One or more columns with net load data
3. Click "Upload & Validate"

### Step 2: Configure Parameters
1. Select the net load column from the dropdown
2. Adjust optimization parameters:
   - **Battery Cost**: Cost per kWh of battery capacity
   - **Sell Price Ratio**: Ratio of electricity selling price to buying price
   - **Efficiency Settings**: Charge/discharge efficiency
   - **Power Capacity**: Maximum charge/discharge power
   - **Economic Parameters**: Project lifetime, discount rate
   - **Constraints**: Maximum battery capacity, demand charges

### Step 3: Run Optimization
1. Click "Run Optimization"
2. Wait for the calculation to complete
3. View results and visualizations

## Results

The application provides:

### Optimization Results
- Optimal battery capacity
- Total system cost
- Annual cost savings

### Economic Metrics
- **Payback Period**: Time to recover initial investment
- **NPV**: Net Present Value of the project
- **IRR**: Internal Rate of Return

### Performance Metrics
- Cost saving ratio
- Energy sell profit
- Operational efficiency

### Visualizations
- Battery energy over time
- Grid import/export patterns
- Battery charge/discharge cycles
- Load comparison (original vs optimized)

## CSV File Format

Your CSV file should be formatted as follows:

```csv
DateTime,Net_Load,Other_Columns
2023-01-01 00:00:00,5.2,
2023-01-01 00:15:00,4.8,
2023-01-01 00:30:00,4.5,
...
```

Requirements:
- First column must be datetime
- DateTime format: YYYY-MM-DD HH:MM:SS
- Net load values in kW
- No missing values in the selected column

## Dependencies

The application requires:
- Python 3.8+
- Flask web framework
- Pandas for data processing
- Matplotlib for visualization
- Gurobi for optimization
- Bootstrap for UI components

## Troubleshooting

### Common Issues

1. **Gurobi License Error**
   - Ensure you have a valid Gurobi license
   - Check license file location
   - Verify license is not expired

2. **CSV Upload Failed**
   - Check file format (CSV with datetime index)
   - Ensure no missing values in data
   - File size should be under 16MB

3. **Optimization Takes Too Long**
   - Reduce data size (use sample data)
   - Increase decision step size
   - Check parameter values

4. **Virtual Environment Issues**
   - Activate the correct environment: `conda activate ecogrid`
   - Install missing packages: `pip install -r requirements_web.txt`

### Error Messages

- **"File not found"**: The uploaded file was not saved properly
- **"Invalid CSV format"**: Check datetime format and column structure
- **"Optimization failed"**: Check parameter values and data quality
- **"No file selected"**: Upload a CSV file before optimization

## Technical Details

### Architecture
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python Flask with REST API
- **Optimization**: Gurobi linear programming solver
- **Visualization**: Matplotlib with base64 encoding

### API Endpoints
- `POST /api/upload`: File upload and validation
- `POST /api/optimize`: Run optimization
- `GET /api/health`: Health check

### Security
- File size limits (16MB)
- File type validation (CSV only)
- Temporary file cleanup
- Input parameter validation

## Development

### Project Structure
```
├── app.py                 # Flask application
├── run_web_app.py         # Startup script
├── requirements_web.txt   # Dependencies
├── templates/
│   └── index.html        # Main template
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── main.js       # Frontend logic
├── uploads/              # Temporary file storage
└── pvbat_optimizer/      # Optimization modules
```

### Adding Features
1. Backend: Add new endpoints in `app.py`
2. Frontend: Update templates and JavaScript
3. Styling: Modify CSS files
4. Dependencies: Update requirements files

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review error messages in the browser console
3. Check the terminal/command prompt for backend errors
4. Ensure all dependencies are properly installed

## Version History

- v1.0.0: Initial release with basic optimization features
- Frontend web interface
- CSV file upload
- Parameter configuration
- Results visualization
- Economic analysis 