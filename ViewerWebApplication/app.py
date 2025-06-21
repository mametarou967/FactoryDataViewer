from flask import Flask, render_template, abort, send_file
import csv
import os
from datetime import datetime, timedelta

app = Flask(__name__)
DATA_DIR = "data"

# 点灯/消灯の閾値
THRESHOLDS = {
    "red": 30,
    "yellow": 100,
    "green": 50
}

# 点灯・状態判定
def get_light_status(red, yellow, green):
    def is_on(color, value):
        return value >= THRESHOLDS[color]

    status = {
        "red": "点灯" if is_on("red", red) else "消灯",
        "yellow": "点灯" if is_on("yellow", yellow) else "消灯",
        "green": "点灯" if is_on("green", green) else "消灯"
    }

    # 状態と色
    state, color = "不明", "gray"
    if status["green"] == "点灯" and status["red"] == "消灯" and status["yellow"] == "消灯":
        state, color = "加工中", "green"
    elif status["yellow"] == "点灯" and status["red"] == "消灯" and status["green"] == "消灯":
        state, color = "加工完了", "yellow"
    elif status["red"] == "点灯" and status["yellow"] == "消灯" and status["green"] == "消灯":
        state, color = "設備停止／アラーム", "red"
    elif status["red"] == "点灯" and status["yellow"] == "点灯" and status["green"] == "消灯":
        state, color = "加工終了／設備停止", "orange"
    elif status["red"] == "点灯" and status["green"] == "点灯" and status["yellow"] == "消灯":
        state, color = "加工中／軽微なアラーム", "purple"

    return status, state, color

# 最新データ取得
def get_latest_data():
    now = datetime.now()
    threshold = now - timedelta(minutes=5)
    latest_row = None

    for filename in sorted(os.listdir(DATA_DIR), reverse=True):
        if not filename.endswith(".csv"):
            continue
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reversed(list(reader)):
                try:
                    row_time = datetime.strptime(f"{filename[:-4]} {row[0]}", "%Y-%m-%d %H:%M:%S")
                except:
                    continue
                if threshold <= row_time <= now:
                    return {
                        "time": row[0],
                        "red": float(row[1]),
                        "yellow": float(row[2]),
                        "green": float(row[3]),
                        "timestamp": row_time.strftime("%Y-%m-%d %H:%M:%S")
                    }
    return None

@app.route("/")
def index():
    latest = get_latest_data()
    status = {}
    if latest:
        lights, _, _ = get_light_status(latest["red"], latest["yellow"], latest["green"])
        status = {**lights, "timestamp": latest["timestamp"]}
    return render_template("index.html", status=status if latest else None)

@app.route("/<date>")
def show_table(date):
    filename = f"{date}.csv"
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
    rows = []
    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            rows.append({
                "time": row[0],
                "red": row[1],
                "yellow": row[2],
                "green": row[3],
                "current": row[4]
            })
    return render_template("table.html", date=date, rows=rows)

@app.route("/<date>/status")
def show_status_table(date):
    filename = f"{date}.csv"
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
    rows = []
    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            red, yellow, green = float(row[1]), float(row[2]), float(row[3])
            lights, state, color = get_light_status(red, yellow, green)
            rows.append({
                "time": row[0], "red": lights["red"], "yellow": lights["yellow"],
                "green": lights["green"], "state": state, "color": color
            })
    return render_template("status_table.html", date=date, rows=rows)

@app.route("/<date>/graph")
def show_graph(date):
    image_path = os.path.join(DATA_DIR, f"{date}_graph.png")
    csv_path = os.path.join(DATA_DIR, f"{date}.csv")
    if not os.path.exists(csv_path):
        abort(404)

    from matplotlib import pyplot as plt
    import pandas as pd

    def determine_state(r, y, g):
        return get_light_status(r, y, g)[1:]

    times, colors = [], []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            time = datetime.strptime(row[0], "%H:%M:%S")
            state, color = determine_state(float(row[1]), float(row[2]), float(row[3]))
            times.append(time)
            colors.append(color)

    plt.figure(figsize=(12, 1.5))
    for i in range(len(times) - 1):
        plt.barh(0, (times[i+1] - times[i]).seconds, left=(times[i] - times[0]).seconds, color=colors[i], height=0.5)
    plt.yticks([])
    plt.title(f"{date} 状態時系列")
    plt.tight_layout()
    plt.savefig(image_path)
    plt.close()
    return send_file(image_path, mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
