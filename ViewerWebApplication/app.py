from flask import Flask, render_template, abort, send_file
import csv
import os
from datetime import datetime, timedelta

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import matplotlib.font_manager as fm
from collections import defaultdict

app = Flask(__name__)
DATA_DIR = "data"

# 点灯/消灯の閾値
THRESHOLDS = {
    "red": 200,
    "yellow": 200,
    "green": 200
}
CURRENT_THRESHOLD = 3.0

# 点灯・状態判定
def get_light_status(red, yellow, green, current):
    def is_on(color, value):
        return value >= THRESHOLDS[color]

    status = {
        "red": "点灯" if is_on("red", red) else "消灯",
        "yellow": "点灯" if is_on("yellow", yellow) else "消灯",
        "green": "点灯" if is_on("green", green) else "消灯"
    }

    machine_action = "加工中" if current >= CURRENT_THRESHOLD else "加工なし"

    # 状態判定
    state, color = "不明", "gray"  # 色なし
    r, y, g, m = status["red"], status["yellow"], status["green"], machine_action
    
    if r == "消灯" and y == "消灯" and g == "消灯" and m == "加工なし":
        state, color = "不明", "gray"
    elif r == "消灯" and y == "消灯" and g == "点灯" and m == "加工なし":
        state, color = "加工中", "green"
    elif r == "消灯" and y == "点灯" and g == "消灯" and m == "加工なし":
        state, color = "加工完了", "yellow"
    elif r == "消灯" and y == "点灯" and g == "点灯" and m == "加工なし":
        state, color = "加工中", "green"
    elif r == "点灯" and y == "消灯" and g == "消灯" and m == "加工なし":
        state, color = "アラーム", "red"
    elif r == "点灯" and y == "消灯" and g == "点灯" and m == "加工なし":
        state, color = "加工中", "green"
    elif r == "点灯" and y == "点灯" and g == "消灯" and m == "加工なし":
        state, color = "加工完了", "yellow"
    elif r == "点灯" and y == "点灯" and g == "点灯" and m == "加工なし":
        state, color = "加工中", "green"
    elif r == "消灯" and y == "消灯" and g == "消灯" and m == "加工中":
        state, color = "手動加工中", "blue"
    elif r == "消灯" and y == "消灯" and g == "点灯" and m == "加工中":
        state, color = "加工中", "green"
    elif r == "消灯" and y == "点灯" and g == "消灯" and m == "加工中":
        state, color = "手動加工中", "blue"
    elif r == "消灯" and y == "点灯" and g == "点灯" and m == "加工中":
        state, color = "加工中", "green"
    elif r == "点灯" and y == "消灯" and g == "消灯" and m == "加工中":
        state, color = "手動加工中", "blue"
    elif r == "点灯" and y == "消灯" and g == "点灯" and m == "加工中":
        state, color = "加工中", "green"
    elif r == "点灯" and y == "点灯" and g == "消灯" and m == "加工中":
        state, color = "手動加工中", "blue"
    elif r == "点灯" and y == "点灯" and g == "点灯" and m == "加工中":
        state, color = "加工中", "green"

    return status, machine_action, state, color

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
                        "current": float(row[4]),
                        "timestamp": row_time.strftime("%Y-%m-%d %H:%M:%S")
                    }
    return None

def generate_graph_image(date):
    csv_path = os.path.join(DATA_DIR, f"{date}.csv")
    image_filename = f"{date}_graph.png"
    image_path = os.path.join("static", image_filename)

    if not os.path.exists(csv_path):
        return

    # CSVの方が新しければ再生成、そうでなければスキップ
    if os.path.exists(image_path):
        csv_mtime = os.path.getmtime(csv_path)
        image_mtime = os.path.getmtime(image_path)
        if csv_mtime <= image_mtime:
            return  # 画像が最新なので生成しない

    font_path = "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf"
    if os.path.exists(font_path):
        plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()

    data = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            try:
                t = datetime.strptime(date + " " + row[0], "%Y-%m-%d %H:%M:%S")  # 修正: 時間だけでなく日付と結合
                r, y, g, c = float(row[1]), float(row[2]), float(row[3]), float(row[4])
                _, _, _, color = get_light_status(r, y, g, c)
                data.append((t, color))
            except:
                continue

    if not data:
        return

    base_date = datetime.strptime(date, "%Y-%m-%d")
    range_start = datetime.combine(base_date, datetime.strptime("00:00:00", "%H:%M:%S").time())
    range_end = datetime.combine(base_date + timedelta(days=1), datetime.strptime("00:00:00", "%H:%M:%S").time())

    color_map = {t: c for t, c in data}
    current = range_start
    times, colors = [], []
    while current < range_end:
        next_time = current + timedelta(minutes=1)
        color = color_map.get(current, None)  # 修正: current.time() → current
        if color is None:
            pass
        elif color == "gray":
            times.append(current)
            colors.append("gray")
        else:
            times.append(current)
            colors.append(color)
        current = next_time

    plt.figure(figsize=(14, 2))
    for i in range(len(times)):
        left = (times[i] - range_start).total_seconds()
        plt.barh(0, 60, left=left, color=colors[i], height=0.5)

    xticks = []
    xticklabels = []
    hour = range_start
    while hour <= range_end:
        xticks.append((hour - range_start).total_seconds())
        # 最後のラベルだけ特別に「24:00」にする
        if hour == range_end:
            xticklabels.append("24:00")
        else:
            xticklabels.append(hour.strftime("%H:%M"))
        hour += timedelta(hours=1)

    plt.xticks(xticks, xticklabels, rotation=0)
    plt.yticks([])
    plt.xlim(0, (range_end - range_start).total_seconds())
    plt.title(f"{date} 状態推移グラフ")
    plt.tight_layout()

    os.makedirs("static", exist_ok=True)
    if os.path.exists(image_path):
        os.remove(image_path)
    plt.savefig(image_path)
    plt.close()


@app.route("/")
def index():
    latest = get_latest_data()
    status = {}
    if latest:
        lights, _, _, _ = get_light_status(latest["red"], latest["yellow"], latest["green"], latest["current"])
        status = {**lights, "current": latest["current"], "timestamp": latest["timestamp"]}
    # 年度判定（4月～翌年3月）
    now = datetime.now()
    if now.month >= 4:
        fiscal_start = datetime(now.year, 4, 1)
    else:
        fiscal_start = datetime(now.year - 1, 4, 1)
    fiscal_end = fiscal_start.replace(year=fiscal_start.year + 1) - timedelta(days=1)

    # 存在するCSV日付・月の判定
    existing_days = set()
    existing_months = set()
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".csv"):
            try:
                date_obj = datetime.strptime(fname[:-4], "%Y-%m-%d")
                if fiscal_start <= date_obj <= fiscal_end:
                    existing_days.add(date_obj.date())
                    existing_months.add(date_obj.strftime("%Y-%m"))
            except:
                continue

    # カレンダーデータ構築
    calendar = {}
    current = fiscal_start
    while current <= fiscal_end:
        ym = current.strftime("%Y-%m")
        if ym not in calendar:
            calendar[ym] = {
                "month_link": ym in existing_months,
                "weeks": [[]]
            }

        week = calendar[ym]["weeks"][-1]
        if len(week) == 0 and current.weekday() != 0:
            week.extend([None] * current.weekday())

        week.append({
            "day": current.day,
            "date": current.strftime("%Y-%m-%d"),
            "link": current.date() in existing_days
        })

        if current.weekday() == 6:
            calendar[ym]["weeks"].append([])

        current += timedelta(days=1)

    return render_template("index.html", status=status if latest else None, thresholds=THRESHOLDS, current_threshold = CURRENT_THRESHOLD, calendar=calendar)


@app.route("/month/<year_month>/graph")
def show_month_graph(year_month):
    try:
        month_date = datetime.strptime(year_month, "%Y-%m")
    except:
        abort(404)

    year = month_date.year
    month = month_date.month
    day = 1
    images = []

    while True:
        try:
            current_date = datetime(year, month, day)
        except:
            break
        date_str = current_date.strftime("%Y-%m-%d")
        csv_path = os.path.join(DATA_DIR, f"{date_str}.csv")
        image_filename = f"{date_str}_graph.png"
        image_path = os.path.join("static", image_filename)

        # 存在するCSVファイルについてのみ描画
        if os.path.exists(csv_path):
            generate_graph_image(date_str)
            images.append({
                "date": date_str,
                "image_filename": image_filename
            })

        day += 1

    if not images:
        abort(404)

    return render_template("month_graph.html", year_month=year_month, images=images)


@app.route("/month/<year_month>/summary")
def show_month_summary(year_month):
    print("hello")
    try:
        target_month = datetime.strptime(year_month, "%Y-%m")
    except ValueError:
        abort(404)

    states = ["加工中", "手動加工中", "加工完了", "アラーム", "不明"]
    summaries = {state: [] for state in states}
    labels = []

    # 存在する .csv の中で該当月のものだけを処理
    for fname in sorted(os.listdir(DATA_DIR)):
        print(fname)
        if not fname.endswith(".csv"):
            continue
        try:
            date_obj = datetime.strptime(fname[:-4], "%Y-%m-%d")
        except ValueError:
            continue

        if date_obj.strftime("%Y-%m") != year_month:
            continue

        labels.append(date_obj.strftime("%Y-%m-%d"))
        filepath = os.path.join(DATA_DIR, fname)
        durations = {state: 0 for state in states}

        print(filepath)
        with open(filepath, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) < 5:
                    continue
                try:
                    r, y, g, c = float(row[1]), float(row[2]), float(row[3]), float(row[4])
                    _, _, state, _ = get_light_status(r, y, g, c)
                    durations[state] += 60
                except:
                    continue

        for state in states:
            summaries[state].append(round(durations[state] / 3600, 2))

    # データが1件もない場合はabort
    if not labels:
        abort(404, description="指定された月にデータが見つかりませんでした")

    return render_template("month_summary.html", year_month=year_month, states=states, labels=labels, summaries=summaries)

@app.route("/date/<date>/table")
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

@app.route("/date/<date>/status")
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
            red, yellow, green, current = float(row[1]), float(row[2]), float(row[3]), float(row[4])
            lights, machine_action, state, color = get_light_status(red, yellow, green, current)
            rows.append({
                "time": row[0],
                "red": lights["red"],
                "yellow": lights["yellow"],
                "green": lights["green"],
                "machine_action": machine_action,
                "state": state,
                "color": color
            })
    return render_template("status_table.html", date=date, rows=rows)

@app.route("/date/<date>/graph")
def show_graph(date):
    image_filename = f"{date}_graph.png"
    image_path = os.path.join("static", image_filename)

    csv_path = os.path.join(DATA_DIR, f"{date}.csv")
    if not os.path.exists(csv_path):
        abort(404)

    # グラフ生成（既存ならスキップ）
    generate_graph_image(date)

    if not os.path.exists(image_path):
        abort(400, description="グラフ画像の生成に失敗しました。")

    return render_template("graph.html", date=date, image_filename=image_filename)

@app.route("/date/<date>/summary")
def show_day_summary(date):
    filepath = os.path.join(DATA_DIR, f"{date}.csv")
    if not os.path.exists(filepath):
        abort(404)

    states = ["加工中", "手動加工中", "加工完了", "アラーム", "不明"]
    durations = {state: 0 for state in states}

    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            try:
                r, y, g, c = float(row[1]), float(row[2]), float(row[3]), float(row[4])
                _, _, state, _ = get_light_status(r, y, g, c)
                durations[state] += 60  # assuming 1 minute resolution
            except:
                continue

    for key in durations:
        durations[key] = round(durations[key] / 3600, 2)

    return render_template("summary.html", date=date, durations=durations)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
