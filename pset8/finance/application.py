import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from datetime import datetime
# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    users = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
    stocks = db.execute("SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id=session["user_id"])
    cash = users[0]["cash"]
    quotes = {stock["symbol"] : lookup(stock["symbol"]) for stock in stocks}
    print(repr(stocks))
    total = cash
    for stock in stocks:
        total = total + stock["total_shares"]*quotes[stock['symbol']]["price"]
    print(total)
    return render_template("index.html", cash=cash, stocks=stocks, quotes=quotes, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if 'GET' == request.method:
        return render_template('buy.html')
    elif 'POST' == request.method:
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        if not symbol:
            return apology("Give me a symbol!", 400)
        if not shares:
            return apology("Give me a number of shares!", 400)
        shares = int(shares)
        if shares <= 0:
            return apology("Invalid number of shares", 400)
        quote = lookup(symbol)
        if not quote:
            return apology("Couldn't get the quote", 400)
        price = quote['price']
        users = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
        cash = users[0]["cash"]

        cost = shares * price
        if cost > cash:
            return apology("You don't have enough money", 400)

        db.execute("UPDATE users SET cash = cash - :cost WHERE id = :user_id", cost=cost, user_id=session["user_id"])
        db.execute("INSERT INTO transactions (id, symbol, shares, price, date) VALUES(:user_id, :symbol, :shares, :price, :date)", user_id=session["user_id"], symbol=symbol, shares=shares, price=price, date=now_str())
        flash("Transaction successful!")
        return redirect("/")

    else:
        return apology("That didn't work!", 400)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("SELECT symbol, shares, price, date FROM transactions WHERE id = :user_id ORDER BY date ASC", user_id=session["user_id"])
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        print("ID:::::::: " + str(rows[0]["id"]))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if 'POST' == request.method:
        symbol = request.form.get('symbol')
        if not symbol:
            return apology('Give me a stock symbol!', 400)
        quote = lookup(symbol)
        print(repr(quote))
        if not quote:
            return apology("That symbol is no good", 400)

        return render_template('quoted.html', quote=quote)

    elif 'GET' == request.method:
        return render_template('quote.html')
    else:
        return apology('That didn\'t work!', 400)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if 'GET' == request.method:
        return render_template("register.html")
    elif 'POST' == request.method:
        """Verify that the inputs are filled out"""
        if not request.form.get('username'):
            return apology('Please give me a username!', 400)
        if not request.form.get('password'):
            return apology('Please give me a password!', 400)
        if not request.form.get('confirmation'):
            return apology('Please re-enter your password!', 400)

        username = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('confirmation')

        if not password == password2:
            return apology('Those passwords don\'t match!')

        letter_count = 0
        number_count = 0
        for char in password:
            if char.isalpha():
                letter_count = letter_count + 1
            if char.isnumeric():
                number_count = number_count + 1

        if letter_count < 1 or number_count < 1:
            return apology("Password needs at least 1 letter and 1 number", 400)

        hash = generate_password_hash(password)
        new_id = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=hash)

        if not new_id:
            return apology(username + " is already taken")

        session['user_id'] = new_id
        flash("Registration successful!")
        return redirect('/')
    else:
        return apology("That didn't work!")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if 'GET' == request.method:
        stocks = db.execute("SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id=session["user_id"])
        return render_template("sell.html", stocks=stocks)
    elif 'POST' == request.method:
        quote = lookup(request.form.get("symbol"))
        price = quote["price"]
        try:
            shares = int(request.form.get("shares"))
            if shares <= 0:
                raise ValueError
        except:
            return apology("sharecount must be >= 0", 400)

        stock = db.execute("SELECT SUM(shares) as total_shares FROM transactions WHERE id = :user_id AND symbol = :symbol GROUP BY symbol",
                            user_id=session["user_id"],
                            symbol=request.form.get("symbol"))

        if len(stock) != 1 or stock[0]["total_shares"] <= 0 or stock[0]["total_shares"] < shares:
            return apology("you don't have that many shares", 400)
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
        total = shares * price
        db.execute("UPDATE users SET cash = cash + :price WHERE id = :user_id", price=total, user_id=session["user_id"])
        db.execute("INSERT INTO transactions (id, symbol, shares, price, date) VALUES(:user_id, :symbol, :shares, :price, :date)", user_id=session["user_id"], symbol=request.form.get("symbol"), shares=-shares, price=price, date=now_str())

        flash("Successful sale!")

        return redirect("/")
    else:
        return apology("That didn't work!", 400)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

def now_str():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

