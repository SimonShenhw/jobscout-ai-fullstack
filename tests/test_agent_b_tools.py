"""
[ZH] Agent B 工具函数单元测试 / [EN] Unit tests for Agent B tool functions

Run with: pytest tests/test_agent_b_tools.py -v
"""
import sys
import os
import pytest

# [ZH] 把 agent_b_cost 加进路径 / [EN] Add agent_b_cost to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent_b_cost"))

from tools import (
    parse_salary,
    clean_city_name,
    get_cost_of_living,
    CITY_COST_DATA,
    FALLBACK_CITIES,
)


# ==========================================
# parse_salary tests
# ==========================================

class TestParseSalary:
    def test_hourly_range(self):
        result = parse_salary("$30 - $35/hr")
        assert result["type"] == "hourly"
        # [ZH] 30/hr × 40h × 52 / 12 = 5200 / [EN] same
        assert result["min"] == 5200
        assert result["max"] == round(35 * 40 * 52 / 12)

    def test_annual_range_k(self):
        result = parse_salary("$80k - $100k")
        assert result["type"] == "annual"
        assert result["min"] == round(80000 / 12)
        assert result["max"] == round(100000 / 12)

    def test_annual_range_full(self):
        result = parse_salary("$80,000 - $100,000")
        assert result["type"] == "annual"
        assert result["min"] == round(80000 / 12)

    def test_not_specified(self):
        result = parse_salary("Not Specified")
        assert result["type"] == "not_specified"
        assert result["min"] is None
        assert result["max"] is None

    def test_empty_string(self):
        result = parse_salary("")
        assert result["type"] == "not_specified"

    def test_single_number(self):
        result = parse_salary("$50/hr")
        assert result["type"] == "hourly"
        assert result["min"] == result["max"]

    def test_per_hour_variant(self):
        result = parse_salary("$25 per hour")
        assert result["type"] == "hourly"


# ==========================================
# clean_city_name tests
# ==========================================

class TestCleanCityName:
    def test_greater_prefix(self):
        assert clean_city_name("Greater Boston Area") == "Boston"

    def test_state_suffix(self):
        assert clean_city_name("Boston, MA") == "Boston"

    def test_already_clean(self):
        assert clean_city_name("New York") == "New York"

    def test_combined(self):
        assert clean_city_name("Greater Los Angeles Area") == "Los Angeles"

    def test_empty(self):
        assert clean_city_name("") == "Boston"

    def test_none(self):
        assert clean_city_name(None) == "Boston"

    def test_whitespace(self):
        assert clean_city_name("  Boston  ") == "Boston"


# ==========================================
# get_cost_of_living tests
# ==========================================

class TestGetCostOfLiving:
    def test_known_city(self):
        result = get_cost_of_living("Boston")
        assert result["city"] == "Boston"
        assert result["rent_min"] == 2000
        assert result["source"] == "built-in data"
        assert result["city_note"] is None

    def test_unknown_city_falls_back(self):
        result = get_cost_of_living("Providence")
        assert result["city"] == "Boston"
        assert "Providence" in result["city_note"]

    def test_default_fallback(self):
        result = get_cost_of_living("Random City Nowhere")
        assert result["city"] == "Boston"  # default fallback
        assert result["city_note"] is not None

    def test_dirty_city_name(self):
        result = get_cost_of_living("Greater Seattle Area")
        assert result["city"] == "Seattle"

    def test_all_cities_have_required_fields(self):
        """[ZH] 验证所有内置城市数据完整 / [EN] Verify all built-in cities have required fields."""
        required = {"rent_min", "rent_max", "food", "commute", "necessities"}
        for city, data in CITY_COST_DATA.items():
            assert required.issubset(data.keys()), f"{city} missing fields"
            assert data["rent_min"] < data["rent_max"], f"{city} rent_min >= rent_max"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
