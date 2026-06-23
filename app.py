import streamlit as st
import plotly.graph_objects as go
import json, os, csv, io, requests
from datetime import datetime, date
from collections import defaultdict

st.set_page_config(page_title="BudgetIQ AI", page_icon="💰", layout="wide")

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
EXPENSE_FILE = os.path.join(BASE_DIR, "expenses.json")
BUDGET_FILE  = os.path.join(BASE_DIR, "budgets.json")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}

/* Clean Light Background */
.stApp{background:#f8fafc;color:#0f172a;}

/* Vibrant Modern Header */
.hdr{background:linear-gradient(135deg, #0ea5e9, #10b981); border:none; box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);
     border-radius:14px;padding:1.5rem 2rem;margin-bottom:1.2rem;position:relative;overflow:hidden;}
.hdr h1{font-size:1.8rem;font-weight:700;color:#ffffff;margin:0;}
.hdr p{color:#e0f2fe;margin:0.2rem 0 0;font-size:.85rem;font-weight:500;}

/* Neumorphic White Cards */
.card{background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:1rem 1.25rem;margin-bottom:.75rem;box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);}

/* Soft Pastel AI Box */
.ai-box{background:linear-gradient(135deg,#f0fdfa,#ccfbf1);border:1px solid #99f6e4;
         border-radius:10px;padding:1rem 1.25rem;margin-top:.8rem;box-shadow: 0 2px 4px rgba(0,0,0,0.02);}
.ai-label{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;
           color:#0f766e;margin-bottom:.4rem;font-weight:700;}

/* Light Mode Inputs */
.stTextInput>div>div>input,.stNumberInput>div>div>input{
  background:#ffffff!important;border:1px solid #cbd5e1!important;
  color:#0f172a!important;border-radius:7px!important;}
.stSelectbox>div>div{background:#ffffff!important;border:1px solid #cbd5e1!important;
  color:#0f172a!important;border-radius:7px!important;}
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
  <p>DecodeLabs Internship 2026 · Chittem Gowri Sankar · NVIDIA NIM</p>
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
        if not desc.strip(): st.warning("Enter description first.")
        else:
            with st.spinner():
                r = nvidia(api_key, f"Categorize '{desc}' into ONE of: {','.join(CATEGORIES)}. Reply ONLY the category name.",
                           "You are an expense categorizer. Reply with only the category name.")
            suggested = next((c for c in CATEGORIES if c.lower() in r.lower()), "Other")
            st.success(f"🤖 Suggested: {CAT_ICON.get(suggested,'')} **{suggested}**")

with tab2:
    st.subheader("Expense List")
    if not expenses: st.info("No expenses yet.")
    else:
        c1,c2 = st.columns(2)
        fc = c1.selectbox("Category filter", ["All"]+CATEGORIES)
        fm = c2.selectbox("Month filter", ["All"]+sorted({e.get("month","") for e in expenses},reverse=True))
        show = [e for e in expenses if (fc=="All" or e["category"]==fc) and (fm=="All" or e.get("month")==fm)]
        show = sorted(show, key=lambda e:e["date"], reverse=True)
        st.markdown(f"**{len(show)} entries · Total: ₹{total(show):.2f}**")
        for e in show:
            st.markdown(f"""
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span>{CAT_ICON.get(e['category'],'📦')} <strong style="color:#1e293b">{e['description']}</strong>
                  <span style="color:#64748b;font-size:.8rem"> · {e['category']}</span></span>
                <span style="color:#ef4444;font-weight:700;font-family:'JetBrains Mono',monospace">
                  ₹{e['amount']:.2f}</span>
              </div>
              <div style="font-size:.72rem;color:#64748b;margin-top:3px">{e['date']} {e.get('time','')}
                {' · '+e['note'] if e.get('note') else ''}</div>
            </div>""", unsafe_allow_html=True)
        buf = io.StringIO()
        csv.DictWriter(buf, fieldnames=["id","date","category","amount","description","note"]).writeheader()
        csv.DictWriter(buf, fieldnames=["id","date","category","amount","description","note"]).writerows(show)
        st.download_button("⬇️ Export CSV", buf.getvalue(), "expenses.csv", "text/csv")

with tab3:
    st.subheader("Monthly Budget Tracker")
    c1,c2 = st.columns(2)
    with c1:
        bc = st.selectbox("Category", CATEGORIES, format_func=lambda x:f"{CAT_ICON[x]} {x}", key="bc")
        ba = st.number_input("Monthly budget (₹)", min_value=0.0, step=100.0, format="%.2f")
        if st.button("💾 Save", type="primary"):
            budgets[bc]=round(float(ba),2); save_bud(budgets)
            st.success(f"✅ {bc} = ₹{ba:.2f}/month"); st.rerun()
    with c2:
        if not budgets: st.info("Set budgets on the left.")
        else:
            for cat in CATEGORIES:
                if cat not in budgets: continue
                b=budgets[cat]; sp=round(month_cat.get(cat,0),2)
                pct=min(sp/b*100 if b else 0,100)
                color="#10b981" if pct<80 else ("#f59e0b" if pct<100 else "#ef4444")
                status="🚨 OVER" if pct>=100 else ("⚠️ Near" if pct>=80 else "✅ OK")
                st.markdown(f"""
                <div class="card" style="margin-bottom:.4rem">
                  <div style="display:flex;justify-content:space-between">
                    <strong>{CAT_ICON.get(cat,'')} {cat}</strong>
                    <span style="color:{color};font-size:.8rem;font-weight:600">{status} · ₹{sp:.0f}/₹{b:.0f}</span>
                  </div>
                  <div style="background:#e2e8f0;border-radius:4px;height:6px;margin:5px 0;overflow:hidden">
                    <div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:4px"></div>
                  </div>
                  <div style="font-size:.72rem;color:#64748b;font-weight:600">{pct:.0f}% · ₹{max(b-sp,0):.0f} left</div>
                </div>""", unsafe_allow_html=True)

with tab4:
    st.subheader("🤖 NVIDIA AI Financial Advisor")
    if not api_key: st.warning("Enter NVIDIA API key in sidebar.")
    else:
        c1,c2 = st.columns(2)
        if c1.button("📊 Analyze Spending", type="primary", use_container_width=True):
            if not expenses: st.info("Add expenses first.")
            else:
                bk = ", ".join(f"{k}:₹{v:.0f}" for k,v in by_cat(month_exp).items())
                bu = ", ".join(f"{k}:₹{v:.0f}" for k,v in budgets.items()) if budgets else "not set"
                with st.spinner():
                    r = nvidia(api_key,f"Spending this month: {bk}. Budgets: {bu}. 1)Top concern 2)Saving tip 3)Month-end prediction. Under 110 words.",
                               "You are a personal finance advisor for Indian students. Use ₹. Be direct.")
                st.markdown(f'<div class="ai-box"><div class="ai-label">🤖 Spending Analysis</div>'
                            f'<div style="color:#1e293b;white-space:pre-wrap">{r}</div></div>',unsafe_allow_html=True)
        if c2.button("💡 Saving Tips", use_container_width=True):
            if not expenses: st.info("Add expenses first.")
            else:
                top = sorted(by_cat(month_exp).items(),key=lambda x:-x[1])[:3]
                cats = ", ".join(f"{k}(₹{v:.0f})" for k,v in top)
                with st.spinner():
                    r = nvidia(api_key,f"Top spending: {cats}. Give 3 specific saving tips for Indian college student. Under 90 words.",
                               "You are a frugal finance coach. Use ₹. Be specific.")
                st.markdown(f'<div class="ai-box"><div class="ai-label">🤖 Saving Tips</div>'
                            f'<div style="color:#1e293b;white-space:pre-wrap">{r}</div></div>',unsafe_allow_html=True)
        st.divider()
        uq = st.text_input("Ask your finance advisor")
        if st.button("Ask →") and uq:
            ctx = f"Monthly spending: {by_cat(month_exp)}. Budgets: {budgets}. Q: {uq}"
            with st.spinner():
                r = nvidia(api_key,ctx,"Personal finance advisor for Indian students. Use ₹. Under 120 words.")
            st.markdown(f'<div class="ai-box"><div class="ai-label">🤖 Answer</div>'
                        f'<div style="color:#1e293b;white-space:pre-wrap">{r}</div></div>',unsafe_allow_html=True)

with tab5:
    if not expenses: st.info("Add expenses to see charts.")
    else:
        c1,c2 = st.columns(2)
        with c1:
            bcd = by_cat(expenses)
            fig = go.Figure(go.Pie(labels=[f"{CAT_ICON.get(k,'')} {k}" for k in bcd],
                                   values=list(bcd.values()),hole=0.5,
                                   marker_colors=["#10b981","#3b82f6","#f59e0b","#8b5cf6","#ef4444","#06b6d4","#6b7280"]))
            fig.update_layout(title="By Category",paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",font_color="#475569",
                              height=280,margin=dict(t=40,b=0,l=0,r=0))
            st.plotly_chart(fig,use_container_width=True)
        with c2:
            monthly = defaultdict(float)
            for e in expenses: monthly[e.get("month","")] += e["amount"]
            months = sorted(monthly.keys())
            fig2 = go.Figure(go.Bar(x=months,y=[monthly[m] for m in months],marker_color="#10b981"))
            fig2.update_layout(title="Monthly Trend",paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)",font_color="#475569",
                               height=280,margin=dict(t=40,b=0,l=0,r=0))
            st.plotly_chart(fig2,use_container_width=True)
