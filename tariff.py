import os
import csv
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime # Used for electrical usage record, specifically the timestamp attribute.
from const import SPREADSHEET_FILE, SPREADSHEET_COL_TIMESTAMP, SPREADSHEET_COL_KWH

### DATA STRUCTURES
class ElectricalUsageRecord:
    """Singular electricity usage record."""
    def __init__(self, timestamp: str, kwh: float):
        self.timestamp = timestamp
        self.kwh = kwh

class TariffDataCell:
    """
    Singular cell of tariff data with validation.

    e.g.:
       timestamp: '2025-01-01 00:00:00'
       kWh: '0.25'
    """
    def __init__(self, value: str, data_type: str):
        self.value = value
        self.data_type = data_type
### END DATA STRUCTURES

## FUNCTION DEFINITIONS
def readCSVFile(file_path: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """
    Reads a CSV file and returns its contents as a list of dictionaries.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        Tuple containing:
        - List of dictionaries (each representing a row)
        - Error message if any, None otherwise
    """
    # Check if file exists, 
    #   return empty list and error message of its file path if it doesnt exist
    if not os.path.exists(file_path):
        return [], f"Error: File '{file_path}' not found"


    # NOTE: File exists, continue..

    # Try case as an error could definitely occur during a file read operation
    try:
        with open(
            file_path,        # File path to .csv file
            'r',              # Read only rights
            newline='',       # No newlines in the file
            encoding='utf-8'  # should be utf-8 encoding
        ) as file:
            """
            Gracefully detect the CSV format and it's dialect 
            (container class, how its formatted. e.g. doublequotes, delimiters, whitespace, etc)
            https://docs.python.org/3/library/csv.html
            """
            # Read sample to detect delimiter
            sample = file.read(1024) # Read first 1024 bytes of file, to detect dialect
            file.seek(0) # Move the file ptr back to start, as the prev operation moved it (so we can read the file properly)
            
            # Detect CSV dialect
            dialect = csv.Sniffer().sniff(sample)
            
            # Create DictReader object, so we can start reading the file, in it's detected dialect
            reader = csv.DictReader(file, dialect=dialect)
            
            # Convert to list of dicts and validate required columns
            data = [row for row in reader]
            
            # Check if file is empty
            if not data:
                return [], "Error: CSV file is empty"
                
            # Check for required columns (case sensitive: kWh has capital W)
            headers = reader.fieldnames if reader.fieldnames else []
            if SPREADSHEET_COL_TIMESTAMP not in headers or SPREADSHEET_COL_KWH not in headers:
                return [], f"Error: Required columns '{SPREADSHEET_COL_TIMESTAMP}' and '{SPREADSHEET_COL_KWH}' not found. Found: {headers}"
                
            return data, None
            
    except Exception as e:
        return [], f"Error reading CSV file: {str(e)}"

# NOTE: if else statement for our branch coverage testing.
def validateDataFormat(cell: TariffDataCell) -> bool:
    """
    Validates a singular data cell based on its expected type.
    
    Args:
        cell (TariffDataCell): The cell to validate (timestamp or kWh)
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Check if it's cell value is empty
    if not cell.value.strip():
        return False
        
    # Handle datetime validation
    # e.g.: '2025-01-01 00:00:00'
    if cell.data_type == 'datetime':
        try:
            # Try space-separated format (YYYY-MM-DD HH:MM:SS)
            datetime.strptime(cell.value, '%Y-%m-%d %H:%M:%S')
            return True
        except ValueError:
            # Value is not a valid datetime string
            return False
            
    # Handle numeric validation
    # e.g.: '0.25'
    elif cell.data_type == 'numeric':
        try:
            # Cast value to a float
            float(cell.value)
            return True
        except ValueError:
            # Value is not a valid number
            return False

    else:
        # If we reach here, the data_type is not supported
        print('Unsupported data type: ' + cell.data_type)
        return False

# NOTE: if else statement for our branch coverage testing.
def parseSpreadsheetData(spreadsheet_file: str) -> List[ElectricalUsageRecord]:
    """
    Parses the electricity usage spreadsheet data (.csv) into ElectricalUsageRecord objects.
    
    Args:
        spreadsheet_file (str): File path to the CSV spreadsheet file
        
    Returns:
        List[ElectricalUsageRecord]: List of validated usage records
    """
    # First, read the raw CSV data
    csv_data, error = readCSVFile(spreadsheet_file)
    if error:
        print(error)
        return []
        
    electrical_usage_records = []
    
    # Process each row with 0-based indexing
    for row_index, row in enumerate(csv_data):
        try:
            # Get values using column indices from const
            timestamp_val = row[SPREADSHEET_COL_TIMESTAMP].strip()
            kwh_val = row[SPREADSHEET_COL_KWH].strip()
            
            # Define TariffCells to relevant data type
            timestamp_cell = TariffDataCell(timestamp_val, 'datetime')
            kwh_cell = TariffDataCell(kwh_val, 'numeric')
            
            # Validate cells
            if validateDataFormat(timestamp_cell) and validateDataFormat(kwh_cell):
                usage_record = ElectricalUsageRecord(
                    timestamp=timestamp_val,
                    kwh=float(kwh_val)
                )
                electrical_usage_records.append(usage_record)
            else:
                print(f"Skipping invalid row at index {row_index}")
                
        except (ValueError, KeyError) as e:
            print(f"Error processing row at index {row_index}: {str(e)}")
    
    print(f"Successfully parsed {len(electrical_usage_records)} electrical usage records from {spreadsheet_file}")
    return electrical_usage_records