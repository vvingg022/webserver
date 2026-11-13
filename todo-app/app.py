import json
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DATA_FILE = Path(__file__).parent / "todos.json"


def load_todos():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_todos(todos):
    DATA_FILE.write_text(json.dumps(todos, indent=2), encoding="utf-8")


def new_id(todos):
    return max((t["id"] for t in todos), default=0) + 1


@app.route("/")
def index():
    return render_template("index.html", todos=load_todos())


@app.route("/add", methods=["POST"])
def add():
    text = request.form.get("text", "").strip()
    if text:
        todos = load_todos()
        todos.append({"id": new_id(todos), "text": text, "done": False})
        save_todos(todos)
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
def toggle(todo_id):
    todos = load_todos()
    for todo in todos:
        if todo["id"] == todo_id:
            todo["done"] = not todo["done"]
    save_todos(todos)
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    todos = [t for t in load_todos() if t["id"] != todo_id]
    save_todos(todos)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=8000)