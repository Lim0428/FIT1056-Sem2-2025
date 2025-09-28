import streamlit as st

def show_payment_page(manager):
    st.header("Finance Report")

    st.subheader("Balances")
    balances = [
        {"ID": s.id, "Name": s.name, "Balance": s.balance, "Payments": len(s.payments)}
        for s in manager.students
    ]
    st.dataframe(balances)

    st.subheader("Record Payment")
    with st.form("payment_form"):
        sid = st.selectbox("Select Student", [s.id for s in manager.students])
        amount = st.number_input("Amount", min_value=0.0, step=10.0)
        note = st.text_input("Note (optional)")
        submitted = st.form_submit_button("Submit Payment")
        if submitted and amount > 0:
            manager.record_payment(sid, amount, note)
            st.success(f"Payment recorded for student {sid}")

