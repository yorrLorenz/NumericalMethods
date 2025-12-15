from flask import Flask, render_template, request
from datetime import datetime, date, timedelta
import bisect

app = Flask(__name__)

BASE_WEEK1_MONDAY = date(2023, 8, 21)
MAX_POINTS = 119

weekly_prices = [
    7.29, 7.23, 7.25, 7.34, 7.56, 7.64, 7.73, 7.87, 7.88, 7.96,
    8.02, 8.10, 8.14, 8.18, 8.19, 8.20, 8.17, 8.14, 8.13, 8.08,
    8.07, 7.95, 7.95, 7.80, 7.71, 7.46, 7.38, 7.37, 7.37, 7.34,
    7.33, 7.31, 7.26, 7.08, 7.04, 7.11, 7.00, 7.00, 6.91, 6.93,
    7.06, 7.10, 7.02, 7.12, 7.16, 7.29, 7.47, 7.55, 7.71, 7.80,
    7.88, 7.93, 8.00, 8.04, 8.07, 8.12, 8.17, 8.27, 8.29, 8.38,
    8.43, 8.49, 8.46, 8.46, 8.45, 8.47, 8.43, 8.45, 8.40, 8.38,
    8.36, 8.39, 8.31, 8.17, 8.14, 8.04, 7.96, 7.95, 7.96, 8.00,
    8.02, 8.05, 8.07, 8.12, 8.12, 8.14, 8.12, 8.11, 8.09, 8.04,
    8.00, 8.04, 8.01, 8.00, 8.05, 8.00, 8.01, 8.01, 8.05, 8.07,
    8.07, 8.11, 8.17, 8.20, 8.24, 8.24, 8.31, 8.30, 8.32, 8.35,
    8.32, 8.37, 8.35, 8.33, 8.32, 8.33, 8.34, 8.31, 8.29
]

history = []


def date_to_fractional_week(d):
    delta_days = (d - BASE_WEEK1_MONDAY).days
    if delta_days < 0:
        raise ValueError("Date is before Week 1.")
    week = delta_days // 7 + 1
    day = delta_days % 7
    return week + day / 7.0


def build_xy(prices):
    x = [float(i + 1) for i in range(len(prices))]
    y = [float(p) for p in prices]
    return x, y


def newton_interpolation(x, y, target_x):
    n = len(x)
    table = [[0.0] * n for _ in range(n)]
    for i in range(n):
        table[i][0] = y[i]
    for j in range(1, n):
        for i in range(n - j):
            table[i][j] = (table[i + 1][j - 1] - table[i][j - 1]) / (x[i + j] - x[i])
    result = table[0][0]
    prod = 1.0
    for j in range(1, n):
        prod *= (target_x - x[j - 1])
        result += table[0][j] * prod
    return result


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


def nearest_points(x_all, y_all, target_x, n):
    pos = bisect.bisect_left(x_all, target_x)
    left = max(0, pos - n)
    right = min(len(x_all), pos + n)
    pairs = list(zip(x_all[left:right], y_all[left:right]))
    pairs.sort(key=lambda p: abs(p[0] - target_x))
    pairs = sorted(pairs[:n], key=lambda p: p[0])
    return [p[0] for p in pairs], [p[1] for p in pairs]


def build_data_table():
    table = []
    for i, price in enumerate(weekly_prices):
        start = BASE_WEEK1_MONDAY + timedelta(weeks=i)
        end = start + timedelta(days=4)
        table.append({
            "week": i + 1,
            "range": f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}",
            "price": f"{price:.2f}"
        })
    return table


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    week_value = None
    error = None
    selected_weeks = []

    if request.method == "POST":
        try:
            d = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            n = int(request.form["n_points"])

            if n < 2 or n > MAX_POINTS:
                raise ValueError("Data points must be between 2 and 119.")

            target_x = date_to_fractional_week(d)
            x_all, y_all = build_xy(weekly_prices)
            x_sel, y_sel = nearest_points(x_all, y_all, target_x, n)

            newton_val = newton_interpolation(x_sel, y_sel, target_x)
            lag_val = lagrange_interpolation(x_sel, y_sel, target_x)

            result = (newton_val, lag_val)
            week_value = target_x
            selected_weeks = [int(x) for x in x_sel]

            history.append({
                "date": d.strftime("%Y-%m-%d"),
                "week": round(target_x, 3),
                "points": n,
                "newton": round(newton_val, 4),
                "lagrange": round(lag_val, 4)
            })

        except Exception as e:
            error = str(e)

    return render_template(
        "index.html",
        result=result,
        week_value=week_value,
        error=error,
        data_table=build_data_table(),
        selected_weeks=selected_weeks,
        history=history
    )


if __name__ == "__main__":
    app.run(debug=True)
