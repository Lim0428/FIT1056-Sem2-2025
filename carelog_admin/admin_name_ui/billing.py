# admin_name_ui/billing.py
from __future__ import annotations

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

from admin_name_utils.storage import load_db, save_db

# =============== Helpers ===============

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _parse_iso(iso: str) -> datetime:
    return datetime.fromisoformat((iso or "").replace("Z", "+00:00"))

def _ensure_shapes(db: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure required arrays exist and invoices have safe defaults.
       Also backfills missing invoice codes (persisting them)."""
    db.setdefault("invoices", [])
    db.setdefault("patients", [])
    db.setdefault("users", [])
    db.setdefault("appointments", [])

    changed = False
    used_codes = set(str(i.get("code")) for i in db["invoices"] if i.get("code"))

    def next_code() -> str:
        year = datetime.utcnow().strftime("%Y")
        prefix = f"INV-{year}-"
        seqs = []
        for c in used_codes:
            if isinstance(c, str) and c.startswith(prefix):
                try:
                    seqs.append(int(c.replace(prefix, "")))
                except Exception:
                    pass
        nxt = (max(seqs) + 1) if seqs else 1
        code = f"{prefix}{nxt:04d}"
        used_codes.add(code)
        return code

    for inv in db["invoices"]:
        inv.setdefault("id", 0)
        if not inv.get("code"):
            inv["code"] = next_code()
            changed = True
        inv.setdefault("patient_id", None)
        inv.setdefault("doctor_id", None)   # keeps compatibility (provider id stored here)
        inv.setdefault("appt_id", None)
        inv.setdefault("items", [])
        inv.setdefault("tax_pct", 0.0)
        inv.setdefault("discount", 0.0)
        inv.setdefault("subtotal", 0.0)
        inv.setdefault("tax", 0.0)
        inv.setdefault("total", 0.0)
        inv.setdefault("status", "unpaid")
        inv.setdefault("issued_at", _now_iso())
        inv.setdefault("paid_at", "")
        inv.setdefault("notes", "")

    if changed:
        save_db(db)

    return db

def _patient_by_id(db, pid: int):
    return next((p for p in db.get("patients", []) if p.get("id") == pid), None)

def _user_by_id(db, uid: int):
    return next((u for u in db.get("users", []) if u.get("id") == uid), None)

def _appt_by_id(db, aid: int):
    return next((a for a in db.get("appointments", []) if a.get("id") == aid), None)

def _next_invoice_id(db) -> int:
    return max([i.get("id", 0) for i in db.get("invoices", [])] + [0]) + 1

def _next_invoice_code(db) -> str:
    year = datetime.utcnow().strftime("%Y")
    prefix = f"INV-{year}-"
    seqs = []
    for inv in db.get("invoices", []):
        code = str(inv.get("code") or "")
        if code.startswith(prefix):
            try:
                seqs.append(int(code.replace(prefix, "")))
            except Exception:
                pass
    nxt = (max(seqs) + 1) if seqs else 1
    return f"{prefix}{nxt:04d}"

def _totals_from_items(items: List[Dict[str, Any]], tax_pct: float, discount: float) -> Dict[str, float]:
    subtotal = sum((float(it.get("qty", 0)) * float(it.get("unit_price", 0.0))) for it in items)
    tax = max(subtotal * (tax_pct / 100.0), 0.0)
    disc = max(float(discount or 0.0), 0.0)
    total = max(subtotal + tax - disc, 0.0)
    return {"subtotal": round(subtotal, 2), "tax": round(tax, 2), "discount": round(disc, 2), "total": round(total, 2)}

def _status_pill(s: str) -> str:
    s = (s or "unpaid").lower()
    tone = {"paid":"rgba(34,197,94,.25)","unpaid":"rgba(250,204,21,.25)","void":"rgba(248,113,113,.25)"}.get(s,"rgba(255,255,255,.12)")
    label = s.title()
    return f"<span style='padding:3px 8px;border-radius:999px;background:{tone};border:1px solid rgba(255,255,255,.18);'>{label}</span>"

def _appt_label(a: Dict[str, Any], db: Dict[str, Any]) -> str:
    if not a: return "—"
    p = _patient_by_id(db, a.get("patient_id"))
    d = _user_by_id(db, a.get("doctor_id"))
    when = _parse_iso(a["start_iso"]).strftime("%b %d, %H:%M")
    return f"#{a.get('id')} • {when} • {p.get('name') if p else 'Patient ?'} → {d.get('name') if d else 'Provider ?'}"

def _patient_label(p: Dict[str, Any]) -> str:
    if not p: return "—"
    return f"{p.get('id')} — {p.get('name')}"

# NEW: providers = doctors + psychological counselors
def _provider_options(db):
    return [u for u in db.get("users", []) if u.get("role") in ("doctor", "psychological_counselor")]

def _provider_label(u: Dict[str, Any]) -> str:
    rid = u.get("id")
    name = u.get("name","")
    role = (u.get("role","") or "").replace("_"," ").title()
    return f"{rid} — {name} ({role})"

# =============== Page ===============

def render():
    db = _ensure_shapes(load_db())
    user = st.session_state.get("user", {"id": 0, "name": "Admin", "role": "admin"})

    st.markdown(
        "<h3 style='display:flex;align-items:center;gap:10px;margin:0 0 6px 0;'>"
        "💳 <span>Billing</span></h3>"
        "<p style='margin:0;opacity:.8;'>Invoices, payments and exports.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    invoices: List[Dict[str, Any]] = db.get("invoices", [])
    patients: List[Dict[str, Any]] = db.get("patients", [])
    appts: List[Dict[str, Any]] = db.get("appointments", [])

    # ---------- KPIs ----------
    unpaid = [i for i in invoices if i.get("status","unpaid") == "unpaid"]
    unpaid_total = sum(float(i.get("total", 0.0)) for i in unpaid)
    this_month = datetime.utcnow().replace(day=1)
    paid_this_month = sum(float(i.get("total", 0.0)) for i in invoices
                          if i.get("status") == "paid" and i.get("paid_at") and
                             _parse_iso(i.get("paid_at")).date() >= this_month.date())

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown("<div style='font-size:13px;opacity:.8'>Unpaid</div><div style='font-size:22px;font-weight:700'>"
                    f"{len(unpaid)} • RM {unpaid_total:,.2f}</div>", unsafe_allow_html=True)
    with k2:
        st.markdown("<div style='font-size:13px;opacity:.8'>Paid this month</div><div style='font-size:22px;font-weight:700'>"
                    f"RM {paid_this_month:,.2f}</div>", unsafe_allow_html=True)
    with k3:
        st.markdown("<div style='font-size:13px;opacity:.8'>Total invoices</div><div style='font-size:22px;font-weight:700'>"
                    f"{len(invoices)}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ---------- Filters + Export ----------
    fc1, fc2, fc3 = st.columns([1, 1, 1])
    with fc1:
        status_filter = st.selectbox("Status", ["All", "Unpaid", "Paid", "Void"], index=0)
    with fc2:
        search = st.text_input("Search code / patient / provider", placeholder="e.g., INV-2025, Baka, Li Hang")
    with fc3:
        if st.button("Export CSV", use_container_width=True):
            rows = []
            for i in invoices:
                p = _patient_by_id(db, i.get("patient_id"))
                d = _user_by_id(db, i.get("doctor_id"))  # provider
                rows.append({
                    "Code": i.get("code",""),
                    "Issued At": i.get("issued_at",""),
                    "Status": i.get("status",""),
                    "Patient": p.get("name") if p else "",
                    "Provider": d.get("name") if d else "",
                    "Subtotal": i.get("subtotal", 0.0),
                    "Tax": i.get("tax", 0.0),
                    "Discount": i.get("discount", 0.0),
                    "Total": i.get("total", 0.0),
                    "Paid At": i.get("paid_at",""),
                })
            df = pd.DataFrame(rows)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, file_name="invoices.csv", mime="text/csv", use_container_width=True)

    # ---------- Filtered Table ----------
    def include(i: Dict[str, Any]) -> bool:
        s_ok = (status_filter == "All") or (i.get("status","unpaid").lower() == status_filter.lower())
        if not s_ok:
            return False
        if search:
            p = _patient_by_id(db, i.get("patient_id") or 0) or {}
            d = _user_by_id(db, i.get("doctor_id") or 0) or {}
            hay = f"{i.get('code','')} {p.get('name','')} {d.get('name','')}".lower()
            if search.lower() not in hay:
                return False
        return True

    filtered = [i for i in invoices if include(i)]
    filtered = sorted(filtered, key=lambda x: x.get("issued_at",""), reverse=True)

    rows = []
    for i in filtered:
        p = _patient_by_id(db, i.get("patient_id"))
        d = _user_by_id(db, i.get("doctor_id"))   # provider
        rows.append({
            "Code": i.get("code",""),
            "Issued": (i.get("issued_at") or "")[:10],
            "Patient": p.get("name","") if p else "",
            "Provider": d.get("name","") if d else "",
            "Status": i.get("status","unpaid").title(),
            "Total (RM)": f"{float(i.get('total',0.0)):.2f}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ---------- Create Invoice ----------
    with st.expander("➕ Create Invoice", expanded=False):
        st.caption("Create from an appointment (recommended) or ad-hoc for a patient.")
        pats = patients
        if not pats:
            st.info("No patients yet.")
        else:
            p_idx = st.selectbox("Patient", list(range(len(pats))), format_func=lambda i: _patient_label(pats[i]))
            patient = pats[p_idx]

            pat_appts = [a for a in appts if a.get("patient_id") == patient.get("id")]
            if pat_appts:
                a_idx = st.selectbox("Appointment (optional)", [-1] + list(range(len(pat_appts))),
                                     format_func=lambda i: "— (none)" if i == -1 else _appt_label(pat_appts[i], db))
                appt = None if a_idx == -1 else pat_appts[a_idx]
            else:
                st.caption("No appointments found for this patient.")
                appt = None

            # Provider pool (Doctor or Psychological Counselor)
            prov_options = _provider_options(db)
            if appt and prov_options:
                prov_default = next((k for k,u in enumerate(prov_options) if u.get("id")==appt.get("doctor_id")), 0)
            else:
                prov_default = 0

            provider = prov_options[prov_default] if prov_options else None
            if prov_options:
                prov_idx = st.selectbox(
                    "Provider (Doctor / Psychological Counselor)",
                    list(range(len(prov_options))),
                    format_func=lambda i: _provider_label(prov_options[i]),
                    index=prov_default
                )
                provider = prov_options[prov_idx]
            else:
                st.warning("No providers available. Add a Doctor or a Psychological Counselor.")

            st.markdown("---")

            key_prefix = "inv_new"
            if f"{key_prefix}_rows" not in st.session_state:
                st.session_state[f"{key_prefix}_rows"] = 1
            n_rows = st.session_state[f"{key_prefix}_rows"]

            items: List[Dict[str, Any]] = []
            with st.container():
                for r in range(n_rows):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    desc = c1.text_input(f"Description {r+1}", key=f"{key_prefix}_desc_{r}")
                    qty = c2.number_input(f"Qty {r+1}", min_value=0.0, step=1.0, value=1.0, key=f"{key_prefix}_qty_{r}")
                    price = c3.number_input(f"Unit Price {r+1} (RM)", min_value=0.0, step=1.0, value=0.0, key=f"{key_prefix}_price_{r}")
                    if desc or qty or price:
                        items.append({"desc": desc, "qty": qty, "unit_price": price})

            c_add, c_sub = st.columns([1,1])
            with c_add:
                if st.button("Add line", key=f"{key_prefix}_add"):
                    st.session_state[f"{key_prefix}_rows"] += 1
                    st.rerun()
            with c_sub:
                if st.button("Remove last line", disabled=n_rows<=1, key=f"{key_prefix}_sub"):
                    st.session_state[f"{key_prefix}_rows"] = max(1, n_rows-1)
                    st.rerun()

            tax = st.number_input("Tax (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
            discount = st.number_input("Discount (RM)", min_value=0.0, value=0.0, step=1.0)
            calc = _totals_from_items(items, tax, discount)

            st.markdown(
                f"<div style='display:flex;gap:16px;flex-wrap:wrap'>"
                f"<div>Subtotal: <b>RM {calc['subtotal']:.2f}</b></div>"
                f"<div>Tax: <b>RM {calc['tax']:.2f}</b></div>"
                f"<div>Discount: <b>RM {calc['discount']:.2f}</b></div>"
                f"<div>Total: <b>RM {calc['total']:.2f}</b></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            notes = st.text_area("Notes (optional)", placeholder="Add internal notes or public memo…")

            if st.button("Create Invoice", type="primary", use_container_width=True, disabled=len(items)==0):
                db = load_db()
                invs = db.get("invoices", [])
                inv = {
                    "id": _next_invoice_id(db),
                    "code": _next_invoice_code(db),
                    "patient_id": patient.get("id"),
                    "doctor_id": (provider or {}).get("id"),   # store provider id here
                    "appt_id": (appt or {}).get("id"),
                    "items": items,
                    "tax_pct": float(tax),
                    "discount": float(discount),
                    **_totals_from_items(items, tax, discount),
                    "status": "unpaid",
                    "issued_at": _now_iso(),
                    "paid_at": "",
                    "notes": notes.strip() if notes else "",
                    "created_by": user.get("id"),
                }
                invs.append(inv)
                db["invoices"] = invs
                save_db(db)
                st.success(f"Invoice {inv.get('code')} created.")
                # reset line controls
                for r in range(st.session_state.get(f"{key_prefix}_rows", 1)):
                    for suf in ("desc","qty","price"):
                        st.session_state.pop(f"{key_prefix}_{suf}_{r}", None)
                st.session_state[f"{key_prefix}_rows"] = 1
                st.rerun()

    # ---------- Edit / Pay / Void ----------
    with st.expander("🧾 Edit / Mark Paid", expanded=False):
        if not filtered:
            st.info("No invoices in the current filter.")
        else:
            def _inv_label(i: int) -> str:
                inv = filtered[i]
                code = inv.get("code","(no code)")
                total = f"RM {float(inv.get('total',0.0)):.2f}"
                status = inv.get("status","unpaid").title()
                issued = _parse_iso(inv.get("issued_at","")).strftime("%b %d")
                return f"{code} • {total} • {status} • {issued}"

            idx = st.selectbox("Choose invoice", list(range(len(filtered))), format_func=_inv_label)
            inv = filtered[idx]
            st.markdown(
                f"**{inv.get('code','(no code)')}** • "
                f"{_status_pill(inv.get('status','unpaid'))} • "
                f"Issued {_parse_iso(inv.get('issued_at','')).strftime('%b %d, %Y %H:%M')}",
                unsafe_allow_html=True,
            )

            p = _patient_by_id(db, inv.get("patient_id"))
            d = _user_by_id(db, inv.get("doctor_id"))     # provider
            appt = _appt_by_id(db, inv.get("appt_id") or 0)
            st.caption(f"Patient: {p.get('name') if p else '—'}  |  Provider: {d.get('name') if d else '—'}  "
                       f"|  Appt: {appt.get('id') if appt else '—'}")

            editable = (inv.get("status") == "unpaid")
            items = inv.get("items", [])

            if editable:
                st.write("**Items**")
                new_items: List[Dict[str, Any]] = []
                for r, it in enumerate(items):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    desc = c1.text_input(f"Description {r+1}", value=str(it.get("desc","")), key=f"edit_desc_{inv['id']}_{r}")
                    qty = c2.number_input(f"Qty {r+1}", min_value=0.0, step=1.0, value=float(it.get("qty",1.0)), key=f"edit_qty_{inv['id']}_{r}")
                    price = c3.number_input(f"Unit Price {r+1} (RM)", min_value=0.0, step=1.0, value=float(it.get("unit_price",0.0)), key=f"edit_price_{inv['id']}_{r}")
                    new_items.append({"desc": desc, "qty": qty, "unit_price": price})

                c_add, c_sub = st.columns([1,1])
                with c_add:
                    if st.button("Add line", key=f"edit_add_{inv['id']}"):
                        new_items.append({"desc": "", "qty": 1.0, "unit_price": 0.0})
                        inv["items"] = new_items
                        save_db(db); st.rerun()
                with c_sub:
                    if st.button("Remove last line", key=f"edit_sub_{inv['id']}", disabled=len(new_items)<=1):
                        inv["items"] = new_items[:-1]
                        save_db(db); st.rerun()

                tax = st.number_input("Tax (%)", min_value=0.0, max_value=30.0, value=float(inv.get("tax_pct",0.0)))
                discount = st.number_input("Discount (RM)", min_value=0.0, value=float(inv.get("discount",0.0)))
                calc = _totals_from_items(new_items, tax, discount)
                inv.update(calc)
                inv["tax_pct"] = float(tax)
                inv["discount"] = float(discount)

                st.markdown(
                    f"Subtotal **RM {calc['subtotal']:.2f}** • Tax **RM {calc['tax']:.2f}** • "
                    f"Discount **RM {calc['discount']:.2f}** • Total **RM {calc['total']:.2f}**"
                )

                notes = st.text_area("Notes", value=str(inv.get("notes","")))
                inv["notes"] = notes

                if st.button("Save invoice", type="primary"):
                    for i, row in enumerate(db["invoices"]):
                        if row.get("id") == inv.get("id"):
                            db["invoices"][i] = inv
                            break
                    save_db(db)
                    st.success("Saved.")
                    st.rerun()
            else:
                st.write("**Items**")
                show_rows = []
                for it in items:
                    show_rows.append({
                        "Description": it.get("desc",""),
                        "Qty": it.get("qty",0),
                        "Unit (RM)": it.get("unit_price",0.0),
                        "Line (RM)": round(float(it.get("qty",0))*float(it.get("unit_price",0.0)),2)
                    })
                st.dataframe(pd.DataFrame(show_rows), hide_index=True, use_container_width=True)
                st.caption(f"Subtotal RM {inv.get('subtotal',0.0):.2f} • Tax RM {inv.get('tax',0.0):.2f} • "
                           f"Discount RM {inv.get('discount',0.0):.2f} • Total RM {inv.get('total',0.0):.2f}")

            a1, a2, a3 = st.columns(3)
            if inv.get("status") == "unpaid":
                with a1:
                    if st.button("Mark as Paid", type="primary", use_container_width=True):
                        inv["status"] = "paid"
                        inv["paid_at"] = _now_iso()
                        save_db(db)
                        st.success("Marked Paid.")
                        st.rerun()
                with a2:
                    if st.button("Void Invoice", use_container_width=True):
                        inv["status"] = "void"
                        save_db(db)
                        st.info("Invoice voided.")
                        st.rerun()
            elif inv.get("status") == "paid":
                with a1:
                    st.button("Paid", disabled=True, use_container_width=True)
                with a2:
                    if st.button("Void (revoke)", use_container_width=True):
                        inv["status"] = "void"
                        save_db(db); st.rerun()
            else:  # void
                with a1:
                    if st.button("Restore to Unpaid", use_container_width=True):
                        inv["status"] = "unpaid"
                        inv["paid_at"] = ""
                        save_db(db); st.rerun()
