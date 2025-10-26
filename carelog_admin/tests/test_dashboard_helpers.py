# tests/test_dashboard_helpers.py
from datetime import date
import pandas as pd

from admin_name_ui.dashboard import _add_months, _build_month_df

def test_add_months_wraps_years():
    assert _add_months(date(2025, 1, 1), 1)  == date(2025, 2, 1)
    assert _add_months(date(2025, 11, 1), 2) == date(2026, 1, 1)
    assert _add_months(date(2025, 1, 1), -1) == date(2024, 12, 1)

def test_build_month_df_mom_ma3():
    bill = {
        "2025-01": 100.0,
        "2025-02": 150.0,
        "2025-04":  50.0,  # missing March should be treated as 0
    }
    df = _build_month_df(bill, date(2025,1,1), date(2025,4,1))
    # months present
    assert list(df["MonthKey"]) == ["2025-01","2025-02","2025-03","2025-04"]
    # zero month flagged
    assert float(df.loc[df["MonthKey"]=="2025-03","Amount"].iloc[0]) == 0.0
    # MoM first is 0 by design
    assert abs(float(df["MoM_pct"].iloc[0]) - 0.0) < 1e-9
    # MA3 averages over available months
    assert "MA3" in df.columns
