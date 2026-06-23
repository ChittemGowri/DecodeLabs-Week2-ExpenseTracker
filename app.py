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
st.title("
