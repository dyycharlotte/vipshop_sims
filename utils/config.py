import datetime as dt

# configurations
DATA_FILE = "./data/data.csv"
CAT_MAP = {
    "Category": "CategoryName",
    "Team": "TeamID",
    "Brand": "BrandName",
}
CAT = list(CAT_MAP.keys())

DATE = dt.date(2024, 9, 30)
DATE_MAX = dt.date(2024, 12, 31)
DATE_MIN = dt.date(2023, 1, 1)
