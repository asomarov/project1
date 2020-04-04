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

headers = db.execute("SELECT * FROM columnsoftable").fetchall()
headernames = ["id", "isbn", "title", "author", "year"]

@app.route("/")
def index():
    allyears = db.execute("SELECT year FROM books ORDER BY year ASC").fetchall() #to get a list of all publication years
    years = []                                                                      #an empty list
    [years.append(item) for item in allyears if item not in years]                  #deleting duplicates

    return render_template("index.html", headers = headers, years = years)

@app.route("/search_results", methods=["POST"])
def search_results():
    """Search results"""

    item = request.form.get("search_item")
    #item = str('\'' + "%" + str(item) + "%" + '\'')
    item = "%" + str(item) + "%"

    try:
        i = int(request.form.get("search_type"))
    except TypeError:
        return render_template("error.html", message="There is no such search type")

    if i == 1:
        rescount = db.execute("SELECT * FROM books WHERE isbn LIKE :item", {"item": item}).rowcount
        res = db.execute("SELECT * FROM books WHERE isbn LIKE :item", {"item": item}).fetchall()
    elif i == 2:
        rescount = db.execute("SELECT * FROM books WHERE title LIKE :item", {"item": item}).rowcount
        res = db.execute("SELECT * FROM books WHERE title LIKE :item", {"item": item}).fetchall()
    elif i == 3:
        rescount = db.execute("SELECT * FROM books WHERE author LIKE :item", {"item": item}).rowcount
        res = db.execute("SELECT * FROM books WHERE author LIKE :item", {"item": item}).fetchall()

    if rescount == 0:
        return render_template("error.html", message="Nothing found, please rephrase your query")
    else:
        return render_template("search_results.html", res=res)

@app.route("/search_by_year", methods=["POST"])
def search_by_year():
    """Search results"""

    year = request.form.get("year")

    rescount = db.execute("SELECT * FROM books WHERE year = :year", {"year": year}).rowcount
    res = db.execute("SELECT * FROM books WHERE year = :year", {"year": year}).fetchall()

    if rescount == 0:
        return render_template("error.html", message="Nothing found, try another year")
    else:
        return render_template("search_by_year.html", res=res, year=year)

@app.route("/more")
def more():
    return render_template("more.html")
