## Testing
```
pytest -vvv test_tariff.py --html=tariff-test-unit.html  --self-contained-html
pytest --cov=tariff --cov-report=html:tariff_statement_cov
pytest --cov=tariff --cov-branch --cov-report=html:tariff_branch_cov
```