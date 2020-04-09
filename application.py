import os
import requests
import json
import random

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, render_template, request
from requests.exceptions import ConnectionError

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

    return render_template("index.html")

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
    username_id = str(random.random())                              #This will allow to use it as a route to a particular user

    u = db.execute("SELECT username FROM users WHERE username= :username", {"username": username}).fetchone()
    if name == "":
        return render_template("registration_error.html", message="Enter your name")
    elif username == "":
        return render_template("registration_error.html", message="Enter your username")
    elif password == "":
        return render_template("registration_error.html", message="Enter your password")
    elif not u is None:
        return render_template("registration_error.html", message="This username has already been chosen, select another username")

    db.execute("INSERT INTO users (name, email, username, password, username_id) VALUES(:name, :email, :username, :password, :username_id)",
                                {"name": name, "email": email, "username": username, "password": password, "username_id": username_id})
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
        return render_template("signin.html", headers = headers, years = years, username=username, username_id=user.username_id)
    else:
        return render_template("error.html", message="Your username or password is incorrect")

@app.route("/<float:username_id>")
def username(username_id):
    user = db.execute("SELECT * FROM users WHERE username_id = :username_id", {"username_id": username_id}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE user_id = :user_id", {"user_id": user.id}).fetchall()
    revcount = db.execute("SELECT * FROM reviews WHERE user_id = :user_id", {"user_id": user.id}).rowcount
    books = []
    for review in reviews:
        books += db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": review.book_id}).fetchone()

    if revcount == 0:
        message = "You haven't made any reviews"
    else:
        message = "Your reviews:"
    return render_template("username.html", reviews = reviews, message = message, username = user.name, books = books)

@app.route("/search_results/<float:username_id>", methods=["POST"])
def search_results(username_id):
    """Search results"""
    user = db.execute("SELECT * FROM users WHERE username_id = :username_id", {"username_id": username_id}).fetchone()
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
        return render_template("search_results.html", res=res, username=user.username, username_id=username_id)

@app.route("/search_by_year/<float:username_id>", methods=["POST"])
def search_by_year(username_id):
    """Search results"""

    user = db.execute("SELECT * FROM users WHERE username_id = :username_id", {"username_id": username_id}).fetchone()
    year = request.form.get("year")

    rescount = db.execute("SELECT * FROM books WHERE year = :year", {"year": year}).rowcount
    res = db.execute("SELECT * FROM books WHERE year = :year", {"year": year}).fetchall()

    if rescount == 0:
        return render_template("error.html", message="Nothing found, try another year")
    else:
        return render_template("search_by_year.html", res=res, year=year, username=user.username, username_id=username_id)

@app.route("/books/<float:username_id>")
def books(username_id):
    """List of all books"""
    user = db.execute("SELECT * FROM users WHERE username_id = :username_id", {"username_id": username_id}).fetchone()
    books = db.execute("SELECT * FROM books").fetchall()
    return render_template("books.html", books=books, username=user.username, username_id=username_id)

@app.route("/books/<int:book_id>/<float:username_id>")
def book(book_id, username_id):
    """Details of a particular book"""
    user = db.execute("SELECT * FROM users WHERE username_id = :username_id", {"username_id": username_id}).fetchone()
    #Make sure that we have that book in our database
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
    if book is None:
        return render_template("error.html", message="There is no such book")

    try:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "JJS9Nrl9dVZjEdT4rB8g", "isbns": book.isbn})
    except ConnectionError as e:
        message = "No response. Try again later."
        return render_template("error.html", message = message)

    #if res.status_code != 200:
    #  raise Exception("ERROR: API request unsuccessful.")
    data = res.json()
    rating = data["books"][0]["average_rating"]
    ratingcount = data["books"][0]["work_ratings_count"]
    return render_template("book.html", book=book, rating=rating, ratingcount=ratingcount, username=user.username, username_id=username_id, reviews=reviews)

@app.route("/review/<int:book_id>/<float:username_id>", methods=["POST"])
def review(book_id, username_id):
    """Review"""
    review = request.form.get("review")
    rating = request.form.get("inlineRadioOptions")

    if rating is None:
        return render_template("error.html", message="Please submit at least a rating")

    user = db.execute("SELECT * FROM users WHERE username_id = :username_id", {"username_id": username_id}).fetchone()
    userreviews = db.execute("SELECT * FROM reviews WHERE user_id = :user_id", {"user_id": user.id}).fetchall()
    flag = False
    for userreview in userreviews:
        if userreview.book_id == book_id:
            flag = True
    if flag == True:
        return render_template("error.html", message="You have already submitted a review for this book")

    db.execute("INSERT INTO reviews (review, book_id, user_id, rate) VALUES(:review, :book_id, :user_id, :rating)",
                                {"review": review, "book_id": book_id, "user_id": user.id, "rating": rating})
    db.commit()
    return render_template("review_submit.html", message="You have successfully submitted your review and rating")
