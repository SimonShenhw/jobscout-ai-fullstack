"""
tools.py — Agent B 的底层工具函数 / Low-level tool functions for Agent B

[ZH] 包含三个工具：薪资解析、城市名清洗、生活成本查询（内置数据）
[EN] Contains three tools: salary parsing, city cleaning, cost of living lookup (built-in data)
"""

import re


# ============================================================
# [ZH] 工具 1：薪资字符串解析器
# [EN] Tool 1: Salary String Parser
# ============================================================

def parse_salary(estimated_salary: str) -> dict:
    """
    [ZH] 支持三种格式 / [EN] Supports three formats:
      - 时薪 Hourly:  "$30 - $35/hr"   → × 40 × 52 ÷ 12
      - 年薪 Annual:  "$80k - $100k"   → ÷ 12
      - 无数据 None:  "Not Specified"  → 返回 None / Returns None
    """
    if not estimated_salary or "not specified" in estimated_salary.lower():
        return {
            "min": None,
            "max": None,
            "type": "not_specified",
            "note": "Salary not specified. Using market average.",
        }

    salary_str = estimated_salary.lower().strip()
    raw_numbers = re.findall(r'[\d,]+\.?\d*k?', salary_str)

    def to_number(s: str) -> float:
        s = s.replace(',', '')
        if s.endswith('k'):
            return float(s[:-1]) * 1000
        return float(s)

    numbers = [to_number(n) for n in raw_numbers if n]
    if not numbers:
        return {"min": None, "max": None, "type": "not_specified"}

    val_min = numbers[0]
    val_max = numbers[1] if len(numbers) >= 2 else numbers[0]

    if "/hr" in salary_str or "per hour" in salary_str or "hourly" in salary_str:
        # [ZH] 时薪 → 月薪：× 40h/周 × 52周/年 ÷ 12月
        # [EN] Hourly to monthly: × 40 hrs/week × 52 weeks/year ÷ 12 months
        monthly_min = round(val_min * 40 * 52 / 12)
        monthly_max = round(val_max * 40 * 52 / 12)
        salary_type = "hourly"
    else:
        # [ZH] 年薪 → 月薪：÷ 12 / [EN] Annual to monthly: ÷ 12
        monthly_min = round(val_min / 12)
        monthly_max = round(val_max / 12)
        salary_type = "annual"

    return {"min": monthly_min, "max": monthly_max, "type": salary_type}


# ============================================================
# [ZH] 工具 2：城市名称清洗器
# [EN] Tool 2: City Name Cleaner
# ============================================================

# [ZH] 兜底映射：小城市 → 最近大城市 / [EN] Fallback: small city → nearest big city
FALLBACK_CITIES = {
    "providence":   "Boston",
    "cambridge":    "Boston",
    "somerville":   "Boston",
    "worcester":    "Boston",
    "newark":       "New York",
    "jersey city":  "New York",
    "brooklyn":     "New York",
    "queens":       "New York",
    "long beach":   "Los Angeles",
    "anaheim":      "Los Angeles",
    "san jose":     "San Francisco",
    "oakland":      "San Francisco",
    "berkeley":     "San Francisco",
    "palo alto":    "San Francisco",
    "henderson":    "Las Vegas",
    "mountain view": "San Francisco",
    "default":      "Boston",
}


def clean_city_name(location: str) -> str:
    """
    [ZH] 清洗城市名称，去掉 'Greater' 前缀、'Area' 后缀、州名缩写
    [EN] Clean city name: remove 'Greater' prefix, 'Area' suffix, state codes
    """
    if not location:
        return "Boston"

    city = location.strip()
    city = re.sub(r'^greater\s+', '', city, flags=re.IGNORECASE)
    city = re.sub(r'\s+area$', '', city, flags=re.IGNORECASE)
    city = re.sub(r',\s*[A-Z]{2}$', '', city)
    return city.strip()


# ============================================================
# [ZH] 工具 3：生活成本查询（纯内置数据，无外部 API）
# [EN] Tool 3: Cost of Living Lookup (built-in data, no external API)
# ============================================================

# [ZH] 内置城市生活成本数据 / [EN] Built-in city cost data
# Source: Numbeo (2024 estimates) + Bureau of Labor Statistics
CITY_COST_DATA = {
    "Boston":         {"rent_min": 2000, "rent_max": 2800, "food": 600, "commute": 90,  "necessities": 200},
    "New York":       {"rent_min": 2800, "rent_max": 3800, "food": 700, "commute": 127, "necessities": 250},
    "Los Angeles":    {"rent_min": 2200, "rent_max": 3200, "food": 620, "commute": 150, "necessities": 220},
    "Seattle":        {"rent_min": 1900, "rent_max": 2700, "food": 580, "commute": 99,  "necessities": 200},
    "San Francisco":  {"rent_min": 2800, "rent_max": 3900, "food": 700, "commute": 98,  "necessities": 260},
    "Austin":         {"rent_min": 1600, "rent_max": 2300, "food": 520, "commute": 80,  "necessities": 180},
    "Chicago":        {"rent_min": 1700, "rent_max": 2400, "food": 540, "commute": 105, "necessities": 190},
    "Denver":         {"rent_min": 1700, "rent_max": 2300, "food": 530, "commute": 114, "necessities": 190},
    "Atlanta":        {"rent_min": 1500, "rent_max": 2100, "food": 500, "commute": 95,  "necessities": 170},
    "Dallas":         {"rent_min": 1500, "rent_max": 2100, "food": 510, "commute": 95,  "necessities": 180},
    "Houston":        {"rent_min": 1400, "rent_max": 2000, "food": 500, "commute": 85,  "necessities": 170},
    "Miami":          {"rent_min": 2100, "rent_max": 2900, "food": 580, "commute": 112, "necessities": 200},
    "Philadelphia":   {"rent_min": 1500, "rent_max": 2100, "food": 540, "commute": 96,  "necessities": 180},
    "Phoenix":        {"rent_min": 1400, "rent_max": 2000, "food": 490, "commute": 75,  "necessities": 170},
    "Portland":       {"rent_min": 1700, "rent_max": 2300, "food": 560, "commute": 100, "necessities": 190},
    "Washington":     {"rent_min": 2100, "rent_max": 2900, "food": 600, "commute": 134, "necessities": 210},
    "Las Vegas":      {"rent_min": 1400, "rent_max": 1900, "food": 470, "commute": 65,  "necessities": 160},
    "San Diego":      {"rent_min": 2100, "rent_max": 2900, "food": 590, "commute": 80,  "necessities": 210},
    "Nashville":      {"rent_min": 1500, "rent_max": 2100, "food": 510, "commute": 80,  "necessities": 175},
    "Minneapolis":    {"rent_min": 1500, "rent_max": 2100, "food": 510, "commute": 100, "necessities": 180},
}


def get_cost_of_living(city: str) -> dict:
    """
    [ZH] 查询城市生活成本（纯内置数据）。城市未知时回退到最近大城市。
    [EN] Look up cost of living (built-in data only). Falls back to nearest big city if unknown.
    """
    clean_city = clean_city_name(city)
    city_note = None

    if clean_city in CITY_COST_DATA:
        cost = CITY_COST_DATA[clean_city]
        source_city = clean_city
    else:
        # [ZH] 兜底：使用映射表或默认城市 / [EN] Fallback: mapping table or default
        fallback = FALLBACK_CITIES.get(clean_city.lower(), FALLBACK_CITIES["default"])
        cost = CITY_COST_DATA[fallback]
        city_note = f"No data found for {clean_city}. Showing {fallback} data instead."
        source_city = fallback

    return {
        "city": source_city,
        "rent_min": cost["rent_min"],
        "rent_max": cost["rent_max"],
        "food": cost["food"],
        "commute": cost["commute"],
        "necessities": cost["necessities"],
        "city_note": city_note,
        "source": "built-in data",
    }
