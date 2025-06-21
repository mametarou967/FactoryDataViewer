from flask import Flask, render_template, abort
import csv
import os
from datetime import datetime, timedelta

app = Flask(__name__)


DATA_DIR = "data"

def get_latest_data():
    now = datetime.now()
    threshold = now - timedelta(minutes=5)

    latest_row = None
    latest_time = None

    for filename in sorted(os.listdir(DATA_DIR), reverse=True):
        if not filename.endswith(".csv"):
            continue

        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reversed(list(reader)):  # 時刻が後ろにあることを想定
                try:
                    row_time = datetime.strptime(f"{filename[:-4]} {row[0]}", "%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue

                if row_time >= threshold and row_time <= now:
                    latest_row = {
                        "time": row[0],
                        "red": float(row[1]),
                        "yellow": float(row[2]),
                        "green": float(row[3]),
                        "timestamp": row_time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    return latest_row  # 最も新しい1件のみでOK

    return None

@app.route("/<date>")
def show_table(date):
    # サニタイズ簡易チェック（YYYY-MM-DD形式）
    if not date or len(date) != 10 or not date[0:4].isdigit():
        abort(404)

    filename = f"{date}.csv"
    filepath = os.path.join("data", filename)
    if not os.path.exists(filepath):
        return f"<h3>{filename} が見つかりません</h3>", 404

    rows = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
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

@app.route("/")
def index():
    latest = get_latest_data()
    status = {}

    if latest:
        status = {
            "red": "点灯" if latest["red"] >= 30 else "消灯",
            "yellow": "点灯" if latest["yellow"] >= 100 else "消灯",
            "green": "点灯" if latest["green"] >= 50 else "消灯",
            "timestamp": latest["timestamp"]
        }
    return render_template("index.html", status=status if latest else None)

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",port=5000)
