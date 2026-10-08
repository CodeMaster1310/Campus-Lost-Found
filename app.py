from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "campus-lost-found-secret"
DATABASE = "database.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            location TEXT NOT NULL,
            item_type TEXT NOT NULL,
            date TEXT NOT NULL,
            contact TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    lost_count = conn.execute("SELECT COUNT(*) FROM items WHERE item_type='Lost' AND status='Active'").fetchone()[0]
    found_count = conn.execute("SELECT COUNT(*) FROM items WHERE item_type='Found' AND status='Active'").fetchone()[0]
    returned_count = conn.execute("SELECT COUNT(*) FROM items WHERE status='Returned'").fetchone()[0]
    latest = conn.execute("SELECT * FROM items ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    return render_template("index.html", lost_count=lost_count, found_count=found_count,
                           returned_count=returned_count, latest=latest)

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        item_name = request.form["item_name"].strip()
        category = request.form["category"]
        description = request.form["description"].strip()
        location = request.form["location"].strip()
        item_type = request.form["item_type"]
        contact = request.form["contact"].strip()
        date = datetime.now().strftime("%Y-%m-%d")

        conn = get_db()
        conn.execute("""
            INSERT INTO items
            (item_name, category, description, location, item_type, date, contact)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item_name, category, description, location, item_type, date, contact))
        conn.commit()
        conn.close()

        flash("Item reported successfully!", "success")
        return redirect(url_for("items"))

    return render_template("report.html")

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    conn = get_db()
    if query:
        results = conn.execute("""
            SELECT * FROM items
            WHERE item_name LIKE ? OR category LIKE ? OR location LIKE ?
            ORDER BY id DESC
        """, (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
    else:
        results = []
    conn.close()
    return render_template("search.html", results=results, query=query)

@app.route("/items")
def items():
    conn = get_db()
    all_items = conn.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("items.html", items=all_items)

@app.route("/returned/<int:item_id>")
def returned(item_id):
    conn = get_db()
    conn.execute("UPDATE items SET status='Returned' WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    flash("Item marked as returned.", "success")
    return redirect(url_for("items"))

@app.route("/delete/<int:item_id>")
def delete(item_id):
    conn = get_db()
    conn.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    flash("Item deleted successfully.", "success")
    return redirect(url_for("items"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
