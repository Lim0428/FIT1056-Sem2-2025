# gui/finance_pages.py  (REPLACE FILE)
import streamlit as st
from gui.components import stat_cards
import datetime

def _students_options(manager):
    opts = []
    for s in manager.students:
        label = f"{s.id} — {s.name}"
        opts.append((label, s.id))
    return opts

def _calc_totals(manager):
    # Total outstanding is sum of student balances
    total_outstanding = sum(getattr(s, "balance", 0.0) or 0.0 for s in manager.students)
    # Total payments count from finance_log
    total_payments = len(getattr(manager, "finance_log", []) or [])
    # Last payment time (if any)
    last_ts = "-"
    if total_payments:
        last_ts = max(p.get("timestamp", "-") for p in manager.finance_log if p)
    return total_outstanding, total_payments, last_ts

def show_finance_page(manager):
    st.subheader("💳 Finance")

    # KPIs
    tot_outstanding, tot_payments, last_ts = _calc_totals(manager)
    stat_cards([
        {"label": "Outstanding", "value": f"{tot_outstanding:.2f}", "help": "Total balance due", "icon": "💰"},
        {"label": "Payments", "value": tot_payments, "help": "Recorded transactions", "icon": "🧾"},
        {"label": "Last Payment", "value": last_ts, "help": "Most recent timestamp", "icon": "⏱️"},
    ])
    st.write("")

    tab1, tab2, tab3 = st.tabs(["➕ Record Payment", "📜 Payment History", "📤 Export"])

    # --- Record Payment ---
    with tab1:
        st.markdown("Record a new payment received from a student.")
        left, right = st.columns([2, 1])
        with left:
            opts = _students_options(manager)
            if not opts:
                st.info("No students found. Add students first.")
                return
            labels = [o[0] for o in opts]
            ids = [o[1] for o in opts]
            pick = st.selectbox("Student", labels)
            student_id = ids[labels.index(pick)]

            method = st.selectbox("Method", ["Cash", "Credit Card", "Bank Transfer", "E-Wallet"])
            amount = st.number_input("Amount", min_value=0.0, value=0.0, step=1.0)
        with right:
            st.markdown("<div class='ui-card'><h3>Tips</h3>", unsafe_allow_html=True)
            st.markdown(
                "- Default password for first login is **1234**\n"
                "- Student balance drops by the paid amount\n"
                "- All payments are logged for export"
            )
            st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Record Payment", type="primary"):
            try:
                if amount <= 0:
                    st.warning("Amount must be positive.")
                else:
                    ok = manager.record_payment(student_id, amount, method)
                    if ok:
                        st.success(f"Payment recorded for student {student_id} — amount {amount:.2f} ({method}).")
                    else:
                        st.error("Could not record payment (unknown error).")
            except Exception as e:
                st.error(f"Failed to record payment: {e}")

    # --- History ---
    with tab2:
        colA, colB = st.columns([2, 2])
        with colA:
            opts = _students_options(manager)
            labels = [o[0] for o in opts]
            ids = [o[1] for o in opts]
            pick = st.selectbox("Filter by Student", labels, key="history_filter")
            student_id = ids[labels.index(pick)]
        with colB:
            st.write("")
            st.info("Showing payments attached to the selected student (from both `student.payments` and `finance_log`).")

        # Merge student.payments & finance_log for this student (as rows)
        rows = []
        # student.payments
        stu = manager.find_student_by_id(student_id)
        if stu and getattr(stu, "payments", None):
            for p in stu.payments:
                rows.append({
                    "student_id": student_id,
                    "student_name": getattr(stu, "name", ""),
                    "amount": p.get("amount"),
                    "method": p.get("method"),
                    "timestamp": p.get("timestamp"),
                    "source": "student.payments",
                })
        # finance_log
        if getattr(manager, "finance_log", None):
            for p in manager.finance_log:
                if str(p.get("student_id")) == str(student_id):
                    rows.append({
                        "student_id": p.get("student_id"),
                        "student_name": p.get("student_name", ""),
                        "amount": p.get("amount"),
                        "method": p.get("method"),
                        "timestamp": p.get("timestamp"),
                        "source": "finance_log",
                    })

        if rows:
            rows = sorted(rows, key=lambda r: r.get("timestamp",""), reverse=True)
            st.dataframe(rows, use_container_width=True)
        else:
            st.info("No payments found for this student.")

    # --- Export ---
    with tab3:
        st.markdown("Export transaction or attendance logs to CSV.")
        kind = st.selectbox("Report Type", ["finance", "attendance"])
        today = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default = f"exports/{kind}_report_{today}.csv"

        out_path = st.text_input("Output Path", value=default)
        if st.button("Export CSV"):
            try:
                path = manager.export_report(kind, out_path)
                st.success(f"Saved to {path}")
                st.download_button("Download file", data=open(path, "rb").read(),
                                   file_name=path.split("/")[-1], mime="text/csv")
            except Exception as e:
                st.error(f"Export failed: {e}")
