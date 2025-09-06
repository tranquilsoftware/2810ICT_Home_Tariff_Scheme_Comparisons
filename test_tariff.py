import pytest

from tariff import (ElectricalUsageRecord, _flatRateTariff)

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

tarrif_data = [
    ElectricalUsageRecord(timestamp="2025-01-01 00:00:00", kwh=0.25),
    ElectricalUsageRecord(timestamp="2025-01-01 01:00:00", kwh=0.42),
    ElectricalUsageRecord(timestamp="2025-01-01 02:00:00", kwh=0.48),
]

@pytest.mark.parametrize("tarrif_data,tarrif_rate,montly_fee, expected", [
    (tarrif_data, 0.25, 10.0, 10.2875)
])
def test_flatRateTarrif(tarrif_data, tarrif_rate, montly_fee, expected):
    actual = _flatRateTariff(tarrif_data, tarrif_rate, montly_fee)
    assert actual == expected
