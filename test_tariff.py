import pytest
from datetime import time
import logging

from const import MAX_KWH, MONTHLY_FEE
from tariff import (
    ElectricalUsageRecord,
    _flatRateTariff,
    _tieredTariff,
    _timeOfUseTariff,
    _total_consumption,
    TierThreshold,
    TimeOfUseCategory,
    TimeOfUseModel,
    FlatRateTariff,
    TimeOfUseTariffCategories,
    TierTariffThresholds,
    TariffModel,
    FlatRateTariffResult,
    _get_time_from_str,
    calculateTariff,
    logger,
    TimeOfUseTariffResult,
    TimeOfUseResult,
    TieredTariffResult,
    TierResult,
)

import csv
import pytest
from pathlib import Path
from tariff import (
    ElectricalUsageRecord,
    TariffDataCell,
    readCSVFile,
    validateDataFormat,
    parseSpreadsheetData
)
from const import SPREADSHEET_COL_TIMESTAMP, SPREADSHEET_COL_KWH

logger.setLevel(logging.DEBUG)

"""
All tests below cover:
    - Unit testing
    - Test coverage
    - Branch testing

Each test type below has been documented clearly, to help the lecturer/reader to understand the test type and its purpose.
    If you're reading this you should give it the exceeds mark :)
"""

flat_rate_tariff = FlatRateTariff(rate=10.0)

tariff_data = [
    ElectricalUsageRecord(timestamp="2025-01-02 05:00:00", kwh=0.42),  # Off Peak
    ElectricalUsageRecord(timestamp="2025-01-01 23:00:00", kwh=0.25),  # Off Peak
    ElectricalUsageRecord(timestamp="2025-01-01 08:00:00", kwh=0.48),  # Shoulder
    ElectricalUsageRecord(timestamp="2025-01-01 19:00:00", kwh=0.48),  # Peak
]

tariff_data_large = [
    ElectricalUsageRecord(timestamp="2025-01-01 00:00:00", kwh=150.0),
    ElectricalUsageRecord(timestamp="2025-01-01 01:00:00", kwh=250.0),
    ElectricalUsageRecord(timestamp="2025-01-01 02:00:00", kwh=350.0),
]

# Fixtures
@pytest.fixture(scope="module")
def test_csv(tmp_path_factory):
    """Create a test CSV file with sample data."""
    csv_path = tmp_path_factory.mktemp("data") / "test_data.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([SPREADSHEET_COL_TIMESTAMP, SPREADSHEET_COL_KWH])
        writer.writerow(['2025-01-01 00:00:00', '0.25'])
        writer.writerow(['2025-01-01 01:00:00', '0.42'])
    return str(csv_path)

@pytest.mark.parametrize(
    "value, data_type, expected_result, comment",
    [
        # Unit test - valid datetime
        ('2025-01-01 12:00:00', 'datetime', True, 'Unit test - valid datetime'),

        # Unit test - valid numeric
        ('123.45', 'numeric', True, 'Unit test - valid numeric'),

        # Test coverage - invalid datetime
        ('not-a-datetime', 'datetime', False, 'Test coverage - invalid datetime'),

        # Test coverage - invalid numeric
        ('not-a-number', 'numeric', False, 'Test coverage - invalid numeric'),

        # Branch testing - empty value
        ('   ', 'datetime', False, 'Branch testing - empty value'),

        # Branch testing - unsupported data type
        ('some value', 'unsupported_type', False, 'Branch testing - unsupported data type'),
    ]
)
def test_validateDataFormat(
    value,
    data_type,
    expected_result,
    comment):
    """Test validateDataFormat with valid inputs, invalid formats, and edge cases."""
    cell = TariffDataCell(value, data_type)
    assert validateDataFormat(cell) is expected_result


@pytest.mark.parametrize(
    "setup_case, expected_len, expected_error_snippet, comment",
    [
        # Unit test - valid CSV file
        ("valid", 2, None, 'Unit test - valid CSV file with correct format'),

        # Branch testing - non-existent file
        ("not_found", 0, "not found", 'Branch testing - non-existent file path'),

        # Branch testing - empty file
        ("empty", 0, "CSV file is empty", 'Branch testing - empty CSV file with only header'),

        # Branch testing - path is directory
        ("is_dir", 0, "Error reading CSV file", 'Branch testing - path is a directory instead of file'),
    ]
)
def test_readCSVFile(
    setup_case,
    expected_len,
    expected_error_snippet,
    comment,
    test_csv,
    tmp_path):
    """Test readCSVFile with various file scenarios.

    Args:
        setup_case: The test case scenario to set up
        expected_len: Expected length of returned data
        expected_error_snippet: Expected error message snippet or None
        comment: Test type and description (e.g., 'Unit test - valid CSV file')
        test_csv: Fixture providing path to test CSV file
        tmp_path: Fixture providing temporary directory path
    """
    # {comment}
    if setup_case == "valid":
        file_path = test_csv

    elif setup_case == "not_found":
        file_path = "nonexistent.csv"

    elif setup_case == "empty":
        file_path = tmp_path / "empty.csv"
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([SPREADSHEET_COL_TIMESTAMP, SPREADSHEET_COL_KWH])  # header only

    elif setup_case == "is_dir":
        file_path = tmp_path / "test_dir.csv"
        file_path.mkdir()

    data, error = readCSVFile(str(file_path))
    assert len(data) == expected_len
    if expected_error_snippet:
        assert error is not None and expected_error_snippet in error
    else:
        assert error is None


@pytest.mark.parametrize(
    "filename, headers, rows, expected_len, expected_msg_snippet, comment",
    [
        # Test coverage - invalid timestamp & kWh
        ("invalid_data.csv",
         [SPREADSHEET_COL_TIMESTAMP, SPREADSHEET_COL_KWH],
         [['not-a-datetime', 'not-a-number']],
         0, "Skipping invalid row",
         'Test coverage - invalid timestamp and kWh values'),

        # Branch testing - missing required columns
        ("missing_columns.csv",
         ['wrong_column', 'another_column'],
         [['2025-01-01 00:00:00', '1.23']],
         0, "Required columns",
         'Branch testing - CSV with missing required columns'),

        # Branch testing - mixed valid/invalid rows
        ("mixed_data.csv",
         [SPREADSHEET_COL_TIMESTAMP, SPREADSHEET_COL_KWH],
         [['2025-01-01 00:00:00', '0.25'], ['2025-01-01 01:00:00', 'not-a-number']],
         1, "Skipping invalid row",
         'Branch testing - CSV with mix of valid and invalid rows'),

        # Branch testing - missing kWh value
        ("missing_value.csv",
         [SPREADSHEET_COL_TIMESTAMP, SPREADSHEET_COL_KWH],
         [['2025-01-01 00:00:00', '']],
         0, "Skipping invalid row",
         'Branch testing - CSV with empty kWh value'),
    ]
)
def test_parseSpreadsheetData(
    tmp_path,
    capsys,
    filename,
    headers,
    rows,
    expected_len,
    expected_msg_snippet,
    comment):
    """Test parseSpreadsheetData with various input scenarios.

    Args:
        tmp_path: Fixture providing temporary directory path
        capsys: Fixture for capturing stdout/stderr
        filename: Name of the test CSV file to create
        headers: List of column headers for the test CSV
        rows: List of data rows for the test CSV
        expected_len: Expected number of valid records
        expected_msg_snippet: Expected message snippet in output
        comment: Test type and description (e.g., 'Branch testing - missing required columns')
    """
    csv_path = tmp_path / filename
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)

    records = parseSpreadsheetData(str(csv_path))
    captured = capsys.readouterr()

    assert len(records) == expected_len
    assert expected_msg_snippet in captured.out

@pytest.mark.parametrize(
    "tariff_data, expected", [
        # Unit test - small usage
        (tariff_data, 1.63),  # A001

        # Unit test - large usage
        (tariff_data_large, 750),  # A002

        # Unit test - empty list
        ([], 0.0), # A003

        # Boundary test - No usage  # B001
        ([
            ElectricalUsageRecord(timestamp="2025-01-01 00:00:00", kwh=0.0),
            ElectricalUsageRecord(timestamp="2025-01-01 00:00:00", kwh=0.0),
            ElectricalUsageRecord(timestamp="2025-01-01 00:00:00", kwh=0.0)
        ], 0.0)
        ]
)
def test_total_consumption(tariff_data, expected):
    actual = _total_consumption(tariff_data)
    assert actual == expected


@pytest.mark.parametrize(
    "timestamp, expected, expected_error",
    [
        # Unit test - valid timestamp string  # A003
        ("18:00:00", time(18, 00, 00), None),

        # Branch testing - invalid format with decimal seconds  # C001
        ("18:00:1.1", None, ValueError),

        # Branch testing - missing seconds component  # C002
        ("18:00", None, ValueError),

        # Branch testing - empty string  # C003
        ("", None, ValueError),

        # Branch testing - non-string input (float)  # C004
        (1.1, None, AttributeError),

        # Branch testing - None input  # C005
        (None, None, AttributeError),
    ],
)
def test_get_time_from_str(timestamp, expected, expected_error):
    """
    Test the _get_time_from_str function with various timestamp inputs.
    This test function validates that _get_time_from_str correctly parses
    timestamp strings and returns the expected result, or raises the
    expected exception for invalid inputs.
    Args:
        timestamp: The timestamp string to be parsed by _get_time_from_str
        expected: The expected return value when no error is expected
        expected_error: The expected exception type to be raised, or None if no error expected
    Raises:
        AssertionError: If the actual result doesn't match the expected result
        The expected_error exception: If the function should raise an exception
    """

    if expected_error:
        with pytest.raises(expected_error):
            _get_time_from_str(timestamp)
    else:
        actual = _get_time_from_str(timestamp)
        assert actual == expected


@pytest.mark.parametrize(
    "tariff_data, tariff_rate, monthly_fee, expected",
    [
        # Unit test - standard tariff data with default rate
        (tariff_data, flat_rate_tariff, MONTHLY_FEE, FlatRateTariffResult(total_cost=26.3, total_consumption=1.63)), # A004

        # Unit test - large consumption data
        (tariff_data_large, flat_rate_tariff, MONTHLY_FEE, FlatRateTariffResult(total_cost=7510.0, total_consumption=750.0)), # A005

        # Branch testing - empty tariff data
        ([], flat_rate_tariff, MONTHLY_FEE, FlatRateTariffResult(total_cost=10.0, total_consumption=0.0)), # A005

        # Test coverage - custom rate and monthly fee
        ([ElectricalUsageRecord(timestamp="2025-01-01 12:00:00", kwh=50.0)], FlatRateTariff(rate=0.5), 5.0, FlatRateTariffResult(total_cost=30.0, total_consumption=50.0))  # A006
    ],
)
def test_flatRateTariff(tariff_data, tariff_rate, monthly_fee, expected):
    """
    Test the _flatRateTariff function with given parameters.
    Args:
        tariff_data: The tariff data to be processed
        tariff_rate: The flat rate to be applied for the tariff calculation
        monthly_fee: The monthly fee component of the tariff
        expected: The expected result from the _flatRateTariff function
    Asserts:
        The actual result from _flatRateTariff matches the expected result
    """

    actual = _flatRateTariff(
        tariff_data=tariff_data, tariff_rate=tariff_rate, monthly_fee=monthly_fee
    )
    assert actual == expected

@pytest.mark.parametrize(
    "tariff_data, tariff_tiers, monthly_fee, expected_result",
    [
        # Unit test - standard tiered tariff calculation with high consumption  # A007
        (
            tariff_data_large,  # 750 kWh total
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.20),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.30),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.40)
            ),
            MONTHLY_FEE,
            TieredTariffResult(
                total_cost=270.0,  # (100*0.20) + (200*0.30) + (450*0.40) + 10.0
                total_consumption=750.0,
                tier1=TierResult(tier_cost=20.0, tier_consumption=100),
                tier2=TierResult(tier_cost=60.0, tier_consumption=200),
                tier3=TierResult(tier_cost=180.0, tier_consumption=450.0)
            ),
        ),
        # Test coverage - consumption only in tier 1   # A008
        (
            [ElectricalUsageRecord(timestamp="2025-01-01 12:00:00", kwh=50.0)],
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.25),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.35),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.45)
            ),
            MONTHLY_FEE,
            TieredTariffResult(
                total_cost=22.5,  # (50*0.25) + 10.0
                total_consumption=50.0,
                tier1=TierResult(tier_cost=12.5, tier_consumption=50.0),
                tier2=TierResult(tier_cost=0.0, tier_consumption=0.0),
                tier3=TierResult(tier_cost=0.0, tier_consumption=0.0)
            ),
        ),
        # Test coverage - consumption spanning tier 1 and tier 2 only  # A009
        (
            [ElectricalUsageRecord(timestamp="2025-01-01 12:00:00", kwh=200.0)],
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.20),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.30),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.40)
            ),
            MONTHLY_FEE,
            TieredTariffResult(
                total_cost=60.0,  # (100*0.20) + (100*0.30) + 10.0
                total_consumption=200.0,
                tier1=TierResult(tier_cost=20.0, tier_consumption=100.0),
                tier2=TierResult(tier_cost=30.0, tier_consumption=100.0),
                tier3=TierResult(tier_cost=0.0, tier_consumption=0.0)
            ),
        ),
        # Branch testing - zero consumption  # A010
        (
            [],
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.20),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.30),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.40)
            ),
            MONTHLY_FEE,
            TieredTariffResult(
                total_cost=10.0,  # Only monthly fee
                total_consumption=0.0,
                tier1=TierResult(tier_cost=0.0, tier_consumption=0.0),
                tier2=TierResult(tier_cost=0.0, tier_consumption=0.0),
                tier3=TierResult(tier_cost=0.0, tier_consumption=0.0)
            ),
        ),
        # Branch testing - very high consumption (tier 3 dominant)  # A011
        (
            [ElectricalUsageRecord(timestamp="2025-01-01 12:00:00", kwh=1000.0)],
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.15),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.25),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.35)
            ),
            MONTHLY_FEE,
            TieredTariffResult(
                total_cost=320.0,  # (100*0.15) + (200*0.25) + (700*0.35) + 10.0
                total_consumption=1000.0,
                tier1=TierResult(tier_cost=15.0, tier_consumption=100.0),
                tier2=TierResult(tier_cost=50.0, tier_consumption=200.0),
                tier3=TierResult(tier_cost=245.0, tier_consumption=700.0)
            ),
        ),
        # Branch testing - different monthly fee  # A012
        (
            [ElectricalUsageRecord(timestamp="2025-01-01 12:00:00", kwh=150.0)],
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.20),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.30),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.40)
            ),
            25.0,  # Different monthly fee
            TieredTariffResult(
                total_cost=60.0,  # (100*0.20) + (50*0.30) + 25.0
                total_consumption=150.0,
                tier1=TierResult(tier_cost=20.0, tier_consumption=100.0),
                tier2=TierResult(tier_cost=15.0, tier_consumption=50.0),
                tier3=TierResult(tier_cost=0.0, tier_consumption=0.0)
            ),
        ),
        # Branch testing - multiple usage records  # A013
        (
            [
                ElectricalUsageRecord(timestamp="2025-01-01 08:00:00", kwh=75.0),
                ElectricalUsageRecord(timestamp="2025-01-01 12:00:00", kwh=125.0),
                ElectricalUsageRecord(timestamp="2025-01-01 18:00:00", kwh=100.0),
            ],
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.18),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.28),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.38)
            ),
            MONTHLY_FEE,
            TieredTariffResult(
                total_cost=84.0,  # (100*0.18) + (200*0.28) + 10.0
                total_consumption=300.0,
                tier1=TierResult(tier_cost=18.0, tier_consumption=100.0),
                tier2=TierResult(tier_cost=56.0, tier_consumption=200.0),
                tier3=TierResult(tier_cost=0.0, tier_consumption=0.0)
            ),
        ),
        # Boundary testing - consumption exactly at tier 1 boundary  # B002
        (
            [ElectricalUsageRecord(timestamp="2025-01-01 12:00:00", kwh=100.0)],
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.22),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.32),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.42)
            ),
            MONTHLY_FEE,
            TieredTariffResult(
                total_cost=32.0,  # (100*0.22) + 10.0
                total_consumption=100.0,
                tier1=TierResult(tier_cost=22.0, tier_consumption=100.0),
                tier2=TierResult(tier_cost=0.0, tier_consumption=0.0),
                tier3=TierResult(tier_cost=0.0, tier_consumption=0.0)
            ),
        ),
        # Boundary testing - consumption exactly at tier 2 boundary  # B003
        (
            [ElectricalUsageRecord(timestamp="2025-01-01 12:00:00", kwh=300.0)],
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.20),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.30),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.40)
            ),
            MONTHLY_FEE,
            TieredTariffResult(
                total_cost=90.0,  # (100*0.20) + (200*0.30) + 10.0
                total_consumption=300.0,
                tier1=TierResult(tier_cost=20.0, tier_consumption=100.0),
                tier2=TierResult(tier_cost=60.0, tier_consumption=200.0),
                tier3=TierResult(tier_cost=0.0, tier_consumption=0.0)
            ),
        ),
    ]
)
def test_tieredTariff(tariff_data, tariff_tiers, monthly_fee, expected_result):
    """
    Test the _tieredTariff function with various consumption scenarios.
    This parameterized test validates that the _tieredTariff function correctly:
    - Calculates costs across different tier boundaries
    - Handles edge cases like zero consumption
    - Properly distributes consumption across tiers
    - Applies correct tariff rates for each tier
    Args:
        tariff_data: List of electrical usage records
        tariff_tiers: Tier threshold configuration
        monthly_fee: Monthly fee amount
        expected_result: Expected TieredTariffResult
        comment: Test type and description
    Asserts:
        The actual result from _tieredTariff matches the expected_result
    """
    actual = _tieredTariff(
        tariff_data=tariff_data,
        tariff_tiers=tariff_tiers,
        monthly_fee=monthly_fee,
    )
    assert actual == expected_result


@pytest.mark.parametrize(
    "test_data, tariff_categories, monthly_fee, expected_result",
    [
        # Unit test - basic time of use calculation
        (
            [
                ElectricalUsageRecord(timestamp="2025-01-01 19:00:00", kwh=1.0),  # Peak
                ElectricalUsageRecord(timestamp="2025-01-01 08:00:00", kwh=2.0),  # Shoulder
                ElectricalUsageRecord(timestamp="2025-01-01 23:00:00", kwh=3.0),  # Off Peak
            ],
            TimeOfUseTariffCategories(
                peak=TimeOfUseCategory(TimeOfUseModel.PEAK, "18:00:00", "21:59:59", 0.40),
                off_peak=TimeOfUseCategory(TimeOfUseModel.OFF_PEAK, "22:00:00", "06:59:59", 0.12),
                shoulder=TimeOfUseCategory(TimeOfUseModel.SHOULDER, "07:00:00", "17:59:59", 0.30),
            ),
            10.0,
            TimeOfUseTariffResult(
                total_cost=11.36,  # (1*0.40) + (2*0.30) + (3*0.12) + 10.0
                total_consumption=6.0,
                peak=TimeOfUseResult(tou_cost=0.40, tou_consumption=1.0),
                off_peak=TimeOfUseResult(tou_cost=0.36, tou_consumption=3.0),
                shoulder=TimeOfUseResult(tou_cost=0.60, tou_consumption=2.0)
            ),
        ),
        # Test coverage - all peak hours
        (
            [
                ElectricalUsageRecord(timestamp="2025-01-01 18:30:00", kwh=5.0),  # Peak
                ElectricalUsageRecord(timestamp="2025-01-01 20:00:00", kwh=3.0),  # Peak
            ],
            TimeOfUseTariffCategories(
                peak=TimeOfUseCategory(TimeOfUseModel.PEAK, "18:00:00", "21:59:59", 0.50),
                off_peak=TimeOfUseCategory(TimeOfUseModel.OFF_PEAK, "22:00:00", "06:59:59", 0.15),
                shoulder=TimeOfUseCategory(TimeOfUseModel.SHOULDER, "07:00:00", "17:59:59", 0.25),
            ),
            5.0,
            TimeOfUseTariffResult(
                total_cost=9.0,  # (8*0.50) + 5.0
                total_consumption=8.0,
                peak=TimeOfUseResult(tou_cost=4.0, tou_consumption=8.0),
                off_peak=TimeOfUseResult(tou_cost=0.0, tou_consumption=0.0),
                shoulder=TimeOfUseResult(tou_cost=0.0, tou_consumption=0.0)
            ),
        ),
        # Test coverage - all shoulder hours
        (
            [
                ElectricalUsageRecord(timestamp="2025-01-01 10:00:00", kwh=2.5),  # Shoulder
                ElectricalUsageRecord(timestamp="2025-01-01 15:30:00", kwh=1.5),  # Shoulder
            ],
            TimeOfUseTariffCategories(
                peak=TimeOfUseCategory(TimeOfUseModel.PEAK, "18:00:00", "21:59:59", 0.45),
                off_peak=TimeOfUseCategory(TimeOfUseModel.OFF_PEAK, "22:00:00", "06:59:59", 0.18),
                shoulder=TimeOfUseCategory(TimeOfUseModel.SHOULDER, "07:00:00", "17:59:59", 0.32),
            ),
            8.0,
            TimeOfUseTariffResult(
                total_cost=9.28,  # (4*0.32) + 8.0
                total_consumption=4.0,
                peak=TimeOfUseResult(tou_cost=0.0, tou_consumption=0.0),
                off_peak=TimeOfUseResult(tou_cost=0.0, tou_consumption=0.0),
                shoulder=TimeOfUseResult(tou_cost=1.28, tou_consumption=4.0)
            ),
        ),
        # Branch testing - off peak spanning midnight
        (
            [
                ElectricalUsageRecord(timestamp="2025-01-01 23:30:00", kwh=1.0),  # Off Peak (evening)
                ElectricalUsageRecord(timestamp="2025-01-01 02:00:00", kwh=2.0),  # Off Peak (early morning)
                ElectricalUsageRecord(timestamp="2025-01-01 06:30:00", kwh=1.5),  # Off Peak (morning)
            ],
            TimeOfUseTariffCategories(
                peak=TimeOfUseCategory(TimeOfUseModel.PEAK, "17:00:00", "20:59:59", 0.38),
                off_peak=TimeOfUseCategory(TimeOfUseModel.OFF_PEAK, "21:00:00", "06:59:59", 0.14),
                shoulder=TimeOfUseCategory(TimeOfUseModel.SHOULDER, "07:00:00", "16:59:59", 0.28),
            ),
            12.0,
            TimeOfUseTariffResult(
                total_cost=12.63,  # (4.5*0.14) + 12.0
                total_consumption=4.5,
                peak=TimeOfUseResult(tou_cost=0.0, tou_consumption=0.0),
                off_peak=TimeOfUseResult(tou_cost=0.63, tou_consumption=4.5),
                shoulder=TimeOfUseResult(tou_cost=0.0, tou_consumption=0.0)
            ),
        ),
        # Branch testing - empty tariff data
        (
            [],
            TimeOfUseTariffCategories(
                peak=TimeOfUseCategory(TimeOfUseModel.PEAK, "18:00:00", "21:59:59", 0.40),
                off_peak=TimeOfUseCategory(TimeOfUseModel.OFF_PEAK, "22:00:00", "06:59:59", 0.12),
                shoulder=TimeOfUseCategory(TimeOfUseModel.SHOULDER, "07:00:00", "17:59:59", 0.30),
            ),
            15.0,
            TimeOfUseTariffResult(
                total_cost=15.0,  # Only monthly fee
                total_consumption=0.0,
                peak=TimeOfUseResult(tou_cost=0.0, tou_consumption=0.0),
                off_peak=TimeOfUseResult(tou_cost=0.0, tou_consumption=0.0),
                shoulder=TimeOfUseResult(tou_cost=0.0, tou_consumption=0.0)
            ),
        ),
        # Boundary testing - edge case at period boundaries
        (
            [
                ElectricalUsageRecord(timestamp="2025-01-01 17:59:59", kwh=1.0),  # Shoulder (just before peak)
                ElectricalUsageRecord(timestamp="2025-01-01 18:00:00", kwh=2.0),  # Peak (exactly at start)
                ElectricalUsageRecord(timestamp="2025-01-01 21:59:59", kwh=1.5),  # Peak (just before end)
                ElectricalUsageRecord(timestamp="2025-01-01 22:00:00", kwh=0.5),  # Off Peak (exactly at start)
            ],
            TimeOfUseTariffCategories(
                peak=TimeOfUseCategory(TimeOfUseModel.PEAK, "18:00:00", "21:59:59", 0.35),
                off_peak=TimeOfUseCategory(TimeOfUseModel.OFF_PEAK, "22:00:00", "06:59:59", 0.10),
                shoulder=TimeOfUseCategory(TimeOfUseModel.SHOULDER, "07:00:00", "17:59:59", 0.25),
            ),
            0.0,
            TimeOfUseTariffResult(
                total_cost=1.52,  # (1*0.25) + (3.5*0.35) + (0.5*0.10) + 0.0
                total_consumption=5.0,
                peak=TimeOfUseResult(tou_cost=1.22, tou_consumption=3.5),
                off_peak=TimeOfUseResult(tou_cost=0.05, tou_consumption=0.5),
                shoulder=TimeOfUseResult(tou_cost=0.25, tou_consumption=1.0)
            ),
        ),
    ]
)
def test_timeOfUseTariff(test_data, tariff_categories, monthly_fee, expected_result):
    """
    Test the _timeOfUseTariff function with given parameters.
    Args:
        test_data: Input data for tariff calculation testing
        tariff_categories: Categories/tiers used for time-of-use tariff calculation
        monthly_fee: Fixed monthly fee component of the tariff
        expected_result: Expected output value to validate against actual result
    Asserts:
        The actual result from _timeOfUseTariff matches the expected_result
    """

    actual = _timeOfUseTariff(
        tariff_data=test_data,
        tariff_categories=tariff_categories,
        monthly_fee=monthly_fee,
    )
    assert actual == expected_result

@pytest.mark.parametrize(
    "tariff_data,tariff_model,flat_rate_tariff,time_of_use_tariffs,tiered_tariffs,monthly_fee,expected_error",
    [
        # Test case: Unknown tariff model (should raise ValueError)
        (
            [ElectricalUsageRecord("2025-01-01 12:00:00", 0.5)],
            "UNKNOWN_MODEL",  # Invalid tariff model
            None, None, None, MONTHLY_FEE, ValueError
        ),
        # Test case: FLAT_RATE with None flat_rate_tariff (should raise AttributeError)
        (
            [ElectricalUsageRecord("2025-01-01 12:00:00", 0.5)],
            TariffModel.FLAT_RATE,
            None,  # Missing flat_rate_tariff data
            None, None, MONTHLY_FEE, AttributeError
        ),
        # Test case: TIME_OF_USE with None time_of_use_tariffs (should raise AttributeError)
        (
            [ElectricalUsageRecord("2025-01-01 12:00:00", 0.5)],
            TariffModel.TIME_OF_USE,
            None,
            None,  # Missing time_of_use_tariffs data
            None, MONTHLY_FEE, AttributeError
        ),
        # Test case: TIERED with None tiered_tariffs (should raise AttributeError)
        (
            [ElectricalUsageRecord("2025-01-01 12:00:00", 0.5)],
            TariffModel.TIERED,
            None, None,
            None,  # Missing tiered_tariffs data
            MONTHLY_FEE, AttributeError
        ),
    ],
)
def test_calculateTariff_error_cases(
    tariff_data, tariff_model, flat_rate_tariff, time_of_use_tariffs, tiered_tariffs, monthly_fee, expected_error
):
    """
    Test that calculateTariff function raises expected errors for invalid input cases.
    This test function verifies that the calculateTariff function properly handles
    error conditions by raising the appropriate exceptions when given invalid
    parameters or parameter combinations.
    Args:
        tariff_data: The tariff data to be processed
        tariff_model: The type of tariff model to apply
        flat_rate_tariff: Flat rate tariff configuration
        time_of_use_tariffs: Time-of-use tariff configuration
        tiered_tariffs: Tiered tariff configuration
        monthly_fee: Monthly fee amount
        expected_error: The expected exception type that should be raised
    Raises:
        The exception specified in expected_error parameter
    Note:
        This test is typically used with pytest.mark.parametrize to test
        multiple error scenarios with different input combinations.
    """
    with pytest.raises(expected_error):
        calculateTariff(
            tariff_data=tariff_data,
            tariff_model=tariff_model,
            flat_rate_tariff=flat_rate_tariff,
            time_of_use_tariffs=time_of_use_tariffs,
            tiered_tariffs=tiered_tariffs,
            monthly_fee=monthly_fee,
        )

@pytest.mark.parametrize(
    "tariff_model, tariff_data, flat_rate_tariff, time_of_use_tariffs, tiered_tariffs, monthly_fee, expected_type, expected_cost, expected_consumption",
    [
        # Unit test - FLAT_RATE success case
        (
            TariffModel.FLAT_RATE,
            [ElectricalUsageRecord("2025-01-01 12:00:00", 100.0)],
            FlatRateTariff(rate=0.25),
            None,
            None,
            MONTHLY_FEE,
            FlatRateTariffResult,
            (100.0 * 0.25) + MONTHLY_FEE,  # 35.0
            100.0,
        ),
        # Unit test - TIME_OF_USE success case
        (
            TariffModel.TIME_OF_USE,
            [ElectricalUsageRecord("2025-01-01 12:00:00", 100.0)],  # Shoulder period
            None,
            TimeOfUseTariffCategories(
                peak=TimeOfUseCategory(
                    category=TimeOfUseModel.PEAK,
                    period_start="16:00:00",
                    period_end="20:00:00",
                    tariff_rate=0.40
                ),
                off_peak=TimeOfUseCategory(
                    category=TimeOfUseModel.OFF_PEAK,
                    period_start="22:00:00",
                    period_end="06:00:00",
                    tariff_rate=0.12
                ),
                shoulder=TimeOfUseCategory(
                    category=TimeOfUseModel.SHOULDER,
                    period_start="06:00:00",
                    period_end="16:00:00",
                    tariff_rate=0.30
                )
            ),
            None,
            MONTHLY_FEE,
            TimeOfUseTariffResult,
            (100.0 * 0.30) + MONTHLY_FEE,  # 40.0
            100.0,
        ),
        # Unit test - TIERED success case
        (
            TariffModel.TIERED,
            [ElectricalUsageRecord("2025-01-01 12:00:00", 100.0)],
            None,
            None,
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.20),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.30),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.40)
            ),
            MONTHLY_FEE,
            TieredTariffResult,
            (100.0 * 0.20) + MONTHLY_FEE,  # 30.0
            100.0,
        ),
        # Test coverage - FLAT_RATE with zero consumption
        (
            TariffModel.FLAT_RATE,
            [],
            FlatRateTariff(rate=0.25),
            None,
            None,
            MONTHLY_FEE,
            FlatRateTariffResult,
            MONTHLY_FEE,  # Only monthly fee
            0.0,
        ),
        # Test coverage - TIME_OF_USE with peak period consumption
        (
            TariffModel.TIME_OF_USE,
            [ElectricalUsageRecord("2025-01-01 18:00:00", 50.0)],  # Peak period
            None,
            TimeOfUseTariffCategories(
                peak=TimeOfUseCategory(
                    category=TimeOfUseModel.PEAK,
                    period_start="16:00:00",
                    period_end="20:00:00",
                    tariff_rate=0.40
                ),
                off_peak=TimeOfUseCategory(
                    category=TimeOfUseModel.OFF_PEAK,
                    period_start="22:00:00",
                    period_end="06:00:00",
                    tariff_rate=0.12
                ),
                shoulder=TimeOfUseCategory(
                    category=TimeOfUseModel.SHOULDER,
                    period_start="06:00:00",
                    period_end="16:00:00",
                    tariff_rate=0.30
                )
            ),
            None,
            MONTHLY_FEE,
            TimeOfUseTariffResult,
            (50.0 * 0.40) + MONTHLY_FEE,  # 30.0
            50.0,
        ),
        # Branch testing - TIERED with multi-tier consumption
        (
            TariffModel.TIERED,
            [ElectricalUsageRecord("2025-01-01 12:00:00", 250.0)],
            None,
            None,
            TierTariffThresholds(
                tier1=TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.20),
                tier2=TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.30),
                tier3=TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.40)
            ),
            MONTHLY_FEE,
            TieredTariffResult,
            (100.0 * 0.20) + (150.0 * 0.30) + MONTHLY_FEE,  # 75.0
            250.0,
        ),
    ]
)
def test_calculateTariff_success_cases(
    tariff_model, tariff_data, flat_rate_tariff, time_of_use_tariffs, tiered_tariffs,
    monthly_fee, expected_type, expected_cost, expected_consumption
):
    """
    Test successful execution of calculateTariff function with valid parameters.
    This parameterized test validates that the calculateTariff function correctly
    processes different tariff models and returns the expected result types and values.
    Args:
        tariff_model: The tariff model to use for calculation
        tariff_data: List of electrical usage records
        flat_rate_tariff: Flat rate tariff configuration (if applicable)
        time_of_use_tariffs: Time-of-use tariff configuration (if applicable)
        tiered_tariffs: Tiered tariff configuration (if applicable)
        monthly_fee: Monthly fee amount
        expected_type: Expected return type of the result
        expected_cost: Expected total cost calculation
        expected_consumption: Expected total consumption
    Asserts:
        - Result is of the expected type
        - Total cost matches expected calculation
        - Total consumption matches expected value
    """
    result = calculateTariff(
        tariff_data=tariff_data,
        tariff_model=tariff_model,
        flat_rate_tariff=flat_rate_tariff,
        time_of_use_tariffs=time_of_use_tariffs,
        tiered_tariffs=tiered_tariffs,
        monthly_fee=monthly_fee,
    )
    # Verify result type
    assert isinstance(result, expected_type)

    # Verify calculations
    assert result.total_cost == expected_cost
    assert result.total_consumption == expected_consumption


@pytest.mark.parametrize(
    "tariff_model, flat_rate_tarrif, time_of_use_tariffs, tiered_tariffs, expected_error",
    [
        # Branch testing - None tariff model
        (None, None, None, None, ValueError),

        # Branch testing - Invalid string tariff model
        ("INVALID_MODEL", None, None, None,  ValueError),

        # Branch testing - No flat rate tariff data
        (TariffModel.FLAT_RATE, None, None, None, AttributeError),

        # Branch testing - No tiered tariff data
        (TariffModel.TIERED, None, None, None, AttributeError),

        # Branch testing - No time of use tariff data
        (TariffModel.TIME_OF_USE, None, None, None, AttributeError),
    ]
)
def test_calculateTariff_error_cases(tariff_model, flat_rate_tarrif, time_of_use_tariffs, tiered_tariffs, expected_error):
    """
    Test calculateTariff with invalid tariff model values.
    This test ensures that invalid tariff models raise appropriate errors.

    Args:
        tariff_model: Invalid tariff model to test
        expected_error: Expected exception type
    """

    with pytest.raises(expected_error):
        calculateTariff(
            tariff_data=tariff_data,
            tariff_model=tariff_model,
            flat_rate_tariff=flat_rate_tarrif,
            time_of_use_tariffs=time_of_use_tariffs,
            tiered_tariffs=tiered_tariffs,
            monthly_fee=MONTHLY_FEE,
        )
