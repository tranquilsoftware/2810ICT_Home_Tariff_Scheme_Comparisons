import pytest
import sys
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
)

logger.setLevel(logging.DEBUG)

# Unit Testing:
#  Tests individual units (functions/methods) in isolation.


# Test Coverage:
#  Measures which lines of code are executed during tests.
#  Helps identify untested parts of your code.


# Branch Coverage:
#  Ensures all possible code paths are tested.
#  Example: Testing both if and else branches.

# 2025-01-01 00:00:00,0.25
# 2025-01-01 01:00:00,0.42
# 2025-01-01 02:00:00,0.48

flat_rate_tariff = FlatRateTariff(rate=10.0)

tariff_data = [
    # ElectricalUsageRecord(timestamp="2025-01-01 02:00:00", kwh=300.0),
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


@pytest.mark.parametrize(
    "tariff_data, expected", [(tariff_data, sum(x.kwh for x in tariff_data))]
)
def test_total_consumption(tariff_data, expected):
    actual = _total_consumption(tariff_data)
    assert actual == expected


@pytest.mark.parametrize(
    "timestamp, expected, expected_error",
    [
        ("18:00:00", time(18, 00, 00), None),
        ("18:00:1.1", None, ValueError),
        ("18:00", None, ValueError),
        ("", None, ValueError),
        (1.1, None, AttributeError),
        (None, None, AttributeError),
    ],
)
def test_get_time_from_str(timestamp, expected, expected_error):
    if expected_error:
        with pytest.raises(expected_error):
            _get_time_from_str(timestamp)
    else:
        actual = _get_time_from_str(timestamp)
        assert actual == expected


@pytest.mark.parametrize(
    "tariff_data,tariff_rate,monthly_fee, expected",
    [
        (tariff_data, flat_rate_tariff, MONTHLY_FEE, FlatRateTariffResult(total_cost=26.299999999999997, total_consumption=1.63)),
    ],
)
def test_flatRateTariff(tariff_data, tariff_rate, monthly_fee, expected):
    actual = _flatRateTariff(
        tariff_data=tariff_data, tariff_rate=tariff_rate, monthly_fee=monthly_fee
    )
    assert actual == expected


def test_tieredTariff():
    tier1 = TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tariff_rate=0.20)
    tier2 = TierThreshold(
        threshold_level=2, low_kwh=101, high_kwh=300, tariff_rate=0.30
    )
    tier3 = TierThreshold(
        threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tariff_rate=0.40
    )
    tariff_tiers = TierTariffThresholds(
        tier1=tier1,
        tier2=tier2,
        tier3=tier3,
    )
    result = _tieredTariff(
        tariff_data=tariff_data_large,
        tariff_tiers=tariff_tiers,
        monthly_fee=MONTHLY_FEE,
    )
    assert False


def test_timeOfUseTariff():
    shoulder = TimeOfUseCategory(
        category=TimeOfUseModel.SHOULDER,
        period_start="07:00:00",
        period_end="17:59:59",
        tariff_rate=0.30,
    )
    peak = TimeOfUseCategory(
        category=TimeOfUseModel.PEAK,
        period_start="18:00:00",
        period_end="21:59:59",
        tariff_rate=0.40,
    )
    off_peak = TimeOfUseCategory(
        category=TimeOfUseModel.OFF_PEAK,
        period_start="22:00:00",
        period_end="06:59:59",
        tariff_rate=0.12,
    )
    tariff_categories = TimeOfUseTariffCategories(
        peak=peak,
        off_peak=off_peak,
        shoulder=shoulder,
    )

    actual = _timeOfUseTariff(
        tariff_data=tariff_data,
        tariff_categories=tariff_categories,
        monthly_fee=MONTHLY_FEE,
    )
    assert False


@pytest.mark.parametrize(
    "tariff_data,tariff_model,tarrif_type_data,monthly_fee,expected,expected_error",
    [
        (tariff_data, None, None, MONTHLY_FEE, None, ValueError),
        (tariff_data, TariffModel.FLAT_RATE, None, MONTHLY_FEE, None, None),
    ],
)
def test_calculateTariff(
    tariff_data, tariff_model, tarrif_type_data, monthly_fee, expected, expected_error
):
    if expected_error:
        with pytest.raises(expected_error):
            calculateTariff(
                tariff_data=tariff_data,
                tariff_model=tariff_model,
                # tarrif_type_data=tarrif_type_data,
                monthly_fee=monthly_fee,
            )
    else:
        actual = None
        assert actual == expected
