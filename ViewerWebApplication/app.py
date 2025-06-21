from flask import Flask, render_template, abort
import csv
import os

app = Flask(__name__)

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
    return "<h3>日付をURLで指定してください。例：/2025-06-19</h3>"

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",port=5000)
