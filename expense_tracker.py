import json, os, csv, sys
from datetime import datetime, date
from collections import defaultdict
from typing import Optional

_TTY = sys.stdout.isatty()
def _c(t, code): return f"\033[{code}m{t}\033[0m" if _TTY else t

RED    = lambda t: _c(t, "31")
GREEN  = lambda t: _c(t, "32")
YELLOW = lambda t: _c(t, "33")
CYAN   = lambda t: _c(t, "36")
BOLD   = lambda t: _c(t, "1")
DIM    = lambda t: _c(t, "2")

DATA_FILE   = "expenses.json"
BUDGET_FILE = "budgets.json"
EXPORT_FILE = "expenses_export.csv"

CATEGORIES = ["Food", "Transport", "Shopping",
              "Education", "Health", "Entertainment", "Other"]

CAT_ICON = {
    "Food": "🍽", "Transport": "🚌", "Shopping": "🛍",
    "Education": "📚", "Health": "💊", "Entertainment": "🎮", "Other": "📦",
}



def load_expenses() -> list:
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE) as f: return json.load(f)

def save_expenses(expenses: list) -> None:
    with open(DATA_FILE, "w") as f: json.dump(expenses, f, indent=2)

def load_budgets() -> dict:
    if not os.path.exists(BUDGET_FILE): return {}
    with open(BUDGET_FILE) as f: return json.load(f)

def save_budgets(budgets: dict) -> None:
    with open(BUDGET_FILE, "w") as f: json.dump(budgets, f, indent=2)



def add_expense(expenses, amount, description, category, note=""):
    """
    Accumulator pattern: each expense is one immutable record.
    list.append() ≡ SQL INSERT INTO expenses VALUES (...)
    """
    exp = {
        "id"         : len(expenses) + 1,
        "amount"     : round(float(amount), 2),
        "description": description.strip(),
        "category"   : category,
        "note"       : note.strip(),
        "date"       : date.today().isoformat(),
        "month"      : date.today().strftime("%Y-%m"),
        "time"       : datetime.now().strftime("%H:%M"),
    }
    expenses.append(exp)
    return exp

def get_total(expenses) -> float:
    """Accumulator: total = 0; total += e['amount'] for each e"""
    return round(sum(e["amount"] for e in expenses), 2)

def get_by_category(expenses) -> dict:
    result = defaultdict(float)
    for e in expenses:
        result[e["category"]] += e["amount"]
    return dict(result)

def get_by_month(expenses, month: str) -> list:
    """month format: YYYY-MM"""
    return [e for e in expenses if e.get("month") == month]

def get_today(expenses) -> list:
    today = date.today().isoformat()
    return [e for e in expenses if e["date"] == today]

def get_this_month(expenses) -> list:
    return get_by_month(expenses, date.today().strftime("%Y-%m"))

def check_budget_alerts(expenses, budgets) -> list:
    """Return list of (category, spent, budget, pct) where pct >= 80"""
    alerts = []
    month_data = get_by_category(get_this_month(expenses))
    for cat, budget in budgets.items():
        spent = month_data.get(cat, 0.0)
        pct   = (spent / budget * 100) if budget > 0 else 0
        if pct >= 80:
            alerts.append((cat, spent, budget, pct))
    return alerts

def export_csv(expenses) -> str:
    with open(EXPORT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id","date","category","amount","description","note"])
        writer.writeheader()
        writer.writerows(expenses)
    return EXPORT_FILE

# ──────────────────────────────────────────────
# VIEW LAYER
# ──────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════╗
║   💰  BudgetIQ  ·  DecodeLabs Internship 2026        ║
║      Gowri Chittem  ·  Smart Expense Tracker v2.0    ║
╚══════════════════════════════════════════════════════╝"""

MENU = """
  ┌─ EXPENSES ───────────────────────────────────────┐
  │  [1] Add expense        [6] Monthly summary      │
  │  [2] View all           [7] Set category budget  │
  │  [3] Today's expenses   [8] Budget tracker       │
  │  [4] Category report    [9] Export CSV           │
  │  [5] Financial summary  [0] Exit                 │
  └──────────────────────────────────────────────────┘"""


def _fmt(amount): return f"₹{amount:>10.2f}"

def display_expenses(expenses, title="Expenses"):
    print(f"\n  {BOLD('──')} {CYAN(title)} {BOLD('──')}")
    if not expenses:
        print(DIM("  (no expenses recorded)")); return
    print(f"  {'ID':>3}  {'Date':<12} {'':<2} {'Category':<14} {'Amount':>11}  Description")
    print("  " + "─" * 62)
    for e in expenses:
        icon = CAT_ICON.get(e["category"], "📦")
        print(f"  {e['id']:>3}  {e['date']:<12} {icon}  {e['category']:<14}"
              f"  {GREEN(_fmt(e['amount'])):<}  {e['description']}")
    print("  " + "─" * 62)
    total = get_total(expenses)
    print(f"  {'':>3}  {'':12}  {'TOTAL':<16}  {BOLD(_fmt(total))}")

def display_category_report(expenses):
    if not expenses:
        print(RED("\n  No data to report.")); return
    by_cat = get_by_category(expenses)
    total  = get_total(expenses)
    rows   = sorted(by_cat.items(), key=lambda x: -x[1])

    print(f"\n  {BOLD('── Category Breakdown ──')}")
    print(f"  {'Category':<16} {'Amount':>11}  {'Share':>7}  Spending Bar")
    print("  " + "─" * 60)
    for cat, amt in rows:
        pct  = (amt / total * 100) if total else 0
        bar  = CYAN("█") * int(pct / 4) + DIM("░") * (25 - int(pct / 4))
        icon = CAT_ICON.get(cat, "📦")
        print(f"  {icon} {cat:<14}  {GREEN(_fmt(amt))}  {pct:>6.1f}%  {bar}")
    print("  " + "─" * 60)
    print(f"  {'TOTAL':<16}  {BOLD(_fmt(total))}")

def display_summary(expenses):
    if not expenses:
        print(RED("\n  No data yet.")); return
    amounts     = [e["amount"] for e in expenses]
    total       = get_total(expenses)
    avg         = total / len(expenses)
    this_month  = get_total(get_this_month(expenses))
    today_total = get_total(get_today(expenses))

    # streak — consecutive days with at least 1 expense
    days = sorted({e["date"] for e in expenses}, reverse=True)
    streak = 0
    for i, d in enumerate(days):
        expected = (date.today() - __import__("datetime").timedelta(days=i)).isoformat()
        if d == expected: streak += 1
        else: break

    print(f"""
  ╔══════════════════════════════════════════╗
  ║  {BOLD('FINANCIAL SUMMARY')}                     ║
  ╠══════════════════════════════════════════╣
  ║  Total transactions : {len(expenses):<18}║
  ║  All-time total     : {GREEN(_fmt(total)):<18}║
  ║  This month         : {YELLOW(_fmt(this_month)):<18}║
  ║  Today              : {_fmt(today_total):<18}║
  ║  Average per entry  : {_fmt(avg):<18}║
  ║  Largest expense    : {RED(_fmt(max(amounts))):<18}║
  ║  Smallest expense   : {_fmt(min(amounts)):<18}║
  ║  Tracking streak    : {str(streak) + ' day(s)':<18}║
  ╚══════════════════════════════════════════╝""")

def display_budget_tracker(expenses, budgets):
    if not budgets:
        print(YELLOW("\n  No budgets set yet. Use option [7] to set budgets.")); return
    month_cat = get_by_category(get_this_month(expenses))
    month_str = date.today().strftime("%B %Y")

    print(f"\n  {BOLD('── Budget Tracker')} ({CYAN(month_str)}) {BOLD('──')}")
    print(f"  {'Category':<16} {'Budget':>11} {'Spent':>11} {'Left':>11}  Status")
    print("  " + "─" * 70)
    for cat in CATEGORIES:
        if cat not in budgets: continue
        budget = budgets[cat]
        spent  = round(month_cat.get(cat, 0.0), 2)
        left   = budget - spent
        pct    = (spent / budget * 100) if budget > 0 else 0
        bar_f  = min(int(pct / 5), 20)
        color  = RED if pct >= 100 else (YELLOW if pct >= 80 else GREEN)
        bar    = color("█") * bar_f + DIM("░") * (20 - bar_f)
        status = RED("OVER BUDGET!") if pct >= 100 else (YELLOW("⚠ Near limit") if pct >= 80 else GREEN("OK"))
        icon   = CAT_ICON.get(cat, "📦")
        print(f"  {icon} {cat:<14}  {_fmt(budget)}  {color(_fmt(spent))}  {_fmt(left)}  {bar}  {status}")
    print("  " + "─" * 70)

def display_monthly_summary(expenses):
    months = sorted({e.get("month", e["date"][:7]) for e in expenses}, reverse=True)
    if not months:
        print(DIM("  No data.")); return
    print(f"\n  {BOLD('── Monthly Spending History ──')}")
    max_amt = max(get_total(get_by_month(expenses, m)) for m in months)
    for m in months[:12]:
        month_exp = get_by_month(expenses, m)
        total     = get_total(month_exp)
        bar_len   = int((total / max_amt) * 30) if max_amt else 0
        bar       = CYAN("█") * bar_len
        print(f"  {m}  {bar:<30}  {GREEN(_fmt(total))}  ({len(month_exp)} entries)")


def _input_amount() -> float:
    while True:
        try:
            raw = input("  Amount (₹): ").strip()
            val = float(raw)
            if val <= 0: print(RED("  ✗ Amount must be positive.")); continue
            return val
        except ValueError:
            print(RED(f"  ✗ '{raw}' is not a valid number."))

def _pick_category() -> str:
    print("\n  Categories:")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"    [{i}] {CAT_ICON.get(cat,'📦')} {cat}")
    while True:
        try:
            idx = int(input("  Choose [1-7]: ").strip())
            if 1 <= idx <= len(CATEGORIES): return CATEGORIES[idx - 1]
            print(RED(f"  ✗ Enter 1–{len(CATEGORIES)}."))
        except ValueError:
            print(RED("  ✗ Enter a valid number."))


def main():
    print(CYAN(BANNER))
    expenses = load_expenses()
    budgets  = load_budgets()

    # Boot alerts
    alerts = check_budget_alerts(expenses, budgets)
    for cat, spent, budget, pct in alerts:
        msg = "OVER BUDGET" if pct >= 100 else f"{pct:.0f}% used"
        print(RED(f"  ⚠  {cat}: {msg}  (spent ₹{spent:.2f} of ₹{budget:.2f})"))

    total = get_total(expenses)
    print(GREEN(f"\n  ✓ Loaded {len(expenses)} expense(s). All-time total: ₹{total:.2f}"))

    while True:
        print(MENU)
        choice = input("\n  Enter choice: ").strip()

        if choice == "1":
            amount   = _input_amount()
            desc     = input("  Description: ").strip() or "Miscellaneous"
            category = _pick_category()
            note     = input("  Note (optional): ").strip()
            exp      = add_expense(expenses, amount, desc, category, note)
            save_expenses(expenses)
            running  = get_total(expenses)
            print(GREEN(f"\n  ✓ Added: ₹{exp['amount']:.2f} – {exp['description']}"))
            print(f"  ▶ Running total: ₹{running:.2f}")

            # live budget check
            month_cat = get_by_category(get_this_month(expenses))
            if category in budgets:
                spent  = month_cat.get(category, 0)
                budget = budgets[category]
                pct    = spent / budget * 100 if budget else 0
                if pct >= 100:
                    print(RED(f"  🚨 Budget EXCEEDED for {category}! ₹{spent:.2f} / ₹{budget:.2f}"))
                elif pct >= 80:
                    print(YELLOW(f"  ⚠  {pct:.0f}% of {category} budget used this month."))

        elif choice == "2":
            display_expenses(expenses)

        elif choice == "3":
            display_expenses(get_today(expenses), f"Today's Expenses ({date.today()})")

        elif choice == "4":
            display_category_report(expenses)

        elif choice == "5":
            display_summary(expenses)

        elif choice == "6":
            display_monthly_summary(expenses)

        elif choice == "7":
            print("\n  Set monthly budgets per category:")
            cat = _pick_category()
            try:
                budget = float(input(f"  Monthly budget for {cat} (₹): ").strip())
                if budget < 0: print(RED("  ✗ Budget cannot be negative.")); continue
                budgets[cat] = round(budget, 2)
                save_budgets(budgets)
                print(GREEN(f"  ✓ Budget set: {cat} = ₹{budget:.2f}/month"))
            except ValueError:
                print(RED("  ✗ Enter a valid number."))

        elif choice == "8":
            display_budget_tracker(expenses, budgets)

        elif choice == "9":
            path = export_csv(expenses)
            print(GREEN(f"  ✓ Exported {len(expenses)} records to {path}"))

        elif choice == "0":
            save_expenses(expenses)
            print(GREEN(f"\n  Final total: ₹{get_total(expenses):.2f}  – Data saved. Goodbye! 💰\n"))
            break

        else:
            print(RED("  ✗ Invalid option."))

if __name__ == "__main__":
    main()
