from flask import Flask, render_template, request
from datetime import date, datetime
import bisect

app = Flask(__name__)

BASE_WEEK1_MONDAY = date(2023, 8, 21)

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

history_log = []

def date_to_fractional_week(d):
    delta_days = (d - BASE_WEEK1_MONDAY).days
    if delta_days < 0:
        raise ValueError("Date is before Week 1")
    return delta_days // 7 + 1 + (delta_days % 7) / 7

def build_xy(prices):
    return [i + 1 for i in range(len(prices))], prices[:]

def newton_interpolation(x, y, t):
    n = len(x)
    table = [[0]*n for _ in range(n)]
    for i in range(n):
        table[i][0] = y[i]
    for j in range(1, n):
        for i in range(n - j):
            table[i][j] = (table[i+1][j-1] - table[i][j-1]) / (x[i+j] - x[i])
    result, prod = table[0][0], 1
    for j in range(1, n):
        prod *= (t - x[j-1])
        result += table[0][j] * prod
    return result

def lagrange_interpolation(x, y, t):
    total = 0
    for i in range(len(x)):
        Li = 1
        for j in range(len(x)):
            if i != j:
                Li *= (t - x[j]) / (x[i] - x[j])
        total += y[i] * Li
    return total

def nearest_points(x, y, t, n):
    pos = bisect.bisect_left(x, t)
    pairs = list(zip(x[max(0, pos-n):pos+n], y[max(0, pos-n):pos+n]))
    pairs.sort(key=lambda p: abs(p[0]-t))
    pairs = sorted(pairs[:n], key=lambda p: p[0])
    return [p[0] for p in pairs], [p[1] for p in pairs]

@app.route("/", methods=["GET", "POST"])
def index():
    selected_weeks, result, week_value, error = [], None, None, None

    if request.method == "POST":
        try:
            d = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            n = int(request.form["n_points"])
            t = date_to_fractional_week(d)

            x, y = build_xy(weekly_prices)
            xs, ys = nearest_points(x, y, t, n)

            selected_weeks = xs[:]
            newton = newton_interpolation(xs, ys, t)
            lagrange = lagrange_interpolation(xs, ys, t)

            history_log.append({
                "date": d.strftime("%Y-%m-%d"),
                "week": round(t, 3),
                "points": n,
                "newton": round(newton, 4),
                "lagrange": round(lagrange, 4)
            })

            result, week_value = (newton, lagrange), t
        except Exception as e:
            error = str(e)

    data_table = []
    for i in range(len(weekly_prices)):
        start = BASE_WEEK1_MONDAY + timedelta(days=i*7)
        end = start + timedelta(days=4)
        data_table.append({
            "week": i+1,
            "price": weekly_prices[i],
            "range": f"{start.strftime('%b %d %Y')} – {end.strftime('%b %d %Y')}"
        })

    return render_template(
        "index.html",
        result=result,
        week_value=week_value,
        error=error,
        history=history_log,
        data_table=data_table,
        selected_weeks=selected_weeks
    )

if __name__ == "__main__":
    from datetime import timedelta
    app.run(debug=True)
