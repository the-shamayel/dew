import datetime
import sqlite3
import csv

from flask import Flask, flash, request, redirect, render_template, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, apology, tideman

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# db connection
db = sqlite3.connect("db.db", check_same_thread = False)
db.row_factory = sqlite3.Row
cr = db.cursor()

@app.after_request
def afreq(response):
    response.headers["Pragma"] = "no-cache"
    response.headers["Cache-control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    return response

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods = ["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":    
        name = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        hash = generate_password_hash(password)
        rows = cr.execute("SELECT * FROM users WHERE username = ?", [name])
        rw = rows.fetchone()
        if not rw:
            try:
                cr.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (name, hash))
                db.commit()
                session["logged_in"] = True
                nm = cr.execute("SELECT id FROM users WHERE username = ?", [name])
                rr = nm.fetchone()
                session["user_id"] = int(rr["id"])
                session["events"] = ""
            except:
                db.rollback()
                x = f"something went wrong"
                return render_template("log.html", x = x)
            finally:
                return redirect("/")
        else:
            x = f"That username is already taken..."
            return render_template("log.html", x = x)
        
    else:
        return render_template("register.html")
    

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
        
        nm = request.form.get("username")

        # Query database for username
        rows = cr.execute(
            "SELECT * FROM users WHERE username = ?", [nm]
        )
        # Ensure username exists and password is correct
        rw = rows.fetchone()
        if not rw:
            return apology("user not found", 403)
        if not check_password_hash(rw["hash"], request.form.get("password")):
            return apology("pass don't match", 403)
        # Remember which user has logged in
        session["user_id"] = int(rw["id"])
        session["events"] = ""
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/events", methods=["GET", "POST"])
@login_required
def events():
    if request.method == "POST":
        en = request.form.get("eventName")
        ps = request.form.get("password")
        if not en or not ps:
            apology("Whoa! Put eventName and Pass!")
        hash = generate_password_hash(ps)
        cmd = f"CREATE TABLE IF NOT EXISTS {en} (user TEXT UNIQUE NOT NULL, pref1 INTEGER DEFAULT 0, pref2 INTEGER DEFAULT 0, pref3 INTEGER DEFAULT 0, FOREIGN KEY (pref1) REFERENCES users(id), FOREIGN KEY (pref2) REFERENCES users(id), FOREIGN KEY (pref3) REFERENCES users(id), FOREIGN KEY (user) REFERENCES users(username))"
        cr.execute(cmd)
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        cr.execute("INSERT INTO tables (events, hash, date) VALUES (?, ?, ?)", (en, hash, date))
        db.commit()
        return redirect("/events")
    else:
        llst = cr.execute("SELECT events, date FROM tables")
        lst = llst.fetchall()
        return render_template("events.html", lst = lst)

@app.route("/dew/<var>", methods = ["GET", "POST"])
@login_required
def event(var):
    if request.method == "POST":
        if session["events"] == var:
            prf1 = request.form.get("select1")
            prf2 = request.form.get("select2")
            prf3 = request.form.get("select3")
            if prf1 == prf2 or prf2 == prf3 or prf3 == prf1:
                return apology("Select indifferent candidates")
            uid = int(session["user_id"])
            cmd = f"SELECT username FROM users WHERE id = {uid}"
            tr = cr.execute(cmd)
            nm = tr.fetchone()
            usr = nm["username"]
            for i in range(1,4):
                if i == 1:
                    acmd = f"UPDATE {var} SET pref{i} = {prf1} WHERE user = '{usr}'"
                elif i == 2:
                    acmd = f"UPDATE {var} SET pref{i} = {prf2}  WHERE user = '{usr}'"
                else:
                    acmd = f"UPDATE {var} SET pref{i} = {prf3} WHERE user = '{usr}'"                
                cr.execute(acmd)
                db.commit()
                x = f"submitted!"
            return render_template("log.html", x = x)
        else:
            ps = request.form.get("password")
            llst = cr.execute("SELECT hash FROM tables WHERE events = ?", [var])
            lst = llst.fetchone()
            if check_password_hash(lst["hash"], ps):
                uid = int(session["user_id"])
                cmd = f"SELECT username FROM users WHERE id = {uid}"
                tr = cr.execute(cmd)
                um = tr.fetchone()
                nm = um["username"]
                ckcmd = f"SELECT user FROM {var} WHERE user = {nm}"
                try:
                    cr.execute(ckcmd)
                except sqlite3.OperationalError:
                    print(f"snap! {nm} does not exist")
                    cmnd = f"INSERT INTO {var} (user) VALUES ('{nm}')"
                    cr.execute(cmnd)
                    db.commit()
                finally:  
                    session["events"] = var
                    return redirect("/events")
            else:
                x = f"password don't match!"
                return render_template("log.html", x = x)
    else:
        if session["events"] == var:
            cmd = f"SELECT user, id FROM {var} JOIN users ON user = username"
            leff = cr.execute(cmd)
            rows = list(leff)
            return render_template("event.html", var = var, rows = rows)
        else:
            return render_template("event.html", var=var)
        
@app.route("/result")
@login_required
def result():
    llst = cr.execute("SELECT events, date FROM tables")
    lst = llst.fetchall()
    td = datetime.datetime.now().strftime("%Y-%m-%d")
    return render_template("result.html", lst = lst, td = td)
    
@app.route("/result/<var>")
@login_required
def publish(var):
    x = tideman(var)
    return render_template("publish.html", var = var, x = x)
