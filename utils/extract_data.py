#!/home/user/anaconda3/bin/python
# -*- coding: utf-8 -*-

"""
Extract 2024 electricity load data and merge it by hour
Aggregate 15-minute data into hourly data
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import glob

def show_excel_structure(xlsx_file):
    """
    Display the structure of the Excel file
    
    Args:
        xlsx_file: Path to the Excel file
    """
    try:
        # Read the Excel file
        df = pd.read_excel(xlsx_file)
        
        # Display column information
        print(f"\nExcel file structure ({xlsx_file}):")
        print(f"Column names: {df.columns.tolist()}")
        print(f"Data types:\n{df.dtypes}")
        
        # Display the first 5 rows of data
        print("\nFirst 5 rows of data:")
        print(df.head(5))
        
        # Display data statistics
        print("\nData statistics:")
        print(f"Number of rows: {len(df)}")
        
        # Check for date columns
        date_cols = [col for col in df.columns if df[col].dtype in ['datetime64[ns]', 'object']]
        for col in date_cols:
            try:
                # Attempt to convert the column to datetime
                test_dates = pd.to_datetime(df[col])
                # Check if conversion was successful
                if not pd.isna(test_dates).all():
                    print(f"Possible date column: {col}")
                    # Display date range
                    min_date = test_dates.min()
                    max_date = test_dates.max()
                    print(f"Date range: {min_date} to {max_date}")
            except:
                pass
        
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def extract_load_data(xlsx_file, output_csv):
    """
    Extract 2024 electricity load data from the xlsx file and aggregate it by hour
    
    Args:
        xlsx_file: Path to the input Excel file
        output_csv: Path to the output CSV file
    """
    print(f"Processing file: {xlsx_file}")
    
    # Read the Excel file
    try:
        df = pd.read_excel(xlsx_file)
        print(f"Excel file read successfully, with {len(df)} rows of data")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return False
    
    # Determine processing method based on actual Excel structure
    # Check for 'date' column and time point columns (e.g., '00:00', '00:15', etc.)
    columns = df.columns.tolist()
    if 'date' in columns and '00:00' in columns and '00:15' in columns:
        print("Standard format detected: contains 'date' column and time point columns")
        return process_standard_format(df, output_csv)
    else:
        print("Standard format not detected, attempting generic processing method")
        return process_generic_format(df, output_csv)

def process_standard_format(df, output_csv):
    """
    Process standard format Excel file: contains 'date' column and 15-minute load columns
    
    Args:
        df: DataFrame
        output_csv: Path to the output CSV file
    """
    # Check the type and values of the date column
    print(f"Date column type: {df['date'].dtype}")
    print(f"First 5 values of the date column: {df['date'].head(5).tolist()}")
    
    # Special handling for integer formatted dates
    if df['date'].dtype == 'int64':
        # Assume the date is stored as an integer in YYYYMMDD format
        try:
            # Convert integer to string and then parse as date
            df['date_string'] = df['date'].astype(str)
            df['date_parsed'] = pd.to_datetime(df['date_string'], format='%Y%m%d', errors='coerce')
            
            # Check if conversion was successful
            if df['date_parsed'].isna().all():
                print("Unable to convert integer date to datetime format")
                return False
            
            # Use the converted date column
            date_col = 'date_parsed'
            print(f"Integer date column converted to datetime format")
            print(f"Date range: {df[date_col].min()} to {df[date_col].max()}")
        except Exception as e:
            print(f"Error converting date: {e}")
            return False
    else:
        # Attempt to convert date using standard method
        try:
            df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
            if df['date_parsed'].isna().all():
                print("Unable to convert date column to datetime format")
                return False
            date_col = 'date_parsed'
            print(f"Date range: {df[date_col].min()} to {df[date_col].max()}")
        except:
            print("Unable to convert date column to datetime format")
            return False
    
    # Filter data for the year 2024
    df_2024 = df[df[date_col].dt.year == 2024].copy()
    print(f"Number of rows for 2024: {len(df_2024)}")
    
    if len(df_2024) == 0:
        print("No data found for the year 2024")
        return False
    
    # Get all 15-minute interval time columns
    time_columns = [col for col in df_2024.columns if ':' in col and len(col) == 5]
    time_columns.sort()  # Ensure sorted by time
    
    if not time_columns:
        print("No time point columns found")
        return False
    
    print(f"Found {len(time_columns)} time point columns")
    
    # Create a new DataFrame to store hourly data
    hourly_data = []
    
    # For each day
    for date in df_2024[date_col].unique():
        # Convert numpy.datetime64 to pandas Timestamp
        date_pd = pd.Timestamp(date)
        date_str = date_pd.strftime('%Y-%m-%d')
        day_data = df_2024[df_2024[date_col] == date].iloc[0]  # Get the data row for that day
        
        # Debug: Process the 0 hour data for date date_str
        print(f"Debug: Processing 0 hour data for date {date_str}")
        hour_str = "00"
        hour_columns = [f"{hour_str}:00", f"{hour_str}:15", f"{hour_str}:30", f"{hour_str}:45"]
        for col in hour_columns:
            if col in day_data:
                print(f"Value for column {col}: {day_data[col]}")
        
        # For each hour, take the sum of the 4 15-minute values
        for hour in range(24):
            hour_str = f"{hour:02d}"
            # The 4 15-minute time points for that hour
            hour_columns = [f"{hour_str}:00", f"{hour_str}:15", f"{hour_str}:30", f"{hour_str}:45"]
            
            # Filter existing columns
            existing_columns = [col for col in hour_columns if col in time_columns]
            
            if existing_columns:
                # Extract values and print debug information (only for the first hour)
                if hour == 0:
                    print(f"Columns for 0 hour: {existing_columns}")
                    for col in existing_columns:
                        print(f"Value for column {col}: {day_data[col]}")
                
                # Calculate total load (sum)
                values = [day_data[col] for col in existing_columns]
                # Filter out non-numeric values
                numeric_values = [v for v in values if isinstance(v, (int, float)) and not np.isnan(v)]
                
                if numeric_values:
                    total_load = sum(numeric_values)
                    if hour == 0:
                        print(f"Total value for 0 hour: {total_load}")
                    # Add to result list
                    hourly_data.append({
                        'datetime': f"{date_str} {hour_str}:00:00",
                        'load': total_load
                    })
    
    # Create DataFrame and sort
    result_df = pd.DataFrame(hourly_data)
    result_df['datetime'] = pd.to_datetime(result_df['datetime'])
    result_df = result_df.sort_values('datetime')
    result_df['datetime'] = result_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Add PV_power_rate column, all values set to 0
    result_df['PV_power_rate'] = 0
    
    # Display sample of processed data
    print("Sample of processed data:")
    print(result_df.head(3))
    print(f"Total of {len(result_df)} hours of data generated")
    
    # Save to CSV
    result_df.to_csv(output_csv, index=False)
    print(f"Data saved to: {output_csv}")
    
    return True

def process_generic_format(df, output_csv):
    """
    Generic method to process Excel files
    
    Args:
        df: DataFrame
        output_csv: Path to the output CSV file
    """
    # Attempt to find date/time columns
    date_col = None
    for col in df.columns:
        # If it's an integer type, it might be in YYYYMMDD format
        if pd.api.types.is_integer_dtype(df[col]):
            try:
                # Convert to string and then parse
                date_strings = df[col].astype(str)
                test_dates = pd.to_datetime(date_strings, format='%Y%m%d', errors='coerce')
                if not test_dates.isna().all():
                    df[col + '_date'] = test_dates
                    date_col = col + '_date'
                    print(f"Found integer date column: {col}, converted to: {date_col}")
                    break
            except:
                continue
        else:
            try:
                test_dates = pd.to_datetime(df[col], errors='coerce')
                if not test_dates.isna().all():
                    df[col + '_date'] = test_dates
                    date_col = col + '_date'
                    print(f"Found date/time column: {col}, converted to: {date_col}")
                    break
            except:
                continue
    
    if date_col is None:
        print("Unable to find date/time column")
        return False
    
    # Filter data for the year 2024
    df_2024 = df[pd.DatetimeIndex(df[date_col]).year == 2024].copy()
    print(f"Number of rows for 2024: {len(df_2024)}")
    
    if len(df_2024) == 0:
        print("No data found for the year 2024")
        return False
    
    # Identify possible load column
    load_col = None
    for col in df.columns:
        if col != date_col and pd.api.types.is_numeric_dtype(df[col]):
            load_col = col
            print(f"Found possible load column: {load_col}")
            break
    
    if load_col is None:
        print("Unable to find load column")
        return False
    
    # Create hourly time column
    df_2024['hour'] = pd.DatetimeIndex(df_2024[date_col]).floor('H')
    
    # Group by hour and calculate total load
    hourly_data = df_2024.groupby('hour')[load_col].sum().reset_index()
    
    # Rename columns
    hourly_data.columns = ['datetime', 'load']
    
    # Format datetime to standard format
    hourly_data['datetime'] = pd.DatetimeIndex(hourly_data['datetime']).strftime('%Y-%m-%d %H:%M:%S')
    
    # Add PV_power_rate column, all values set to 0
    hourly_data['PV_power_rate'] = 0
    
    # Display sample of processed data
    print("Sample of processed data:")
    print(hourly_data.head(3))
    print(f"Total of {len(hourly_data)} hours of data generated")
    
    # Save to CSV
    hourly_data.to_csv(output_csv, index=False)
    print(f"Data saved to: {output_csv}")
    
    return True

def process_all_files():
    """Process all xlsx files in the data directory"""
    # Get all xlsx files
    xlsx_files = glob.glob('data/raw/2024_*.xlsx')
    
    if not xlsx_files:
        print("No xlsx files found")
        return
    
    # Ensure output directory exists
    os.makedirs('data/processed', exist_ok=True)
    
    # First display the structure of the first file
    if xlsx_files:
        print("Analyzing Excel file structure...")
        show_excel_structure(xlsx_files[0])
    
    # Ask user for confirmation to continue processing
    confirm = input("Do you want to continue processing all files? (y/n): ")
    if confirm.lower() != 'y':
        print("Processing canceled")
        return
    
    # Store all processed data for merging
    all_processed_data = []
    
    for xlsx_file in xlsx_files:
        # Extract ID from the filename
        file_id = os.path.basename(xlsx_file).replace('.xlsx', '').replace('2024_', '')
        output_csv = f"data/processed/load_{file_id}_hourly.csv"
        
        # Process the file
        result = extract_load_data(xlsx_file, output_csv)
        if result:
            print(f"Successfully processed file: {xlsx_file}")
            # Read the processed CSV file and add to the merge list
            try:
                processed_df = pd.read_csv(output_csv)
                processed_df['region'] = file_id  # Add region identifier
                all_processed_data.append(processed_df)
            except Exception as e:
                print(f"Error reading processed CSV file: {e}")
        else:
            print(f"Failed to process file: {xlsx_file}")
        print("-" * 50)
    
    # Merge all regional data
    if all_processed_data:
        try:
            # Merge all data
            combined_df = pd.concat(all_processed_data, ignore_index=True)
            
            # Group by time and calculate total load
            combined_df['datetime'] = pd.to_datetime(combined_df['datetime'])
            total_load_df = combined_df.groupby('datetime')['load'].sum().reset_index()
            
            # Add PV_power_rate column, all values set to 0
            total_load_df['PV_power_rate'] = 0
            
            # Convert datetime back to string format for saving
            total_load_df['datetime'] = total_load_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Save total load CSV
            total_load_csv = "data/processed/load_total_hourly.csv"
            total_load_df.to_csv(total_load_csv, index=False)
            print(f"Total load for all regions saved to: {total_load_csv}")
            print(f"Sample of total load data:")
            print(total_load_df.head(3))
        except Exception as e:
            print(f"Error merging data: {e}")

if __name__ == "__main__":
    process_all_files()
    print("All files processed")
