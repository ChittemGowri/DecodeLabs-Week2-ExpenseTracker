# BudgetIQ – Smart Expense Tracker

#DecodeLabs Industrial Training
**intern**  :- Chittem Gowri Sankar 
**college** :- Viswam Engineering College | CST 2024–28

---

# 🚀 What Makes This Different

BudgetIQ is a **personal finance management system** built entirely with Python's standard library:

- **Monthly Budget Tracking** — Set per-category budgets with real-time overspend alerts
- **Live Budget Warnings** — Fires instantly after each entry if 80%+ of a category budget is used
- **ASCII Spending Charts** — Visual bar charts per category, no external libraries
- **Monthly Trend History** — Visual monthly breakdown with horizontal bar chart
- **CSV Export** — Export full history to spreadsheet-compatible format
- **Tracking Streak** — Counts consecutive days with at least one expense logged
- **7 Categories with Icons** — Food 🍽, Transport 🚌, Shopping 🛍, Education 📚, Health 💊, Entertainment 🎮
- **Boot-time Alerts** — Warns on startup if any budget is at risk this month

---

## 📐 Architecture

```
┌────────────────────────────────────────────────────┐
│                  BudgetIQ v2.0                     │
├───────────────┬────────────────┬───────────────────┤
│  DATA LAYER   │  BUSINESS      │  VIEW             │
│  ──────────── │  ────────────  │  ──────────────── │
│  expenses.json│  add_expense() │  display_expenses │
│  budgets.json │  get_total()   │  category_report  │
│  CSV export   │  get_by_cat()  │  budget_tracker   │
│               │  check alerts  │  monthly_summary  │
└───────────────┴────────────────┴───────────────────┘
```

---

# Setup & Run


# Pure Python 3.10+ — no pip installs needed
python expense_tracker.py


---

# Key Python Concepts Used

| Concept                   | Where Used              |
| ------------------------- | ----------------------- |
| `defaultdict(float)`      | Category aggregation    |
| `sum()` generator         | Running total           |
| `csv.DictWriter`          | CSV export              |
| `date.today().strftime()` | Month filtering         |
| f-string `{val:>10.2f}`   | Currency formatting     |
| Sentinel loop             | `while True` + `break`  |
| Poka-Yoke                 | `try/except ValueError` |


---



#Files

```
project2_expense_tracker/
├── expense_tracker.py    ← Main application
├── test_expense.py       ← Unit tests
├── expenses.json         ← Auto-created on first run
├── budgets.json          ← Budget configuration
├── expenses_export.csv   ← Generated on export
└── README.md             ← This file
```
