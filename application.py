import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd

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
    currentUserId = session['user_id']
    portfolio = db.execute("SELECT * FROM stocks WHERE users_id = ?", currentUserId)
    cash_object = db.execute("SELECT cash FROM users WHERE id = ?", currentUserId)
    for row in cash_object:
        cash = row['cash']
    totalShares_object = db.execute("SELECT SUM(total) FROM stocks WHERE users_id = ?", currentUserId)
    if not cash:
        cash = 0
    if totalShares_object[0]['SUM(total)'] == None:
        totalShares = 0
    else:
        totalShares = round(totalShares_object[0]['SUM(total)'], 2)
    return render_template("index.html", portfolio=portfolio, cash=round(float(cash), 2), totalShares=round(float(totalShares), 2))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        symbol = (request.form.get("symbol")).upper()
        amount = request.form.get("shares")
        look = lookup(symbol)
        if not symbol:
            return apology("Must provide a symbol", 400)
        elif not amount:
            return apology("Must provide a number of shares", 400)
        elif look == None:
            return apology("INVALID SYMBOL", 400)
        elif not amount.isdigit() or int(amount) < 1:
            return apology("shares amount must be at least 1", 400)
        elif int(amount) < 0:
            return apology("INVALID AMOUNT OF SHARES", 400)
        else:
            #currenct user?
            currentUserId = session['user_id']
            stockName = look['name']
            typeOfTransaction = "Buy"
            #current stock price?
            price = round(float(look['price']), 2)
            #how much does the user have now?
            rows = db.execute("SELECT cash FROM users WHERE id = ?", currentUserId)
            cashBefore = round(float(rows[0]['cash']), 2)
            cashAfter = cashBefore - (price * int(amount))
            totalPrice = price * int(amount)
            time = datetime.now()
            if totalPrice > cashBefore:
                return apology("CAN'T AFFORD", 400)
            #reduce that amount from user's cash
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cashAfter, currentUserId)
            '''
                #add everything to databases
                Table: transactions:
                                    users_id, typeOfTransaction, stockSymbol, stockName, Price, Amount, Time
                Table: stocks:
                                    stockSymbol, StockName, amount, price, total
            '''
            #adding to transactions table
            db.execute("INSERT INTO transactions (users_id, typeOfTransaction, stockSymbol, stockName, Price, Amount, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            currentUserId, typeOfTransaction, symbol, stockName, price, int(amount), time)
            #adding to stocks table (UPDATED AFTER EACH TRANSACTION)
            rows = db.execute("SELECT * FROM stocks WHERE stockSymbol = ? AND users_id = ?", symbol, currentUserId)
            if not rows:
                db.execute("INSERT INTO stocks (users_id, stockSymbol, stockName, amount, price, total) VALUES (?, ?, ?, ?, ?, ?)",
                currentUserId, symbol, stockName, int(amount), price, round(float(totalPrice), 2))
            else:
                amountBeforeBuying_object = db.execute("SELECT amount FROM stocks WHERE users_id = ? AND stockSymbol = ?", currentUserId, symbol)
                amountBeforeBuying = amountBeforeBuying_object[0]['amount']
                amountAfterBuying = amountBeforeBuying + int(amount)
                totalPrice = price * amountAfterBuying
                db.execute("UPDATE stocks SET amount = ?, price = ?, total = ? WHERE stockSymbol = ? AND users_id = ?", amountAfterBuying, price, totalPrice, symbol, currentUserId)
            flash("Bought!")
            return redirect("/")
        
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    currentUserId = session['user_id']
    transactions = db.execute("SELECT * FROM transactions WHERE users_id = ?", currentUserId)
    users = db.execute("SELECT * FROM users WHERE id = ?", currentUserId)    
    return render_template("history.html", trans=transactions, users=users)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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
    #if requesting Quote page "GET"
    if request.method == "GET":
        return render_template("quote.html")
    #if trying to Quote a stock price "POST"
    else:
        #defining variables
        symbol = request.form.get("symbol")
        info = lookup(symbol)
        #error check
        if not symbol:
            return apology("MISSING SYMBOL", code=400)
        if info == None:
            return apology("STOCK NOT AVAILABE OR INVALID", code=400)     
        #getting the stocks name, symbol & price using lookup() method.   
        name = info['name']
        symbol = info['symbol']
        price = usd(info['price'])
        return render_template("quoted.html", name=name, price=price, symbol=symbol)    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    #if posting a registeration form.
    if request.method == "POST":
        #defining variables.
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        """ ERROR CHECK """
        if not username:
            return apology("must provide username", 400)
        elif not password:
            return apology("must provide password", 400)
        elif not confirmation:
            return apology("Enter your password again", 400)
        elif password != confirmation:
            return apology("Passwords doesn't match")

        rows = db.execute("SELECT * FROM users WHERE username = %s", username)
        if rows:
            return apology("Sorry this username already exists")
        else:
            #save username & hashed password to database
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hashed_pw)
            rows = db.execute("SELECT * FROM users WHERE username = ?", username)
            #remember the user after registeration and redirect to homepage with a flash message of "registered"
            session["user_id"] = rows[0]["id"]
            flash('Registered!')
            return redirect("/")
    else:
        #if requesting "GET"
        return render_template("register.html")    


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    #get stocks symbols and shares owned from database
    currentUserId = session['user_id']
    stock_info = db.execute("SELECT stockSymbol, SUM(amount) FROM stocks WHERE users_id = ? GROUP BY stockSymbol", currentUserId)
    length = len(stock_info)
    symbols = []
    amountSum = []
    for i in range(0, length):
        symbols.append(stock_info[i]['stockSymbol'])
        amountSum.append(stock_info[i]['SUM(amount)'])
    if request.method == "GET":
        return render_template("sell.html", symbols=symbols, shares=amountSum, len=length)
    else:
        #? ERROR HANDLING
        symbol = request.form.get("symbol")
        amount = int(request.form.get("shares"))
       
        if not symbol:
            return apology("MISSING SYMBOL", 400)
        elif not amount:
            return apology("MISSING SHARES", 400)
        elif symbol not in symbols:
            return apology("Stock is not owned", 400)
        # (if shares entered > shares owned of a specific stock => give eror)
        # make dictionary
        symbol_shares_entered = [
            {'stockSymbol': symbol, 'SUM(amount)': amount},
        ]
        for i in range(0, length):
            if stock_info[i]['stockSymbol'] == symbol_shares_entered[0]['stockSymbol'] and stock_info[i]['SUM(amount)'] < symbol_shares_entered[0]['SUM(amount)']:
                return apology("NOT ENOUGH SHARES", 400)

        else:
            #! sell the shares requested
            look = lookup(symbol) 
            stockName = look['name']
            price = round(float(look['price']), 2)

            #how much does the user have now & after selling?
            cash_object = db.execute("SELECT cash FROM users WHERE id = ?", currentUserId)
            cashBefore = cash_object[0]['cash']
            totalPrice = price * amount
            cash = cashBefore + totalPrice
            time = datetime.now()
            typeOfTransaction = "Sell"
            #reduce that amount from user's cash
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, currentUserId)
            #add to transactions table "History"
            db.execute("INSERT INTO transactions (users_id, typeOfTransaction, stockSymbol, stockName, Price, Amount, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            currentUserId, typeOfTransaction, symbol, stockName, price, amount, time)     
            #?remove from stocks   
            # TODO if the amount of shares is 0 after selling then drop from stocks database else reduce the amount of shares from database and symbols.
            amountBefore_object = db.execute("SELECT SUM(Amount) From transactions WHERE typeOfTransaction = ? AND users_id = ? AND stockSymbol = ? GROUP BY stockSymbol", "Buy", currentUserId, symbol)
            amountBefore = amountBefore_object[0]['SUM(Amount)']
            amountSold_object = db.execute("SELECT SUM(Amount) From transactions WHERE typeOfTransaction = ? AND users_id = ? AND stockSymbol = ? GROUP BY stockSymbol", "Sell", currentUserId, symbol)
            amountSold = amountSold_object[0]['SUM(Amount)']
            shares_owned_now = amountBefore - amountSold

            if shares_owned_now == 0:
                db.execute("DELETE FROM stocks WHERE stockSymbol = ? AND users_id = ?", symbol, currentUserId)
            elif shares_owned_now > 0:
                totalPrice = shares_owned_now * price
                db.execute("UPDATE stocks SET amount = ?, price = ?, total = ? WHERE stockSymbol = ? AND users_id = ?", shares_owned_now, price, totalPrice, symbol, currentUserId)
            flash("Sold!")                          
        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
