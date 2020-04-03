import os

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, render_template, request

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

headers = db.execute("SELECT * FROM books LIMIT 1").fetchone()
headerN = [1,2,3,4]
@app.route("/")
def index():
    #headers = db.execute("SELECT * FROM books LIMIT 1").fetchone()
    return render_template("index.html", headers = headers, headerN = headerN)

@app.route("/search_results", methods=["POST"])
def search_results():
    """Search results"""

    item = request.form.get("search_item")

    try:
        i = int(request.form.get("i"))
    except ValueError:
        return render_template("error.html", message="Nothing found, please try to rephrase your query")
    res = db.execute("SELECT * FROM books WHERE :header LIKE CONCAT('%',:item,'%')", {"header": header, "item": item}).fetchall()

    if res is None:
        return render_template("error.html", message="Nothing found, please try to rephrase your query")
    else:
        return render_template("search_results.html", res=res)
@app.route("/more")
def more():
    return render_template("more.html")
