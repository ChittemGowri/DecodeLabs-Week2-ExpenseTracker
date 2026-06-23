"""
BudgetIQ AI — DecodeLabs Internship 2026
Chittem Gowri Shankar | Viswam Engineering College, JNTUA
"""
import streamlit as st
import plotly.graph_objects as go
import json
import os
import csv
import io
import requests
from datetime import datetime, date
from collections import defaultdict

# --- Setup & Configuration ---
st.set_page_config(page_title="BudgetIQ AI", page_icon="💰", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPENSE_FILE = os.path.join(BASE_DIR, "expenses.json")
BUDGET_FILE = os.path.join(BASE_DIR, "budgets.json")

CATEGORIES = ["Food", "Transport", "Shopping", "Education", "Health", "Entertainment", "Other"]
CAT_ICON = {
    "Food": "🍽️", "Transport": "🚌", "Shopping": "🛍️", 
    "Education": "📚", "Health": "💊", "Entertainment": "🎮", "Other": "📦"
}

# --- Data Handling Functions ---
def load_exp():
    if not os.path.exists(EXPENSE_FILE):
        return []
    try:
        with open(EXPENSE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_exp(data):
    with open(EXPENSE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_bud():
    if not os.path.exists(BUDGET_FILE):
        return {}
    try:
        with open(BUDGET_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_bud(data):
    with open(BUDGET_FILE, "w") as f:
        json.dump(data, f, indent=2)

def this_month(expenses):
    current_month = date.today().strftime("%Y-%m")
    return [e for e in expenses if e.get("month") == current_month]

def by_cat(expenses):
    result = defaultdict(float)
    for e in expenses:
        result[e["category"]] += e["amount"]
    return dict(result)

def get_total(expenses):
    return round(sum(e["amount"] for e in expenses), 2)

# --- AI Integration ---
def nvidia_ai_call(api_key, prompt, system_prompt="You are a helpful assistant.", max_tokens=400):
    try:
        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "meta/llama-3.1-8b-instruct",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": max_tokens
            },
            timeout=25
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.Timeout:
        return "⚠️ Request timed out. Please try again."
    except Exception as e:
        return f"⚠️ API error: {e}"

# --- State Management ---
if "expenses" not in st.session_state:
    st.session_state.expenses = load_exp()
if "budgets" not in st.session_state:
    st.session_state.budgets = load_bud()

expenses = st.session_state.expenses
budgets = st.session_state.budgets

month_exp = this_month(expenses)
month_cat = by_cat(month_exp)

# Calculate alerts
alerts = []
for cat, budget in budgets.items():
    spent = month_cat.get(cat, 0)
    pct = (spent / budget * 100) if budget else 0
    if pct >= 80:
        alerts.append((cat, spent, budget, pct))

# --- UI Header ---
st.title("💰 BudgetIQ AI")
st.caption("DecodeLabs Internship 2026 · Chittem Gowri Shankar · Powered by NVIDIA NIM")
st.divider()

# --- Display Alerts ---
for cat, spent, budget, pct in alerts:
    if pct >= 100:
        st.error(f"{CAT_ICON.get(cat, '')} **{cat}**: 🚨 OVER BUDGET — ₹{spent:.0f} / ₹{budget:.0f}")
    else:
        st.warning(f"{CAT_ICON.get(cat, '')} **{cat}**: ⚠️ {pct:.0f}% used — ₹{spent:.0f} / ₹{budget:.0f}")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings & Overview")
    api_key = st.text_input("🔑 NVIDIA API Key", type="password", placeholder="nvapi-...")
    st.caption("[Get your key here](https://build.nvidia.com)")
    
    st.divider()
    
    m_total = get_total(month_exp)
    t_total = get_total(expenses)
    today_t = get_total([e for e in expenses if e.get("date") == date.today().isoformat()])
    
    col1, col2 = st.columns(2)
    col1.metric("This Month", f"₹{m_total:.0f}")
    col2.metric("Today", f"₹{today_t:.0f}")
    
    col3, col4 = st.columns(2)
    col3.metric("All-Time", f"₹{t_total:.0f}")
    col4.metric("Total Entries", len(expenses))
    
    if budgets:
        total_budget = sum(budgets.values())
        st.divider()
        if total_budget:
            budget_ratio = min(m_total / total_budget, 1.0)
            st.write(f"**Total Budget Used: {m_total / total_budget:.0%}**")
            st.progress(budget_ratio)

# --- Main Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Add Expense", "📋 Expense List", "🎯 Budgets", "🤖 AI Advisor", "📊 Charts"])

# --- TAB 1: Add Expense ---
with tab1:
    st.subheader("Log a New Expense")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        amount = c1.number_input("Amount (₹)", min_value=0.01, step=1.0, format="%.2f")
        desc = c1.text_input("Description")
        
        cat = c2.selectbox("Category", CATEGORIES, format_func=lambda x: f"{CAT_ICON[x]} {x}")
        note = c2.text_input("Note (optional)")
        
        b1, b2 = st.columns(2)
        if b1.button("➕ Add Expense", type="primary", use_container_width=True):
            if amount <= 0:
                st.error("Amount must be positive.")
            elif not desc.strip():
                st.error("Description is required.")
            else:
                new_exp = {
                    "id": len(expenses) + 1,
                    "amount": round(float(amount), 2),
                    "description": desc.strip(),
                    "category": cat,
                    "note": note.strip(),
                    "date": date.today().isoformat(),
                    "month": date.today().strftime("%Y-%m"),
                    "time": datetime.now().strftime("%H:%M")
                }
                expenses.append(new_exp)
                save_exp(expenses)
                
                # Check budget status for standard success or warning message
                if cat in budgets:
                    new_mc = by_cat(this_month(expenses))
                    spent_now = new_mc.get(cat, 0)
                    bu = budgets[cat]
                    p = (spent_now / bu * 100) if bu else 0
                    
                    if p >= 100:
                        st.error(f"🚨 OVER BUDGET {cat}: ₹{spent_now:.0f} / ₹{bu:.0f}")
                    elif p >= 80:
                        st.warning(f"⚠️ {p:.0f}% of {cat} budget used")
                    else:
                        st.success(f"✅ Added ₹{new_exp['amount']:.2f} to {cat}")
                else:
                    st.success(f"✅ Added ₹{new_exp['amount']:.2f} to {cat}")
                st.rerun()
                
        if b2.button("🤖 Auto-Categorize", use_container_width=True):
            if not api_key:
                st.warning("Enter your NVIDIA API Key in the sidebar.")
            elif not desc.strip():
                st.warning("Enter a description first.")
            else:
                with st.spinner("Categorizing..."):
                    prompt = f"Categorize the expense '{desc}' into ONE of the following categories: {', '.join(CATEGORIES)}. Reply ONLY with the exact category name."
                    system = "You are an AI expense categorizer. Reply with only the category name, nothing else."
                    result = nvidia_ai_call(api_key, prompt, system)
                    suggested = next((c for c in CATEGORIES if c.lower() in result.lower()), "Other")
                    st.success(f"🤖 Suggested Category: {CAT_ICON.get(suggested, '')} **{suggested}**")

# --- TAB 2: Expense List ---
with tab2:
    st.subheader("Expense List")
    if not expenses:
        st.info("No expenses logged yet.")
    else:
        c1, c2 = st.columns(2)
        fc = c1.selectbox("Filter by Category", ["All"] + CATEGORIES)
        fm = c2.selectbox("Filter by Month", ["All"] + sorted({e.get("month", "") for e in expenses}, reverse=True))
        
        filtered_exp = [e for e in expenses if (fc == "All" or e["category"] == fc) and (fm == "All" or e.get("month") == fm)]
        filtered_exp = sorted(filtered_exp, key=lambda e: e["date"], reverse=True)
        
        st.write(f"**Showing {len(filtered_exp)} entries · Total: ₹{get_total(filtered_exp):.2f}**")
        
        for e in filtered_exp:
            with st.container(border=True):
                col_info, col_amt = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**{CAT_ICON.get(e['category'], '📦')} {e['description']}**")
                    st.caption(f"{e['category']} · {e['date']} {e.get('time', '')} {('· ' + e['note']) if e.get('note') else ''}")
                with col_amt:
                    st.markdown(f"### ₹{e['amount']:.2f}")

        # CSV Export
        buf = io.StringIO()
        csv_writer = csv.DictWriter(buf, fieldnames=["id", "date", "category", "amount", "description", "note"])
        csv_writer.writeheader()
        csv_writer.writerows(filtered_exp)
        st.download_button("⬇️ Export to CSV", buf.getvalue(), "expenses.csv", "text/csv")

# --- TAB 3: Budgets ---
with tab3:
    st.subheader("Monthly Budget Tracker")
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        with st.container(border=True):
            st.write("**Set Budget limit**")
            bc = st.selectbox("Category", CATEGORIES, format_func=lambda x: f"{CAT_ICON[x]} {x}", key="bc")
            ba = st.number_input("Monthly budget (₹)", min_value=0.0, step=100.0, format="%.2f")
            
            if st.button("💾 Save Budget", type="primary", use_container_width=True):
                budgets[bc] = round(float(ba), 2)
                save_bud(budgets)
                st.success(f"✅ Budget for {bc} set to ₹{ba:.2f}/month")
                st.rerun()
                
    with c2:
        if not budgets:
            st.info("Set your first budget on the left to start tracking.")
        else:
            for cat in CATEGORIES:
                if cat not in budgets:
                    continue
                b = budgets[cat]
                sp = round(month_cat.get(cat, 0), 2)
                pct = min(sp / b * 100 if b else 0, 100)
                
                status_text = "🚨 OVER BUDGET" if pct >= 100 else ("⚠️ Near limit" if pct >= 80 else "✅ On track")
                
                with st.container(border=True):
                    st.markdown(f"**{CAT_ICON.get(cat, '')} {cat}**")
                    st.write(f"₹{sp:.0f} / ₹{b:.0f} ({status_text})")
                    st.progress(pct / 100)
                    st.caption(f"{pct:.0f}% used · ₹{max(b - sp, 0):.0f} remaining")

# --- TAB 4: AI Advisor ---
with tab4:
    st.subheader("🤖 NVIDIA AI Financial Advisor")
    
    if not api_key:
        st.warning("Please enter your NVIDIA API Key in the sidebar.")
    else:
        c1, c2 = st.columns(2)
        
        if c1.button("📊 Analyze My Spending", type="primary", use_container_width=True):
            if not expenses:
                st.info("Log some expenses first to get an analysis.")
            else:
                bk = ", ".join(f"{k}: ₹{v:.0f}" for k, v in by_cat(month_exp).items())
                bu = ", ".join(f"{k}: ₹{v:.0f}" for k, v in budgets.items()) if budgets else "not set"
                
                with st.spinner("Analyzing your finances..."):
                    prompt = f"Spending this month: {bk}. Budgets: {bu}. Provide: 1) Top area of concern 2) One practical saving tip 3) Month-end prediction. Keep it under 110 words."
                    system = "You are a pragmatic personal finance advisor for Indian college students. Use ₹ formatting. Be direct and helpful."
                    response = nvidia_ai_call(api_key, prompt, system)
                    st.info(response)
                    
        if c2.button("💡 Generate Saving Tips", use_container_width=True):
            if not expenses:
                st.info("Log some expenses first to get customized tips.")
            else:
                top_cats = sorted(by_cat(month_exp).items(), key=lambda x: -x[1])[:3]
                cats_str = ", ".join(f"{k} (₹{v:.0f})" for k, v in top_cats)
                
                with st.spinner("Generating tips..."):
                    prompt = f"My top spending categories are: {cats_str}. Give me 3 highly specific, actionable saving tips suitable for an Indian college student. Keep it under 90 words."
                    system = "You are a frugal finance coach. Use ₹ formatting. Be extremely practical and specific."
                    response = nvidia_ai_call(api_key, prompt, system)
                    st.success(response)
                    
        st.divider()
        st.write("**Ask your Financial Advisor a custom question:**")
        user_query = st.text_input("E.g., 'How can I reduce my food expenses without starving?'")
        
        if st.button("Ask Advisor") and user_query:
            context = f"Monthly spending overview: {dict(by_cat(month_exp))}. Current budgets: {budgets}. User Question: {user_query}"
            with st.spinner("Thinking..."):
                system = "You are a personal finance advisor for Indian students. Use ₹ formatting. Keep answers strictly under 120 words."
                response = nvidia_ai_call(api_key, context, system)
                st.chat_message("assistant").write(response)

# --- TAB 5: Charts ---
with tab5:
    st.subheader("📊 Financial Charts")
    
    if not expenses:
        st.info("Add expenses to visualize your spending trends.")
    else:
        c1, c2 = st.columns(2)
        
        with c1:
            bcd = by_cat(expenses)
            fig_pie = go.Figure(go.Pie(
                labels=[f"{CAT_ICON.get(k, '')} {k}" for k in bcd],
                values=list(bcd.values()),
                hole=0.4,
                marker_colors=["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#ef4444", "#06b6d4", "#6b7280"]
            ))
            fig_pie.update_layout(
                title="Spending by Category",
                height=350,
                margin=dict(t=40, b=20, l=0, r=0)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            monthly_data = defaultdict(float)
            for e in expenses:
                monthly_data[e.get("month", "")] += e["amount"]
                
            months_sorted = sorted(monthly_data.keys())
            fig_bar = go.Figure(go.Bar(
                x=months_sorted,
                y=[monthly_data[m] for m in months_sorted],
                marker_color="#10b981"
            ))
            fig_bar.update_layout(
                title="Monthly Spending Trend",
                height=350,
                margin=dict(t=40, b=20, l=0, r=0)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
