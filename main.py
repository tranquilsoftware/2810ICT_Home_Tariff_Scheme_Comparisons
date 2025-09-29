from const import SPREADSHEET_FILE
from tariff import parseSpreadsheetData, ElectricalUsageRecord

if __name__ == "__main__":
    print("2810ICT Home Tariff Python Program")

    # Define UsageRecord list, by parsing the spreadsheet file
    electrical_usage_records: list[ElectricalUsageRecord] = parseSpreadsheetData(
        SPREADSHEET_FILE
    )

    # Display the results
    # NOTE: if else statement for our branch coverage testing.
    if electrical_usage_records:
        print("TODO compare, calculate show output of whatever")
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