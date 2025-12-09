"""
Egg Price Extrapolation Tool (Weeks + fractional day)
- X = week_number + fraction (Monday=0 ... Sunday/6 -> fraction = day_index/7)
- Base (Week 1 start) = 2023-08-21 (Monday)
- Loads Weeks 1..67 (the data you gave). Placeholder slots exist for Weeks 68..117.
- User may pick 2..117 points. Program will select the N points closest to the target date.
- ALWAYS computes both Newton and Lagrange for comparison.
"""

from datetime import date, datetime, timedelta
import math
import bisect
import csv
import sys

# ---------------------------
# Configuration / Constants
# ---------------------------
BASE_WEEK1_MONDAY = date(2023, 8, 21)
MAX_WEEKS = 117
CURRENT_WEEKS_AVAILABLE = 67

# ---------------------------
# Load provided weekly price data (Weeks 1..67)
# ---------------------------
weekly_prices = [
    7.29, 7.23, 7.25, 7.34, 7.56, 7.64, 7.73, 7.87, 7.88, 7.96,
    8.02, 8.10, 8.14, 8.18, 8.19, 8.20, 8.17, 8.14, 8.13, 8.08,
    8.07, 7.95, 7.95, 7.80, 7.71, 7.46, 7.38, 7.37, 7.37, 7.34,
    7.33, 7.31, 7.26, 7.08, 7.04, 7.11, 7.00, 7.00, 6.91, 6.93,
    7.02, 7.12, 7.16, 7.29, 7.47, 7.55, 7.71, 7.80, 7.88, 7.93,
    8.00, 8.04, 8.07, 8.12, 8.17, 8.27, 8.29, 8.38, 8.43, 8.49,
    8.46, 8.46, 8.45, 8.47, 8.43, 8.45, 8.40
]

# Fill missing future weeks with None
if len(weekly_prices) < MAX_WEEKS:
    weekly_prices += [None] * (MAX_WEEKS - len(weekly_prices))

# ---------------------------
# Convert date → fractional week
# ---------------------------
def date_to_fractional_week(d: date) -> float:
    if d < BASE_WEEK1_MONDAY:
        raise ValueError("Date is before Week 1.")
    delta_days = (d - BASE_WEEK1_MONDAY).days
    week_number = delta_days // 7 + 1
    day_index = delta_days % 7
    return week_number + (day_index / 7.0)

# ---------------------------
# Build x,y data arrays
# ---------------------------
def build_xy_from_weekly(lst):
    x, y = [], []
    for i, price in enumerate(lst, start=1):
        if price is None:
            break
        x.append(float(i))
        y.append(float(price))
    return x, y

# ---------------------------
# Newton + Lagrange
# ---------------------------
def divided_difference_newton(x, y, target_x):
    n = len(x)
    table = [[0.0]*n for _ in range(n)]
    for i in range(n):
        table[i][0] = y[i]

    for j in range(1, n):
        for i in range(n - j):
            denom = x[i+j] - x[i]
            table[i][j] = (table[i+1][j-1] - table[i][j-1]) / denom

    coeffs = [table[0][j] for j in range(n)]

    result = coeffs[0]
    prod = 1.0
    for j in range(1, n):
        prod *= (target_x - x[j-1])
        result += coeffs[j] * prod
    return result, coeffs

def lagrange_interpolation(x, y, target_x):
    total = 0.0
    n = len(x)
    for i in range(n):
        Li = 1.0
        for j in range(n):
            if i != j:
                Li *= (target_x - x[j]) / (x[i] - x[j])
        total += y[i] * Li
    return total

# ---------------------------
# Pick nearest N points
# ---------------------------
def choose_nearest_points(x_all, y_all, target_x, n_points):
    pos = bisect.bisect_left(x_all, target_x)
    left = pos - 1
    right = pos
    selected = []
    total = len(x_all)

    while len(selected) < n_points:
        pick_left = False
        if left < 0:
            pick_left = False
        elif right >= total:
            pick_left = True
        else:
            if abs(x_all[left] - target_x) <= abs(x_all[right] - target_x):
                pick_left = True

        if pick_left:
            selected.append((x_all[left], y_all[left], left))
            left -= 1
        else:
            selected.append((x_all[right], y_all[right], right))
            right += 1

    selected.sort(key=lambda t: t[0])
    x_sel = [t[0] for t in selected]
    y_sel = [t[1] for t in selected]
    idxs = [t[2] for t in selected]
    return x_sel, y_sel, idxs

# ---------------------------
# MAIN LOOP
# ---------------------------
def main():
    print("\nEgg Price Extrapolation Tool (MM-DD-YYYY input)")
    print("Base Week 1:", BASE_WEEK1_MONDAY.isoformat())

    x_all, y_all = build_xy_from_weekly(weekly_prices)
    n_available = len(x_all)

    while True:
        print("\n--------------------------------------------")
        s = input("Enter date (MM-DD-YYYY) or 'exit': ").strip()

        if s.lower() in ("exit", "quit"):
            print("Goodbye.")
            return

        try:
            d = datetime.strptime(s, "%m-%d-%Y").date()
        except:
            print("Invalid format. Use MM-DD-YYYY.")
            continue

        try:
            target_x = date_to_fractional_week(d)
        except Exception as e:
            print(e)
            continue

        print(f"\nConverted to fractional week x = {target_x:.6f}")

        # choose number of points
        while True:
            try:
                np = int(input(f"How many data points to use (2..{n_available}): ").strip())
                if 2 <= np <= n_available:
                    break
                else:
                    print("Invalid count.")
            except:
                print("Enter a number.")

        x_sel, y_sel, idxs = choose_nearest_points(x_all, y_all, target_x, np)

        print("\nSelected data points:")
        for xi, yi in zip(x_sel, y_sel):
            print(f"  Week {int(xi)} -> {yi}")

        # Compute BOTH methods
        newton_val, coeffs = divided_difference_newton(x_sel, y_sel, target_x)
        lag_val = lagrange_interpolation(x_sel, y_sel, target_x)

        print("\n==================== RESULTS ====================")
        print(f"Newton estimate   : {newton_val:.4f}")
        print(f"Lagrange estimate : {lag_val:.4f}")
        print("=================================================")

        show = input("Show Newton coefficients? (y/n): ").lower().strip()
        if show == "y":
            print("\nNewton coefficients:")
            for i, c in enumerate(coeffs):
                print(f"  a{i} = {c}")

        print("\nDistance summary:")
        for xi, yi in zip(x_sel, y_sel):
            dist = abs(xi - target_x)
            monday = BASE_WEEK1_MONDAY + timedelta(days=(int(xi)-1)*7)
            print(f"  Week {int(xi)} (start {monday})  price={yi}  |x-target|={dist:.4f}")

        print("\nDone. The program will now ask again.\n")

if __name__ == "__main__":
    main()
