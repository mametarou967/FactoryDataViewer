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
DATA_DIR = "data/sensor"
HINMOKU_SUBDIR = "../hinmoku"  # 品目CSVのサブディレクトリ名（data/hinmoku/）

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

def read_hinmoku_csv(date_str):
    """
    品目CSV: data/hinmoku/A214_YYYYMMDD_.csv を読み、(headers, rows) を返す。
    rows は 1行=リスト。1行目は見出し。
    文字コードは cp932 優先、失敗時に utf-8 にフォールバック。
    """
    yyyymmdd = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
    expected_name = f"A214_{yyyymmdd}_.csv"
    dirpath = os.path.join(DATA_DIR, HINMOKU_SUBDIR)
    filepath = os.path.join(dirpath, expected_name)

    if not os.path.isdir(dirpath) or not os.path.exists(filepath):
        return None, None, expected_name  # 見つからない

    rows = []
    # cp932 -> utf-8 の順でトライ
    tried_encodings = ["cp932", "utf-8"]
    last_err = None
    for enc in tried_encodings:
        try:
            with open(filepath, newline="", encoding=enc) as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        rows.append(row)
            break
        except Exception as e:
            rows = []
            last_err = e
            continue

    if not rows:
        # 空 or 読めない
        return None, None, expected_name

    headers = rows[0]
    records = rows[1:]
    return headers, records, expected_name

def set_japanese_font():
    """日本語フォント設定（存在すれば適用）"""
    font_path = "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf"
    if os.path.exists(font_path):
        plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()


def _day_range(date_str):
    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    start = datetime.combine(base_date, datetime.strptime("00:00:00", "%H:%M:%S").time())
    end   = start + timedelta(days=1)
    return start, end


def _load_minute_colors(date_str, start_dt=None, end_dt=None, include_gray=True):
    """
    data/<date_str>.csv を読み、分単位の色辞書 {datetime: color} を返す。
    start_dt/end_dt が指定されれば [start_dt, end_dt) にクリップして格納。
    include_gray=False の場合は 'gray' を除外。
    """
    csv_path = os.path.join(DATA_DIR, f"{date_str}.csv")
    if not os.path.exists(csv_path):
        return None  # データなし

    day_start, day_end = _day_range(date_str)

    # クリップ（無指定なら一日分）
    s = max(start_dt, day_start) if start_dt else day_start
    e = min(end_dt,   day_end)   if end_dt   else day_end

    minute_color = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            try:
                t = datetime.strptime(date_str + " " + row[0], "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue

            # クリップ範囲外は無視
            if not (s <= t < e):
                continue

            try:
                r, y, g, c = float(row[1]), float(row[2]), float(row[3]), float(row[4])
                _, _, _, color = get_light_status(r, y, g, c)
                if (color == "gray") and (not include_gray):
                    continue
                minute_color[t] = color
            except Exception:
                continue

    return minute_color


def _render_day_timeline(date_str, minute_color, out_png_path, title):
    """
    1日横棒を描画。minute_color に入っている分だけ色を塗る。
    """
    set_japanese_font()
    day_start, day_end = _day_range(date_str)

    plt.figure(figsize=(14, 2))
    current = day_start
    while current < day_end:
        color = minute_color.get(current)
        if color:
            left = (current - day_start).total_seconds()
            plt.barh(0, 60, left=left, height=0.5, color=color)
        current += timedelta(minutes=1)

    # 目盛り（毎時）
    xticks, xticklabels = [], []
    hour = day_start
    while hour <= day_end:
        xticks.append((hour - day_start).total_seconds())
        xticklabels.append("24:00" if hour == day_end else hour.strftime("%H:%M"))
        hour += timedelta(hours=1)

    plt.xticks(xticks, xticklabels)
    plt.yticks([])
    plt.xlim(0, (day_end - day_start).total_seconds())
    plt.title(title)
    plt.tight_layout()

    os.makedirs("static", exist_ok=True)
    if os.path.exists(out_png_path):
        os.remove(out_png_path)
    plt.savefig(out_png_path)
    plt.close()


def generate_graph_image_unified(
    date_str,
    start_dt=None,
    end_dt=None,
    out_png_path=None,
    include_gray=True,
    skip_if_up_to_date=True,
):
    """
    1本化された描画関数。
    - 日全体: start_dt/end_dt を渡さない
    - 区間のみ: start_dt/end_dt を渡す（[start_dt, end_dt)）
    - out_png_path 未指定時はデイリーの既定パスを使う
    - デイリーはCSVが新しければ再描画、最新ならスキップ（skip_if_up_to_date=True）
    """
    csv_path = os.path.join(DATA_DIR, f"{date_str}.csv")
    if not os.path.exists(csv_path):
        return False

    # 既定の出力先
    if out_png_path is None:
        image_filename = f"{date_str}_graph.png"
        out_png_path = os.path.join("static", image_filename)

    # 「日全体」かつ「最新ならスキップ」だけ最適化
    is_full_day = (start_dt is None and end_dt is None)
    if skip_if_up_to_date and is_full_day and os.path.exists(out_png_path):
        if os.path.getmtime(csv_path) <= os.path.getmtime(out_png_path):
            return True  # 画像が最新

    # 分ごとの色割り当てを取得
    minute_color = _load_minute_colors(
        date_str,
        start_dt=start_dt,
        end_dt=end_dt,
        include_gray=include_gray
    )
    if not minute_color:
        return False

    # タイトル
    if is_full_day:
        title = f"{date_str} 状態推移グラフ"
    else:
        # 表示は当日内の時刻だけで十分
        s = start_dt.strftime("%H:%M")
        e = end_dt.strftime("%H:%M")
        title = f"{date_str} 品目時間帯グラフ（{s}〜{e}）"

    _render_day_timeline(date_str, minute_color, out_png_path, title)
    return True

def generate_graph_image(date):
    # 互換ラッパー：そのまま呼ばれても動くように
    return generate_graph_image_unified(date_str=date)

def generate_graph_image_for_interval(date_str, start_dt, end_dt, out_png_path):
    # 互換ラッパー：include_gray のデフォルトはこれまでと同じ挙動（灰色も描画）
    return generate_graph_image_unified(
        date_str=date_str,
        start_dt=start_dt,
        end_dt=end_dt,
        out_png_path=out_png_path,
        include_gray=True,
        # 区間は同じファイル名で上書きする可能性があるので常に再描画を推奨
        skip_if_up_to_date=False,
    )

# --- 追記: 柔軟な日時パーサ（秒あり/なしを許容） ---
def parse_flexible_dt(s):
    """
    "YYYY/M/D H:M[:S]" 形式（ゼロ詰め無しOK、秒あり/なし両対応）を受け付けて datetime を返す。
    例: "2025/8/4 8:46", "2025/08/04 08:46:13"
    """
    s = s.strip()
    fmts = [
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%-m/%-d %-H:%-M:%-S",  # Linux系のゼロ無し。Windowsでは無視されるが例として残す
        "%Y/%-m/%-d %-H:%-M",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    # 上の %- 指定は環境依存。最後に標準的な置換で再トライ
    try:
        # ゼロ詰めして秒なしをまず試す
        parts = s.replace("/", " ").replace(":", " ").split()
        # ["YYYY","M","D","H","M"(,"S")]
        if len(parts) >= 5:
            Y, M, D, h, m = parts[:5]
            sec = parts[5] if len(parts) >= 6 else "00"
            canon = f"{int(Y):04d}/{int(M):02d}/{int(D):02d} {int(h):02d}:{int(m):02d}:{int(sec):02d}"
            return datetime.strptime(canon, "%Y/%m/%d %H:%M:%S")
    except Exception:
        pass
    raise ValueError("日時の形式が不正です")

# --- 追記: 区間限定の状態別集計ユーティリティ ---
def summarize_states_for_interval(date_str, start_dt, end_dt):
    """
    data/<date_str>.csv の 1分単位データを読み、[start_dt, end_dt) の区間だけ
    状態別合計秒数を算出して返す（dict: state -> 秒）。
    区間が当日の 0:00〜24:00 をはみ出していれば当日内にクリップする。
    """
    csv_path = os.path.join(DATA_DIR, f"{date_str}.csv")
    if not os.path.exists(csv_path):
        return None  # データなし

    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    day_start = datetime.combine(base_date, datetime.strptime("00:00:00", "%H:%M:%S").time())
    day_end   = day_start + timedelta(days=1)

    # クリップ
    s = max(start_dt, day_start)
    e = min(end_dt,   day_end)
    if not (s < e):
        # 重なりなし
        return {k: 0 for k in ["加工中", "手動加工中", "加工完了", "アラーム", "不明"]}

    states = ["加工中", "手動加工中", "加工完了", "アラーム", "不明"]
    secs = {state: 0 for state in states}

    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            try:
                t = datetime.strptime(date_str + " " + row[0], "%Y-%m-%d %H:%M:%S")
            except Exception:
                # 時刻列が壊れている行はスキップ
                continue

            if not (s <= t < e):
                continue

            try:
                r, y, g, c = float(row[1]), float(row[2]), float(row[3]), float(row[4])
                _, _, state, _ = get_light_status(r, y, g, c)
                secs[state] += 60  # 1分分加算
            except Exception:
                continue

    return secs


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

    return render_template("month/graph.html", year_month=year_month, images=images)


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

    return render_template("month/summary.html", year_month=year_month, states=states, labels=labels, summaries=summaries)

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
    
    year_month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
    
    return render_template("date/sensor_data_list.html", date=date,year_month=year_month, rows=rows)

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

    year_month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
    return render_template("date/status_list.html", date=date,year_month=year_month, rows=rows)

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

    year_month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")

    return render_template("date/graph.html", date=date, year_month=year_month, image_filename=image_filename)

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

    year_month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")

    return render_template("date/summary.html", date=date, year_month=year_month, durations=durations)

@app.route("/date/<date>/hinmoku")
def show_hinmoku_for_date(date):
    """
    指定日付の品目一覧（行頭に 1..N の行番号列を追加＆リンク化）
    """
    # 日付バリデーション
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        abort(404)

    headers, records, filename = read_hinmoku_csv(date)
    if not headers or records is None:
        return render_template(
            "date/hinmoku_list.html",
            has_data=False,
            date=date,
            message="品目リストはありません"
        )

    # 先頭に「#」列を追加したヘッダ
    display_headers = ["#"] + headers

    # 行番号を付与（1始まり）。リンク先は /date/<date>/hinmoku/<idx>
    # テンプレ側でリンクを生成するため、ここではインデックスのみ渡す
    indexed_records = []
    for i, row in enumerate(records, start=1):
        indexed_records.append((i, row))  # (行番号, 元の行)

    year_month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
    
    return render_template(
        "date/hinmoku_list.html",
        has_data=True,
        date=date,
        year_month=year_month,
        headers=display_headers,
        records=indexed_records,
        filename=filename
    )

@app.route("/date/<date>/hinmoku/<int:hinmokuno>")
def show_hinmoku_graph(date, hinmokuno):
    """
    指定行(hinmokuno: 1始まり)の「着手日時〜完了日時」だけ色が付いた1日グラフを生成・表示。
    """
    # 日付バリデーション
    try:
        base_dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        abort(404)

    headers, records, filename = read_hinmoku_csv(date)
    if not headers or not records:
        abort(404, description="品目リストがありません。")

    if hinmokuno < 1 or hinmokuno > len(records):
        abort(404, description="指定の品目番号が範囲外です。")

    row = records[hinmokuno - 1]
    # 想定列：
    # 0:機械番号 1:製番 2:手配番号 3:品目番号 4:品目名 5:手配数 6:段取時間 7:加工時間 8:着手日時 9:完了日時
    try:
        start_raw = row[8].strip()
        end_raw   = row[9].strip()
        # 例: "2025/8/4 8:46" → "%Y/%m/%d %H:%M" でパース（0詰め無しにも対応）
        start_dt = datetime.strptime(start_raw, "%Y/%m/%d %H:%M:%S")
        end_dt   = datetime.strptime(end_raw,   "%Y/%m/%d %H:%M:%S")
    except Exception:
        abort(400, description="着手日時/完了日時の形式が不正です。")

    # 画像生成
    image_filename = f"{date}_hinmoku_{hinmokuno}.png"
    image_path = os.path.join("static", image_filename)
    ok = generate_graph_image_for_interval(date, start_dt, end_dt, image_path)
    if not ok:
        abort(400, description="グラフ画像の生成に失敗しました。対象区間にデータが無い可能性があります。")

    year_month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
    
    # グラフ表示
    return render_template(
        "hinmoku/graph.html",
        date=date,
        year_month=year_month,
        hinmokuno=hinmokuno,
        image_filename=image_filename,
        row=row,
        headers=headers
    )

# --- 追記: 品目の稼働時間集計（着手〜完了） ---
@app.route("/date/<date>/hinmoku/<int:hinmokuno>/summary")
def show_hinmoku_summary(date, hinmokuno):
    """
    指定日の品目CSV(data/hinmoku/A214_YYYYMMDD_.csv) から行番号 hinmokuno を取り、
    その着手日時(7列目)〜完了日時(8列目)の区間に限定して、
    data/<date>.csv を用いて状態別の合計時間を集計して表示する。
    """
    # 日付バリデーション
    try:
        base_dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        abort(404)

    headers, records, filename = read_hinmoku_csv(date)
    if not headers or not records:
        abort(404, description="品目リストがありません。")

    if hinmokuno < 1 or hinmokuno > len(records):
        abort(404, description="指定の品目番号が範囲外です。")

    row = records[hinmokuno - 1]
    # 0:機械番号 1:製番 2:手配番号 3:品目番号 4:品目名 5:手配数 6:段取時間 7:加工時間 8:着手日時 9:完了日時
    try:
        start_raw = row[8]
        end_raw   = row[9]
        start_dt = parse_flexible_dt(start_raw)
        end_dt   = parse_flexible_dt(end_raw)
    except Exception:
        abort(400, description="着手日時/完了日時の形式が不正です。")

    if end_dt <= start_dt:
        abort(400, description="完了日時が着手日時以下です。")

    # 区間の状態別集計（当日内に自動クリップ）
    secs = summarize_states_for_interval(date, start_dt, end_dt)
    if secs is None:
        abort(404, description=f"{date}.csv が見つかりません。")

    # 時間に変換（小数2桁）
    durations_hours = {k: round(v / 3600.0, 2) for k, v in secs.items()}

    # 参考情報
    interval_info = {
        "start": start_dt.strftime("%Y/%m/%d %H:%M:%S"),
        "end":   end_dt.strftime("%Y/%m/%d %H:%M:%S"),
        "clipped_date": date  # 当日CSVで集計
    }

    year_month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")

    return render_template(
        "hinmoku/summary.html",
        date=date,
        year_month=year_month,
        hinmokuno=hinmokuno,
        headers=headers,
        row=row,
        durations=durations_hours,
        interval=interval_info,
        filename=filename
    )

# --- 追加: 本日分の手配情報（品目の基本情報を分離表示） ---
@app.route("/date/<date>/hinmoku/<int:hinmokuno>/info")
def show_hinmoku_info(date, hinmokuno):
    """
    指定日の品目CSV(data/hinmoku/A214_YYYYMMDD_.csv) から行番号 hinmokuno を取り、
    その着手日時(7列目)〜完了日時(8列目)の区間に限定して、
    data/<date>.csv を用いて状態別の合計時間を集計して表示する。
    """
    # 日付バリデーション
    try:
        base_dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        abort(404)

    headers, records, filename = read_hinmoku_csv(date)
    if not headers or not records:
        abort(404, description="品目リストがありません。")

    if hinmokuno < 1 or hinmokuno > len(records):
        abort(404, description="指定の品目番号が範囲外です。")

    row = records[hinmokuno - 1]
    # 0:機械番号 1:製番 2:手配番号 3:品目番号 4:品目名 5:手配数 6:段取時間 7:加工時間 8:着手日時 9:完了日時
    try:
        start_raw = row[8]
        end_raw   = row[9]
        start_dt = parse_flexible_dt(start_raw)
        end_dt   = parse_flexible_dt(end_raw)
    except Exception:
        abort(400, description="着手日時/完了日時の形式が不正です。")

    if end_dt <= start_dt:
        abort(400, description="完了日時が着手日時以下です。")

    # 区間の状態別集計（当日内に自動クリップ）
    secs = summarize_states_for_interval(date, start_dt, end_dt)
    if secs is None:
        abort(404, description=f"{date}.csv が見つかりません。")

    # 時間に変換（小数2桁）
    durations_hours = {k: round(v / 3600.0, 2) for k, v in secs.items()}

    # 参考情報
    interval_info = {
        "start": start_dt.strftime("%Y/%m/%d %H:%M:%S"),
        "end":   end_dt.strftime("%Y/%m/%d %H:%M:%S"),
        "clipped_date": date  # 当日CSVで集計
    }

    year_month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")

    return render_template(
        "hinmoku/info.html",
        date=date,
        year_month=year_month,
        hinmokuno=hinmokuno,
        headers=headers,
        row=row,
        durations=durations_hours,
        interval=interval_info,
        filename=filename
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
