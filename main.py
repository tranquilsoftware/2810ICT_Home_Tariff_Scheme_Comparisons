
from const import SPREADSHEET_FILE
from tariff import parseSpreadsheetData, ElectricalUsageRecord

if __name__ == '__main__':
    print('2810ICT Home Tariff Python Program')

    # Define UsageRecord list, by parsing the spreadsheet file
    electrical_usage_records: list[ElectricalUsageRecord] = parseSpreadsheetData(SPREADSHEET_FILE)
    
    # Display the results
    # NOTE: if else statement for our branch coverage testing.
    if electrical_usage_records:
        print('TODO compare, calculate show output of whatever')
        # compareTariffs(usage_records)
    else:
        print("No valid usage records were found in the file.")


# FLOW (terminal python application):

# checks to see if SPREADSHEET_FILE exists in project dir (~/):
#   doesnt' exist: 
#       -> exit out  with prompt: "no SPREADSHEET_FILE found."
#   exists: 
#       validate spreadsheet .csv (cell by cell) 
#       -> parse file 
#       -> calculate 
#       -> compare 
#       -> output


# PROPOSED FUNCTIONS
# compareTariffs(TariffData t1, TariffData t2) 
# calculateTariff(TariffData t) 
# validateDataFormat(TariffDataCell tdc) -- This is used in both functions above. 
# parseSpreadsheetData(Spreadsheet spreadsheetFile) 

# MARKING RUBRIC
# Implements four Python functions meeting all requirements: 
#  - at least one with parameters, one returning a value, and one using an if–else structure. 
#  - Functions are correct, clear, and well-structured. Each function contains at least 10 lines of code (excluding comments).

# UNIT TESTING, 
# Provides unit tests for all the four implemented functions, with both positive and negative test cases. 
# Tests thoroughly validate function behavior and edge cases. Achieves a 100% pass rate. 
# Test code is clear, systematic, and well-structured.


# COVERAGE TESTING, BRANCH COVERAGE TESTING.

# Provides comprehensive tests achieving 100% statement coverage and 100% branch coverage. 
# Test cases are clear, systematic, and well-documented. Results are verified with coverage reports.
