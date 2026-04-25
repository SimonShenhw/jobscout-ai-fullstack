# Tests

[ZH] 单元测试目录 / [EN] Unit test directory

## Setup

```bash
pip install pytest pytest-asyncio
```

## Run All Tests

```bash
pytest tests/ -v
```

## Run Specific Test File

```bash
pytest tests/test_agent_b_tools.py -v
pytest tests/test_api_client.py -v
```

## Coverage

```bash
pip install pytest-cov
pytest tests/ --cov=agent_b_cost --cov=frontend_ui
```

## Files

- `test_agent_b_tools.py` — Tests for `parse_salary`, `clean_city_name`, `get_cost_of_living`
- `test_api_client.py` — Tests for `run_pipeline`, `get_interview_feedback`, mock data
