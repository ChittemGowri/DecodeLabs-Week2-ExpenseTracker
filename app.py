"""
BudgetIQ AI — DecodeLabs Internship 2026
Gowri Shankar | Viswam Engineering College, JNTUA
"""
import streamlit as st
import plotly.graph_objects as go
import json, os, csv, io, requests
from datetime import datetime, date
from collections import defaultdict

st.set_page_config(page_title="BudgetIQ AI", page_icon="💰", layout="wide")

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
EXPENSE_FILE = os.path.join(BASE_DIR, "expenses.json")
BUDGET_FILE  = os.path.join(BASE_DIR, "budgets.json")

# --- UPDATED LIGHT & PLEASANT CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background: #f8fafc;
    color: #1e293b;
}
.hdr {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.2rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}
.hdr::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #10b981, #34d399, #3b82f6);
}
.hdr h1 {
    font-size: 1.8rem;
    font-weight: 700;
    color: #064e3b;
    margin: 0;
}
.hdr p {
    color: #64748b;
    margin: 0.3rem 0 0;
    font-size: 0.9rem;
    font-weight: 600;
}
.card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}
.ai-box {
    background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
    border: 1px solid #a7f3d0;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-top: 0.8rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.ai-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #059669;
    margin-bottom: 0.5rem;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

CATEGORIES = ["Food","Transport","Shopping","Education","Health","Entertainment","Other"]
CAT_ICON   = {"Food":"🍽️","Transport":"🚌","Shopping":"🛍️","Education":"📚",
               "Health":"💊","Entertainment":"🎮","Other":"📦"}

def load_exp():
    if not os.path.exists(EXPENSE_FILE): return []
    try:
        with open(EXPENSE_FILE) as f: return json.load(f)
    except Exception: return []

def save_exp(d):
    with open(EXPENSE_FILE,"w") as f: json.dump(d, f, indent=2)

def load_bud():
    if not os.path.exists(BUDGET_FILE): return {}
    try:
        with open(BUDGET_FILE) as f: return json.load(f)
    except Exception: return {}

def save_bud(d):
    with open(BUDGET_FILE,"w") as f: json.dump(d, f, indent=2)

def this_month(expenses):
    m = date.today().strftime("%Y-%m")
    return [e for e in expenses if e.get("month")==m]

def by_cat(expenses):
    r = defaultdict(float)
    for e in expenses: r[e["category"]] += e["amount"]
    return dict(r)

def total(expenses): return round(sum(e["amount"] for e in expenses), 2)

def nvidia(api_key, prompt, system="You are a helpful assistant.", max_tokens=400):
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
            json={"model":"meta/llama-3.1-8b-instruct",
                  "messages":[{"role":"system","content":system},{"role":"user","content":prompt}],
                  "temperature":0.5,"max_tokens":max_tokens},
            timeout=25)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.Timeout: return "⚠️ Timeout. Try again."
    except Exception as e: return f"⚠️ API error: {e}"

if "expenses" not in st.session_state: st.session_state.expenses = load_exp()
if "budgets"  not in st.session_state: st.session_state.budgets  = load_bud()
expenses = st.session_state.expenses
budgets  = st.session_state.budgets

month_exp = this_month(expenses)
month_cat = by_cat(month_exp)
alerts = [(c,month_cat.get(c,0),b,month_cat.get(c,0)/b*100 if b else 0)
          for c,b in budgets.items() if (month_cat.get(c,0)/b*100 if b else 0) >= 80]

st.markdown("""
<div class="hdr">
  <h1>💰 BudgetIQ AI</h1>
  <p>DecodeLabs Internship 2026 · Gowri Shankar · NVIDIA NIM</p>
</div>""", unsafe_allow_html=True)

for cat, spent, budget, pct in alerts:
    status = "🚨 OVER BUDGET" if pct>=100 else f"⚠️ {pct:.0f}% used"
    st.error(f"{CAT_ICON.get(cat,'')} **{cat}**: {status} — ₹{spent:.0f} / ₹{budget:.0f}")

with st.sidebar:
    api_key = st.text_input("🔑 NVIDIA API Key", type="password", placeholder="nvapi-...")
    st.caption("[Get key →](https://build.nvidia.com)")
    st.divider()
    m_total = total(month_exp); t_total = total(expenses)
    today_t = total([e for e in expenses if e.get("date")==date.today().isoformat()])
    st.metric("This Month", f"₹{m_total:.0f}")
    st.metric("Today",      f"₹{today_t:.0f}")
    st.metric("All-Time",   f"₹{t_total:.0f}")
    st.metric("Entries",    len(expenses))
    if budgets:
        tb = sum(budgets.values())
        st.divider()
        if tb: st.progress(min(m_total/tb,1.0), text=f"Budget used: {min(m_total/tb,1.0):.0%}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Add","📋 List","🎯 Budget","🤖 AI","📊 Charts"])

with tab1:
    st.subheader("Log Expense")
    c1, c2 = st.columns(2)
    amount  = c1.number_input("Amount (₹)", min_value=0.01, step=1.0, format="%.2f")
    desc    = c1.text_input("Description")
    cat     = c2.selectbox("Category", CATEGORIES, format_func=lambda x:f"{CAT_ICON[x]} {x}")
    note    = c2.text_input("Note (optional)")
    b1, b2  = st.columns(2)
    if b1.button("➕ Add", type="primary", use_container_width=True):
        if amount<=0: st.error("Amount must be positive.")
        elif not desc.strip(): st.error("Description required.")
        else:
            exp = {"id":len(expenses)+1,"amount":round(float(amount),2),"description":desc.strip(),
                   "category":cat,"note":note.strip(),"date":date.today().isoformat(),
                   "month":date.today().strftime("%Y-%m"),"time":datetime.now().strftime("%H:%M")}
            expenses.append(exp); save_exp(expenses)
            if cat in budgets:
                new_mc = by_cat(this_month(expenses)); sp=new_mc.get(cat,0); bu=budgets[cat]; p=sp/bu*100 if bu else 0
                if p>=100: st.error(f"🚨 OVER BUDGET {cat}: ₹{sp:.0f}/₹{bu:.0f}")
                elif p>=80: st.warning(f"⚠️ {p:.0f}% of {cat} budget used")
                else: st.success(f"✅ Added ₹{exp['amount']:.2f}")
            else: st.success(f"✅ Added ₹{exp['amount']:.2f}")
            st.rerun()
    if api_key and b2.button("🤖 Auto-Categorize", use_container_width=True):
        if not desc.strip(): st.warning("Enter description
