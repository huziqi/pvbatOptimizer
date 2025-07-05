#!/usr/bin/env python3
"""
PV Battery Optimizer Web Application Startup Script
This script sets up the environment and runs the Flask web application.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_virtual_environment():
    """Check if we're in the correct virtual environment"""
    venv_name = "ecogrid"
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # We're in a virtual environment
        current_venv = os.path.basename(sys.prefix)
        if current_venv != venv_name:
            print(f"Warning: You're in virtual environment '{current_venv}', but '{venv_name}' is recommended.")
        return True
    else:
        print(f"Warning: You're not in a virtual environment. Please activate '{venv_name}' environment:")
        print(f"conda activate {venv_name}")
        return False

def install_dependencies():
    """Install required dependencies"""
    requirements_file = Path("requirements_web.txt")
    
    if not requirements_file.exists():
        print("Error: requirements_web.txt not found!")
        return False
    
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                      check=True, capture_output=True, text=True)
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["uploads", "static/css", "static/js", "templates"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def check_gurobi_license():
    """Check if Gurobi license is available"""
    try:
        import gurobipy as gp
        # Try to create a model to test license
        model = gp.Model("test")
        print("Gurobi license is available.")
        return True
    except Exception as e:
        print(f"Warning: Gurobi license check failed: {e}")
        print("The application may not work properly without a valid Gurobi license.")
        return False

def main():
    """Main function to start the web application"""
    print("=" * 60)
    print("PV Battery Optimizer Web Application")
    print("=" * 60)
    
    # Check virtual environment
    if not check_virtual_environment():
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies. Exiting.")
        sys.exit(1)
    
    # Check Gurobi license
    check_gurobi_license()
    
    # Set environment variables
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    # Start the application
    print("\nStarting the web application...")
    print("The application will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the server.")
    print("-" * 60)
    
    try:
        # Import and run the Flask app
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"Error importing app: {e}")
        print("Make sure app.py is in the current directory.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down the web application...")
    except Exception as e:
        print(f"Error running the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 