import pytest
import sys

from const import MAX_KWH
from tariff import (ElectricalUsageRecord, _flatRateTariff, _tieredTariff, _timeOfUseTariff, TierThreshold)

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

tariff_data = [
    # ElectricalUsageRecord(timestamp="2025-01-01 02:00:00", kwh=300.0),
    ElectricalUsageRecord(timestamp="2025-01-01 00:00:00", kwh=0.25),
    ElectricalUsageRecord(timestamp="2025-01-01 01:00:00", kwh=0.42),
    ElectricalUsageRecord(timestamp="2025-01-01 02:00:00", kwh=0.48),
]

tariff_data_large = [
    ElectricalUsageRecord(timestamp="2025-01-01 00:00:00", kwh=150.0),
    ElectricalUsageRecord(timestamp="2025-01-01 01:00:00", kwh=250.0),
    ElectricalUsageRecord(timestamp="2025-01-01 02:00:00", kwh=350.0),
]

@pytest.mark.parametrize("tariff_data,tarrif_rate,monthly_fee, expected", [
    # (tariff_data, 0.25, 10.0, 85.0),
    (tariff_data, 0.25, 10.0, 10.2875),
])
def test_flatRateTarrif(tariff_data, tarrif_rate, monthly_fee, expected):
    actual = _flatRateTariff(tariff_data, tarrif_rate, monthly_fee)
    assert actual == expected

def test_tieredTariff():
    pass

def test_timeOfUseTariff():
    tier1 = TierThreshold(threshold_level=1, low_kwh=0, high_kwh=100, tarrif_rate=0.20)
    tier2 = TierThreshold(threshold_level=2, low_kwh=101, high_kwh=300, tarrif_rate=0.30)
    tier3 = TierThreshold(threshold_level=3, low_kwh=301, high_kwh=MAX_KWH, tarrif_rate=0.40)
    result = _tieredTariff(tariff_data_large, tier1, tier2, tier3)
    assert False
