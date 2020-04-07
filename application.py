import os
import requests
import json

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

@app.route("/books")
def books():
    """List of all books"""

    books = db.execute("SELECT * FROM books").fetchall()
    return render_template("books.html", books=books)

@app.route("/books/<int:book_id>")
def book(book_id):
    """Details of a particular book"""
    #Make sure that we have that book in our database
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", message="There is no such book")

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "JJS9Nrl9dVZjEdT4rB8g", "isbns": book.isbn})
    if res.status_code != 200:
      raise Exception("ERROR: API request unsuccessful.")
    data = res.json()
    rating = data["books"][0]["average_rating"]
    ratingcount = data["books"][0]["work_ratings_count"]
    return render_template("book.html", book=book, rating=rating, ratingcount=ratingcount)

@app.route("/registration_form")
def registration_form():
    return render_template("registration_form.html")

@app.route("/register", methods=["POST"])
def register():
    """Registration form"""
    name = request.form.get("name")
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")

    u = db.execute("SELECT username FROM users WHERE username= :username", {"username": username}).fetchone()
    if name is "":
        return render_template("registration_error.html", message="Enter your name")
    elif username is "":
        return render_template("registration_error.html", message="Enter your username")
    elif password is "":
        return render_template("registration_error.html", message="Enter your password")
    elif not u is None:
        return render_template("registration_error.html", message="This username has already been chosen, select another username")

    db.execute("INSERT INTO users (name, email, username, password) VALUES(:name, :email, :username, :password)",
                                {"name": name, "email": email, "username": username, "password": password})
    db.commit()
    return render_template("registration_success.html", message="You have successfully registered")

@app.route("/sign_in", methods=["POST"])
def sign_in():
    username = request.form.get("regusername")
    password = request.form.get("regpassword")

    headers = db.execute("SELECT * FROM columnsoftable").fetchall()
    allyears = db.execute("SELECT year FROM books ORDER BY year ASC").fetchall() #to get a list of all publication years
    years = []                                                                      #an empty list
    [years.append(item) for item in allyears if item not in years]                  #deleting duplicates

    user = db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
                                        {"username": username, "password": password}).fetchone()
    if not user is None:
        return render_template("signin.html", headers = headers, years = years, user=username)
    else:
        return render_template("error.html", message="Your username or password is incorrect")

@app.route("/<string:username>")
def username(username):
    user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE user_id = :user_id", {"user_id": user.id}).fetchall()
    revcount = db.execute("SELECT * FROM reviews WHERE user_id = :user_id", {"user_id": user.id}).rowcount
    books = db.execute("SELECT * FROM books").fetchall()

    if revcount == 0:
        message = "You haven't made any reviews"
    else:
        message = "Your reviews:"
    return render_template("username.html", reviews = reviews, message = message, user = user.name, books = books)
