import os
import csv
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import (
    datetime,
    time,
    timedelta,
)  # Used for electrical usage record, specifically the timestamp attribute.
from const import (
    SPREADSHEET_FILE,
    SPREADSHEET_COL_TIMESTAMP,
    SPREADSHEET_COL_KWH,
    MONTHLY_FEE,
)
from enum import Enum

from dataclasses import dataclass

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TariffModel(Enum):
    FLAT_RATE = 1
    TIME_OF_USE = 2
    TIERED = 3


class TimeOfUseModel(Enum):
    PEAK = 1
    SHOULDER = 2
    OFF_PEAK = 3


@dataclass
class FlatRateTariff:
    rate: float


@dataclass
class FlatRateTariffResult:
    total_cost: float
    total_consumption: float


@dataclass
class TierThreshold:
    threshold_level: int
    low_kwh: int
    high_kwh: int
    tariff_rate: float


@dataclass
class TierTariffThresholds:
    tier1: TierThreshold
    tier2: TierThreshold
    tier3: TierThreshold


@dataclass
class TierResult:
    tier_cost: float
    tier_consumption: float


@dataclass
class TieredTariffResult:
    total_cost: float
    total_consumption: float
    tier1: TierResult
    tier2: TierResult
    tier3: TierResult


@dataclass
class TimeOfUseCategory:
    category: TimeOfUseModel
    period_start: str
    period_end: str
    tariff_rate: float


@dataclass
class TimeOfUseTariffCategories:
    peak: TimeOfUseCategory
    off_peak: TimeOfUseCategory
    shoulder: TimeOfUseCategory


@dataclass
class TimeOfUseResult:
    tou_cost: float
    tou_consumption: float


@dataclass
class TimeOfUseTariffResult:
    total_cost: float
    total_consumption: float
    peak: TimeOfUseResult
    off_peak: TimeOfUseResult
    shoulder: TimeOfUseResult


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
            file_path,  # File path to .csv file
            "r",  # Read only rights
            newline="",  # No newlines in the file
            encoding="utf-8",  # should be utf-8 encoding
        ) as file:
            """
            Gracefully detect the CSV format and it's dialect
            (container class, how its formatted. e.g. doublequotes, delimiters, whitespace, etc)
            https://docs.python.org/3/library/csv.html
            """
            # Read sample to detect delimiter
            sample = file.read(1024)  # Read first 1024 bytes of file, to detect dialect
            file.seek(
                0
            )  # Move the file ptr back to start, as the prev operation moved it (so we can read the file properly)

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
            if (
                SPREADSHEET_COL_TIMESTAMP not in headers
                or SPREADSHEET_COL_KWH not in headers
            ):
                return (
                    [],
                    f"Error: Required columns '{SPREADSHEET_COL_TIMESTAMP}' and '{SPREADSHEET_COL_KWH}' not found. Found: {headers}",
                )

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
    if cell.data_type == "datetime":
        try:
            # Try space-separated format (YYYY-MM-DD HH:MM:SS)
            datetime.strptime(cell.value, "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError:
            # Value is not a valid datetime string
            return False

    # Handle numeric validation
    # e.g.: '0.25'
    elif cell.data_type == "numeric":
        try:
            # Cast value to a float
            float(cell.value)
            return True
        except ValueError:
            # Value is not a valid number
            return False

    else:
        # If we reach here, the data_type is not supported
        print("Unsupported data type: " + cell.data_type)
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


    print(f"Successfully parsed {len(electrical_usage_records)} electrical usage records from {spreadsheet_file}")
    return electrical_usage_records


def calculateTariff(
    tariff_data: List[ElectricalUsageRecord],
    tariff_model: TariffModel,
    flat_rate_tariff: Optional[FlatRateTariff] = None,
    time_of_use_tariffs: Optional[TimeOfUseTariffCategories] = None,
    tiered_tariffs: Optional[TierTariffThresholds] = None,
    monthly_fee: float = MONTHLY_FEE,
) -> FlatRateTariffResult | TieredTariffResult | TimeOfUseTariffResult:
    """
    Calculate the cost of electricity based on the tariff model.
    """
    result = None

    match tariff_model:
        case TariffModel.FLAT_RATE:
            if flat_rate_tariff is None:
                raise AttributeError(f"No flat_rate_tariff data supplied")
            result = _flatRateTariff(
                tariff_data=tariff_data,
                tariff_rate=flat_rate_tariff,
                monthly_fee=monthly_fee,
            )
        case TariffModel.TIME_OF_USE:
            if time_of_use_tariffs is None:
                raise AttributeError(f"No time_of_use_tariffs data supplied")
            result = _timeOfUseTariff(
                tariff_data=tariff_data,
                tariff_categories=time_of_use_tariffs,
                monthly_fee=monthly_fee,
            )
        case TariffModel.TIERED:
            if tiered_tariffs is None:
                raise AttributeError(f"No tiered_tariffs data supplied")
            result = _tieredTariff(
                tariff_data=tariff_data,
                tariff_tiers=tiered_tariffs,
                monthly_fee=monthly_fee,
            )
        case _:
            raise ValueError(f"Unknown tariff model {tariff_model}")

    return result


def _total_consumption(tariff_data: List[ElectricalUsageRecord]) -> float:
    """
    Calculate the sum of kWh consumed for all tariff_data
    """
    return sum(record.kwh for record in tariff_data)


def _get_time_from_str(time_str: str) -> time:
    """
    Create a datetime.time object from a string. String must be in the %H:%M:%S format.
    """
    try:
        h, m, s = time_str.split(":")
        return time(int(h), int(m), int(s))
    except (ValueError, AttributeError):
        logger.error(f"Invalid time string format '{time_str}' unable to extract time")
        raise


def _flatRateTariff(
    tariff_data: List[ElectricalUsageRecord],
    tariff_rate: FlatRateTariff,
    monthly_fee: float = MONTHLY_FEE,
) -> FlatRateTariffResult:
    """
    Calculate a flat rate tariff.

    EG:
        Total bill = (300 x 0.25) + 10 = $85
    """
    total_consumption = _total_consumption(tariff_data)
    usage_cost = round(total_consumption * tariff_rate.rate, 2)
    result = FlatRateTariffResult(
        total_cost=usage_cost + monthly_fee,
        total_consumption=total_consumption,
    )
    return result


def _timeOfUseTariff(
    tariff_data: List[ElectricalUsageRecord],
    tariff_categories: TimeOfUseTariffCategories,
    monthly_fee: float = MONTHLY_FEE,
) -> TimeOfUseTariffResult:
    """
    Calculate the tariff cost based on time of use data.
    """
    total_consumption = _total_consumption(tariff_data)

    peak_consumption = 0.0
    off_peak_consumption = 0.0
    shoulder_consumption = 0.0

    for record in tariff_data:
        # Convert the timestamp to a datetime object.
        record_dt = datetime.strptime(record.timestamp, "%Y-%m-%d %H:%M:%S")
        record_dt_midnight = record_dt.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        record_dt_date = record_dt.date()
        record_dt_next_date_midnight = record_dt_midnight + timedelta(days=1)

        peak_start_time = _get_time_from_str(tariff_categories.peak.period_start)
        peak_end_time = _get_time_from_str(tariff_categories.peak.period_end)
        peak_start_dt = datetime.combine(record_dt_date, peak_start_time)
        peak_end_dt = datetime.combine(record_dt_date, peak_end_time)

        off_peak_start_time = _get_time_from_str(
            tariff_categories.off_peak.period_start
        )
        off_peak_end_time = _get_time_from_str(tariff_categories.off_peak.period_end)
        off_peak_start_dt = datetime.combine(record_dt_date, off_peak_start_time)
        off_peak_end_dt = datetime.combine(record_dt_date, off_peak_end_time)

        # Peak
        if peak_start_dt <= record_dt <= peak_end_dt:
            peak_consumption += record.kwh
        # Off Peak is split over two timeframes in a day.
        elif (off_peak_start_dt <= record_dt <= record_dt_next_date_midnight) or (
            record_dt_midnight <= record_dt <= off_peak_end_dt
        ):
            off_peak_consumption += record.kwh
        # Shoulder all other times
        else:
            shoulder_consumption += record.kwh

    peak_result = TimeOfUseResult(
        tou_consumption=peak_consumption,
        tou_cost=round(peak_consumption * tariff_categories.peak.tariff_rate, 2),
    )
    off_peak_result = TimeOfUseResult(
        tou_consumption=off_peak_consumption,
        tou_cost=round(off_peak_consumption * tariff_categories.off_peak.tariff_rate, 2),
    )
    shoulder_result = TimeOfUseResult(
        tou_consumption=shoulder_consumption,
        tou_cost=round(shoulder_consumption * tariff_categories.shoulder.tariff_rate, 2),
    )

    result = TimeOfUseTariffResult(
        total_cost=peak_result.tou_cost
        + off_peak_result.tou_cost
        + shoulder_result.tou_cost
        + monthly_fee,
        total_consumption=total_consumption,
        peak=peak_result,
        off_peak=off_peak_result,
        shoulder=shoulder_result,
    )

    return result


def _tieredTariff(
    tariff_data: List[ElectricalUsageRecord],
    tariff_tiers: TierTariffThresholds,
    monthly_fee: float = MONTHLY_FEE,
) -> TieredTariffResult:
    """
    Calculate a tiered tariff where prices based on kWh consumed.

    EG:
        Tier 1: first 100 kWh $0.20, Tier 2: 101-300 kWh $0.30, Tier 3: above 300 kWh $0.40
        Total bill = sum of tariff tier costs + monthly_fee
    """
    total_consumption = _total_consumption(tariff_data)

    tier1_consumption = min(total_consumption, tariff_tiers.tier1.high_kwh)
    tier2_consumption = min(
        max(0, total_consumption - tariff_tiers.tier1.high_kwh),
        tariff_tiers.tier2.high_kwh - tariff_tiers.tier1.high_kwh,
    )
    tier3_consumption = max(0, total_consumption - tariff_tiers.tier2.high_kwh)

    tier1_cost = tier1_consumption * tariff_tiers.tier1.tariff_rate
    tier2_cost = tier2_consumption * tariff_tiers.tier2.tariff_rate
    tier3_cost = tier3_consumption * tariff_tiers.tier3.tariff_rate
    total_cost = tier1_cost + tier2_cost + tier3_cost + monthly_fee

    result = TieredTariffResult(
        total_cost=round(total_cost, 2),
        total_consumption=total_consumption,
        tier1=TierResult(tier_cost=round(tier1_cost, 2), tier_consumption=tier1_consumption),
        tier2=TierResult(tier_cost=round(tier2_cost, 2), tier_consumption=tier2_consumption),
        tier3=TierResult(tier_cost=round(tier3_cost, 2), tier_consumption=tier3_consumption),
    )

    return result
