// PV Battery Optimizer Frontend JavaScript

class PVBatteryOptimizer {
    constructor() {
        this.uploadedFileName = null;
        this.dataInfo = null;
        this.optimizationParameters = null;
        this.monthlyData = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // File upload form
        document.getElementById('uploadForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFileUpload();
        });

        // Optimization form
        document.getElementById('optimizeForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleOptimization();
        });

        // File input change
        document.getElementById('csvFile').addEventListener('change', (e) => {
            this.resetResults();
        });

        // Update plots button
        document.getElementById('updatePlotsBtn').addEventListener('click', (e) => {
            this.updateMonthlyPlots();
        });
    }

    async handleFileUpload() {
        const fileInput = document.getElementById('csvFile');
        const file = fileInput.files[0];

        if (!file) {
            this.showError('Please select a CSV file');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            this.showLoading('Uploading and validating file...');
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.uploadedFileName = result.data_info.filename;
                this.dataInfo = result.data_info;
                this.displayFileInfo(result.data_info);
                this.showParametersSection();
                this.hideLoading();
            } else {
                this.showError(result.error || 'Upload failed');
                this.hideLoading();
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
            this.hideLoading();
        }
    }

    displayFileInfo(info) {
        const fileDetails = document.getElementById('fileDetails');
        fileDetails.innerHTML = `
            <p><strong>File:</strong> ${info.filename}</p>
            <p><strong>Rows:</strong> ${info.rows.toLocaleString()}</p>
            <p><strong>Columns:</strong> ${info.columns.join(', ')}</p>
            <p><strong>Date Range:</strong> ${info.start_date} to ${info.end_date}</p>
        `;
        
        // Populate column selector
        const columnSelect = document.getElementById('columnSelect');
        columnSelect.innerHTML = '<option value="">Select column...</option>';
        info.columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col;
            option.textContent = col;
            columnSelect.appendChild(option);
        });

        document.getElementById('fileInfo').style.display = 'block';
    }

    showParametersSection() {
        document.getElementById('parametersCard').style.display = 'block';
        document.getElementById('parametersCard').classList.add('fade-in');
    }

    async handleOptimization() {
        if (!this.uploadedFileName) {
            this.showError('Please upload a file first');
            return;
        }

        const columnName = document.getElementById('columnSelect').value;
        if (!columnName) {
            this.showError('Please select a net load column');
            return;
        }

        const parameters = this.collectParameters();
        this.optimizationParameters = parameters; // Store for later use
        const requestData = {
            filename: this.uploadedFileName,
            column_name: columnName,
            parameters: parameters
        };

        try {
            this.showLoading('Running optimization...');
            this.hideError();
            
            const response = await fetch('/api/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.displayResults(result.results);
                this.hideLoading();
            } else {
                this.showError(result.error || 'Optimization failed');
                this.hideLoading();
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
            this.hideLoading();
        }
    }

    collectParameters() {
        return {
            battery_cost_per_kwh: parseFloat(document.getElementById('batteryCost').value) || 1300,
            electricity_sell_price_ratio: parseFloat(document.getElementById('sellRatio').value) || 0.6,
            battery_charge_efficiency: parseFloat(document.getElementById('chargeEff').value) || 0.913,
            battery_discharge_efficiency: parseFloat(document.getElementById('dischargeEff').value) || 0.913,
            charge_power_capacity: parseFloat(document.getElementById('chargePower').value) || 0.5,
            discharge_power_capacity: parseFloat(document.getElementById('dischargePower').value) || 0.5,
            years: parseInt(document.getElementById('projectYears').value) || 15,
            discount_rate: parseFloat(document.getElementById('discountRate').value) || 0.13,
            decision_step: parseFloat(document.getElementById('decisionStep').value) || 0.25,
            demand_charge_rate: parseFloat(document.getElementById('demandCharge').value) || 0,
            max_battery_capacity: parseFloat(document.getElementById('maxCapacity').value) || 1000,
            use_seasonal_prices: document.getElementById('seasonalPrices').checked,
            // ToU Pricing Parameters
            peak_price: parseFloat(document.getElementById('peakPrice').value) || 1.44097,
            high_price: parseFloat(document.getElementById('highPrice').value) || 1.20081,
            flat_price: parseFloat(document.getElementById('flatPrice').value) || 0.76785,
            valley_price: parseFloat(document.getElementById('valleyPrice').value) || 0.33489
        };
    }

    displayResults(results) {
        // Store monthly data and parameters for later use
        this.monthlyData = results.monthly_data;

        // Update main metrics
        document.getElementById('batteryCapacity').textContent = results.battery_capacity.toFixed(2);
        document.getElementById('totalCost').textContent = results.total_cost.toFixed(2);
        document.getElementById('annualSavings').textContent = results.annual_savings.toFixed(2);

        // Update economic metrics
        document.getElementById('paybackPeriod').textContent = results.economic_metrics.payback_period.toFixed(2);
        document.getElementById('npv').textContent = results.economic_metrics.npv.toFixed(2);
        document.getElementById('irr').textContent = results.economic_metrics.irr.toFixed(2);
        document.getElementById('costSavingRatio').textContent = (results.economic_metrics.operational_cost_saving_ratio * 100).toFixed(2);
        document.getElementById('sellProfit').textContent = results.economic_metrics.sell_energy_profit.toFixed(2);
        document.getElementById('demandCost').textContent = results.demand_cost.toFixed(2);
        document.getElementById('energyCost').textContent = results.energy_cost.toFixed(2);

        // Update performance metrics
        document.getElementById('optimizationDuration').textContent = results.optimization_duration.toFixed(2);

        // Setup month selector
        this.setupMonthSelector();

        // Display plots
        this.displayPlots(results.plots);

        // Show results section
        document.getElementById('resultsSection').style.display = 'block';
        document.getElementById('resultsSection').classList.add('fade-in');
        
        // Scroll to results
        document.getElementById('resultsSection').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }

    displayPlots(plots) {
        // Daily profile plot (only shows on initial optimization)
        if (plots.daily_profile) {
            const dailyProfileImg = document.getElementById('dailyProfilePlot');
            dailyProfileImg.src = `data:image/png;base64,${plots.daily_profile}`;
            dailyProfileImg.style.display = 'block';
            dailyProfileImg.alt = 'Daily load profile analysis';
        }

        // Time series plots (can be updated by month selection)
        const plotElements = {
            'grid_import': 'gridImportPlot',
            'battery_energy': 'batteryEnergyPlot',
            'charging_power': 'chargingPowerPlot',
            'discharging_power': 'dischargingPowerPlot'
        };

        Object.keys(plotElements).forEach(plotKey => {
            const elementId = plotElements[plotKey];
            const imgElement = document.getElementById(elementId);
            
            if (plots[plotKey]) {
                imgElement.src = `data:image/png;base64,${plots[plotKey]}`;
                imgElement.style.display = 'block';
                imgElement.alt = `${plotKey.replace('_', ' ')} plot`;
            } else {
                imgElement.style.display = 'none';
            }
        });
    }

    setupMonthSelector() {
        if (!this.monthlyData) return;

        const monthSelect = document.getElementById('monthSelect');
        const monthSelector = document.getElementById('monthSelector');

        // Clear existing options (except "All Data")
        monthSelect.innerHTML = '<option value="">All Data</option>';

        // Add month options
        Object.keys(this.monthlyData).forEach(monthKey => {
            const monthInfo = this.monthlyData[monthKey];
            const option = document.createElement('option');
            option.value = monthKey;
            option.textContent = monthInfo.month_name;
            monthSelect.appendChild(option);
        });

        // Show month selector
        monthSelector.style.display = 'block';
    }

    async updateMonthlyPlots() {
        const selectedMonth = document.getElementById('monthSelect').value;
        
        if (!this.uploadedFileName || !this.optimizationParameters) {
            this.showError('Please run optimization first');
            return;
        }

        try {
            this.showPlotsLoading();

            const requestData = {
                filename: this.uploadedFileName,
                column_name: document.getElementById('columnSelect').value,
                parameters: this.optimizationParameters,
                selected_month: selectedMonth || null
            };

            console.log('Sending request to update monthly plots:', requestData);

            const response = await fetch('/api/generate_monthly_plots', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            console.log('Response status:', response.status);
            const result = await response.json();
            console.log('Response data:', result);

            if (response.ok && result.success) {
                this.displayPlots(result.plots);
                this.hidePlotsLoading();
                console.log('Plots updated successfully');
            } else {
                this.showError(result.error || 'Failed to update plots');
                this.hidePlotsLoading();
            }
        } catch (error) {
            console.error('Error updating plots:', error);
            this.showError('Network error: ' + error.message);
            this.hidePlotsLoading();
        }
    }

    showPlotsLoading() {
        document.getElementById('plotsLoadingIndicator').style.display = 'block';
        document.getElementById('plotsContainer').style.opacity = '0.5';
    }

    hidePlotsLoading() {
        document.getElementById('plotsLoadingIndicator').style.display = 'none';
        document.getElementById('plotsContainer').style.opacity = '1';
    }

    showLoading(message = 'Loading...') {
        const loadingElement = document.getElementById('loadingIndicator');
        if (message !== 'Loading...') {
            loadingElement.querySelector('h4').textContent = message;
        }
        loadingElement.style.display = 'block';
        this.hideError();
        this.hideResults();
    }

    hideLoading() {
        document.getElementById('loadingIndicator').style.display = 'none';
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').style.display = 'block';
        this.hideLoading();
    }

    hideError() {
        document.getElementById('errorSection').style.display = 'none';
    }

    hideResults() {
        document.getElementById('resultsSection').style.display = 'none';
    }

    resetResults() {
        this.hideError();
        this.hideResults();
        this.hideLoading();
        document.getElementById('fileInfo').style.display = 'none';
        document.getElementById('parametersCard').style.display = 'none';
        document.getElementById('monthSelector').style.display = 'none';
        this.uploadedFileName = null;
        this.dataInfo = null;
        this.optimizationParameters = null;
        this.monthlyData = null;
    }
}

// Utility functions
function formatNumber(num, decimals = 2) {
    return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatCurrency(amount, currency = '') {
    const formatted = formatNumber(amount, 2);
    return currency ? `${formatted} ${currency}` : formatted;
}

function formatPercentage(value) {
    return `${(value * 100).toFixed(2)}%`;
}

// Enhanced error handling
window.addEventListener('error', (event) => {
    console.error('JavaScript error:', event.error);
    const optimizer = window.pvOptimizer;
    if (optimizer) {
        optimizer.showError('An unexpected error occurred. Please refresh the page and try again.');
    }
});

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.pvOptimizer = new PVBatteryOptimizer();
    console.log('PV Battery Optimizer initialized');
});

// Add loading states to buttons
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                
                // Re-enable button after a timeout (safety measure)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 30000); // 30 seconds timeout
            }
        });
    });
});

// Add tooltips for better user experience
document.addEventListener('DOMContentLoaded', () => {
    // Add tooltips to form fields
    const tooltips = {
        'batteryCost': 'Cost per kWh of battery capacity',
        'sellRatio': 'Ratio of selling price to buying price',
        'chargeEff': 'Efficiency when charging the battery',
        'dischargeEff': 'Efficiency when discharging the battery',
        'chargePower': 'Maximum charging power as ratio of capacity',
        'dischargePower': 'Maximum discharging power as ratio of capacity',
        'projectYears': 'Project lifetime in years',
        'discountRate': 'Discount rate for economic analysis',
        'decisionStep': 'Time step for optimization (hours)',
        'demandCharge': 'Demand charge rate',
        'maxCapacity': 'Maximum allowed battery capacity',
        'seasonalPrices': 'Use seasonal electricity pricing',
        'peakPrice': 'Peak time electricity price (highest rate)',
        'highPrice': 'High time electricity price (medium-high rate)',
        'flatPrice': 'Flat time electricity price (medium rate)',
        'valleyPrice': 'Valley time electricity price (lowest rate)'
    };

    Object.keys(tooltips).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.title = tooltips[id];
            element.setAttribute('data-bs-toggle', 'tooltip');
            element.setAttribute('data-bs-placement', 'top');
        }
    });

    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Add smooth scrolling to internal links
document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(link.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+Enter or Cmd+Enter to submit current form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const activeForm = document.activeElement.closest('form');
        if (activeForm) {
            activeForm.dispatchEvent(new Event('submit'));
        }
    }
});

// Add drag and drop functionality for file upload
document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('csvFile');
    const uploadForm = document.getElementById('uploadForm');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadForm.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadForm.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadForm.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        uploadForm.classList.add('drag-over');
    }

    function unhighlight(e) {
        uploadForm.classList.remove('drag-over');
    }

    uploadForm.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        }
    }
});

// Add progress indication for long operations
class ProgressTracker {
    constructor() {
        this.progressBar = null;
        this.progressContainer = null;
        this.createProgressBar();
    }

    createProgressBar() {
        this.progressContainer = document.createElement('div');
        this.progressContainer.className = 'progress-container';
        this.progressContainer.style.display = 'none';
        
        this.progressBar = document.createElement('div');
        this.progressBar.className = 'progress-bar';
        this.progressBar.style.width = '0%';
        
        const progressWrapper = document.createElement('div');
        progressWrapper.className = 'progress';
        progressWrapper.appendChild(this.progressBar);
        
        this.progressContainer.appendChild(progressWrapper);
        document.body.appendChild(this.progressContainer);
    }

    show(message = 'Processing...') {
        this.progressContainer.style.display = 'block';
        this.progressBar.style.width = '0%';
    }

    update(percentage) {
        this.progressBar.style.width = `${percentage}%`;
    }

    hide() {
        this.progressContainer.style.display = 'none';
    }
}

// Export for use in other modules
window.PVBatteryOptimizer = PVBatteryOptimizer; 