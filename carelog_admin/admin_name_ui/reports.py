# admin_name_ui/reports.py
from __future__ import annotations

from datetime import datetime, date
import pandas as pd
import altair as alt
import streamlit as st
from typing import Dict, Any

from admin_name_utils.storage import load_db


# ----------------------------- helpers -----------------------------
def _parse_iso(iso: str) -> datetime:
    try:
        return datetime.fromisoformat((iso or "").replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()

def _ensure(db: Dict[str, Any]) -> Dict[str, Any]:
    db.setdefault("invoices", [])
    db.setdefault("patients", [])
    db.setdefault("users", [])
    return db

def _year_month_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "issued_at" in df.columns:
        dt = df["issued_at"].map(_parse_iso)
    else:
        dt = pd.to_datetime(df["date"])
    df["year"] = dt.dt.year
    df["month"] = dt.dt.month
    df["ym"] = dt.dt.strftime("%Y-%m")
    df["month_name"] = dt.dt.strftime("%b")
    return df

def _invoices_frame(db: Dict[str, Any]) -> pd.DataFrame:
    invs = db.get("invoices", [])
    if not invs:
        return pd.DataFrame(columns=[
            "id","code","status","issued_at","paid_at","patient_id","doctor_id",
            "subtotal","tax","discount","total"
        ])
    df = pd.DataFrame(invs).copy()
    for c in ("subtotal","tax","discount","total"):
        if c not in df.columns:
            df[c] = 0.0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    for c in ("status","issued_at","paid_at"):
        if c not in df.columns:
            df[c] = ""
    if "doctor_id" not in df.columns:
        df["doctor_id"] = None
    return _year_month_columns(df)

def _users_map(db: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    return {u.get("id"): u for u in db.get("users", [])}

def _patients_map(db: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    return {p.get("id"): p for p in db.get("patients", [])}

def _kpi_block(label: str, value: str, sub: str = ""):
    st.markdown(
        f"""
        <div style="border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:12px 14px;
                    background:linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));">
          <div style="font-size:13px;opacity:.8">{label}</div>
          <div style="font-size:24px;font-weight:800">{value}</div>
          <div style="font-size:12px;opacity:.75">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _pct(a: float, b: float) -> str:
    if b == 0:
        return "—"
    s = (a - b) / b * 100.0
    arrow = "▲" if s >= 0 else "▼"
    return f"{arrow} {abs(s):.1f}%"

def _mo_range_df(df: pd.DataFrame, months_back: int = 12, only_paid: bool = False) -> pd.DataFrame:
    if df.empty:
        return df
    # month anchor at start of current month
    start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    months = pd.date_range(end=start, periods=months_back, freq="MS")
    wanted = set(m.strftime("%Y-%m") for m in months)
    dff = df[df["ym"].isin(wanted)].copy()
    if only_paid:
        dff = dff[dff["status"].str.lower() == "paid"].copy()
    return dff

def _moving_avg(series: pd.Series, n: int = 3) -> pd.Series:
    return series.rolling(n, min_periods=1).mean()

def _money(x: float) -> str:
    return f"RM {x:,.2f}"


# ----------------------------- render -----------------------------
def render():
    db = _ensure(load_db())
    df = _invoices_frame(db)
    users = _users_map(db)
    patients = _patients_map(db)

    st.markdown(
        "<h3 style='display:flex;align-items:center;gap:10px;margin:0 0 6px 0;'>"
        "📊 <span>Reports</span></h3>"
        "<p style='margin:0;opacity:.8;'>Revenue analytics, provider performance, and invoice status mix.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # -------------------- Filters / Controls --------------------
    colA, colB, colC, colD = st.columns([1, 1, 1, 1])
    with colA:
        only_paid = st.toggle("Paid only", value=True)
    with colB:
        months_back = st.select_slider("Window", options=[6, 9, 12, 15, 18, 24], value=12)
    with colC:
        year_pick = st.selectbox("Breakdown Year", sorted(df["year"].unique()) if not df.empty else [date.today().year],
                                 index=0)
    with colD:
        if st.button("Export breakdown CSV", use_container_width=True, disabled=df.empty):
            st.session_state["do_export_breakdown"] = True
        else:
            st.session_state.pop("do_export_breakdown", None)

    # -------------------- KPIs --------------------
    view_df = _mo_range_df(df, months_back=months_back, only_paid=only_paid)
    total_view = float(view_df["total"].sum()) if not view_df.empty else 0.0
    ytd_df = df[(df["year"] == datetime.utcnow().year) & ((~only_paid) | (df["status"].str.lower() == "paid"))]
    ytd_total = float(ytd_df["total"].sum()) if not ytd_df.empty else 0.0
    ar_unpaid = float(df[df["status"].str.lower() == "unpaid"]["total"].sum()) if not df.empty else 0.0

    if not df.empty:
        this_m = datetime.utcnow().strftime("%Y-%m")
        prev_m = (pd.to_datetime(this_m + "-01") - pd.offsets.MonthBegin(1)).strftime("%Y-%m")
        this_val = float(df[(df["ym"] == this_m) & ((~only_paid) | (df["status"].str.lower()=="paid"))]["total"].sum())
        prev_val = float(df[(df["ym"] == prev_m) & ((~only_paid) | (df["status"].str.lower()=="paid"))]["total"].sum())
    else:
        this_val, prev_val = 0.0, 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_block("Window total", _money(total_view), f"Last {months_back} months • {'Paid' if only_paid else 'All'}")
    with k2:
        _kpi_block("YTD revenue", _money(ytd_total))
    with k3:
        _kpi_block("A/R (Unpaid)", _money(ar_unpaid))
    with k4:
        _kpi_block("This month vs prev", _money(this_val), _pct(this_val, prev_val))

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # -------------------- Revenue chart (LINE + MA3) --------------------
    st.markdown("#### Revenue (last months)")
    if view_df.empty:
        st.info("No invoices yet.")
    else:
        by_mo = (
            view_df.groupby(["ym"], as_index=False)[["subtotal","tax","discount","total"]]
            .sum()
            .sort_values("ym")
        )
        by_mo["ma3"] = _moving_avg(by_mo["total"], 3)

        base = alt.Chart(by_mo).encode(
            x=alt.X("ym:N", title="Month", sort=None, axis=alt.Axis(labelAngle=0))
        )

        total_line = base.mark_line(point=True).encode(
            y=alt.Y("total:Q", title="Revenue (RM)"),
            tooltip=[
                alt.Tooltip("ym:N", title="Month"),
                alt.Tooltip("total:Q", title="Total", format=",.2f"),
                alt.Tooltip("subtotal:Q", title="Subtotal", format=",.2f"),
                alt.Tooltip("tax:Q", title="Tax", format=",.2f"),
                alt.Tooltip("discount:Q", title="Discount", format=",.2f"),
            ],
        )

        ma_line = base.mark_line(point=True, strokeDash=[6,4]).encode(
            y=alt.Y("ma3:Q", title=None),
            tooltip=[alt.Tooltip("ma3:Q", title="MA(3)", format=",.2f")],
        )

        st.altair_chart((total_line + ma_line).properties(height=280), use_container_width=True)

        # MoM change table
        mom_rows = []
        for i in range(1, len(by_mo)):
            cur = by_mo.iloc[i]
            prev = by_mo.iloc[i - 1]
            prev_total = float(prev["total"])
            if prev_total == 0:
                mom = "—"
            else:
                s = (float(cur["total"]) - prev_total) / prev_total * 100.0
                arrow = "▲" if s >= 0 else "▼"
                mom = f"{arrow} {abs(s):.1f}%"
            mom_rows.append({"Month": cur["ym"], "MoM": mom})
        if mom_rows:
            st.caption("MoM change")
            st.dataframe(pd.DataFrame(mom_rows), hide_index=True, use_container_width=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.divider()

    # -------------------- Monthly breakdown table --------------------
    if df.empty:
        st.info("No data.")
        return

    st.markdown("#### Monthly breakdown")
    breakdown = (
        df[(df["year"] == year_pick) & ((~only_paid) | (df["status"].str.lower() == "paid"))]
        .groupby(["ym","month"], as_index=False)[["subtotal","tax","discount","total"]]
        .sum()
        .sort_values(["month"])
    )
    split = (
        df[df["year"] == year_pick]
        .groupby(["ym","status"], as_index=False)["total"]
        .sum()
        .pivot(index="ym", columns="status", values="total")
        .fillna(0.0)
        .reset_index()
    )
    merged = breakdown.merge(split, on="ym", how="left")
    for c in ["paid","unpaid","void"]:
        if c not in merged.columns:
            merged[c] = 0.0
    merged_display = merged.rename(columns={
        "ym":"Month", "subtotal":"Subtotal (RM)", "tax":"Tax (RM)",
        "discount":"Discount (RM)", "total":"Total (RM)",
        "paid":"Paid (RM)", "unpaid":"Unpaid (RM)", "void":"Void (RM)"
    })
    st.dataframe(merged_display, hide_index=True, use_container_width=True)

    if st.session_state.get("do_export_breakdown"):
        csv = merged_display.to_csv(index=False).encode("utf-8")
        st.download_button("Download breakdown CSV", data=csv, file_name=f"breakdown_{year_pick}.csv",
                           mime="text/csv", use_container_width=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.divider()

    # -------------------- By Provider --------------------
    st.markdown("#### Revenue by provider")
    prov_df = df.copy()
    if only_paid:
        prov_df = prov_df[prov_df["status"].str.lower() == "paid"]
    prov = (
        prov_df.groupby("doctor_id", as_index=False)["total"].sum().sort_values("total", ascending=False)
    )
    if not prov.empty:
        prov["provider"] = prov["doctor_id"].map(lambda i: (users.get(i) or {}).get("name", f"#{i}"))
        prov["role"] = prov["doctor_id"].map(lambda i: ((users.get(i) or {}).get("role","") or "").replace("_"," ").title())
        prov["share_%"] = (prov["total"] / prov["total"].sum() * 100.0).round(1)

        chart = alt.Chart(prov).mark_bar().encode(
            x=alt.X("total:Q", title="Revenue (RM)"),
            y=alt.Y("provider:N", sort="-x", title=""),
            color=alt.Color("role:N", title="Role"),
            tooltip=[
                alt.Tooltip("provider:N", title="Provider"),
                alt.Tooltip("role:N", title="Role"),
                alt.Tooltip("total:Q", title="Total", format=",.2f"),
                alt.Tooltip("share_%:Q", title="Share %"),
            ],
        ).properties(height=max(160, 26 * len(prov)))
        st.altair_chart(chart, use_container_width=True)

        st.dataframe(
            prov[["provider","role","total","share_%"]].rename(columns={"total":"Total (RM)"}),
            hide_index=True, use_container_width=True
        )
    else:
        st.info("No provider revenue in the selected filter.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.divider()

    # -------------------- Top Patients --------------------
    st.markdown("#### Top patients")
    pat_df = df.copy()
    if only_paid:
        pat_df = pat_df[pat_df["status"].str.lower() == "paid"]
    top_pat = (
        pat_df.groupby("patient_id", as_index=False)["total"].sum().sort_values("total", ascending=False).head(10)
    )
    if not top_pat.empty:
        top_pat["patient"] = top_pat["patient_id"].map(lambda i: (patients.get(i) or {}).get("name", f"#{i}"))
        bar = alt.Chart(top_pat).mark_bar().encode(
            x=alt.X("total:Q", title="Revenue (RM)"),
            y=alt.Y("patient:N", sort="-x", title=""),
            tooltip=[alt.Tooltip("patient:N"), alt.Tooltip("total:Q", format=",.2f")],
        ).properties(height=max(160, 26 * len(top_pat)))
        st.altair_chart(bar, use_container_width=True)
    else:
        st.info("No patient revenue in the selected filter.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.divider()

    # -------------------- Status mix --------------------
    st.markdown("#### Status mix")
    if df.empty:
        st.info("No data.")
    else:
        pie_src = df.groupby("status", as_index=False)["id"].count().rename(columns={"id":"count"})
        pie_src["status"] = pie_src["status"].str.title()
        pie = alt.Chart(pie_src).mark_arc(innerRadius=50).encode(
            theta="count:Q",
            color=alt.Color("status:N", title="Status"),
            tooltip=[alt.Tooltip("status:N"), alt.Tooltip("count:Q", title="Count")]
        ).properties(height=240)
        st.altair_chart(pie, use_container_width=False)
