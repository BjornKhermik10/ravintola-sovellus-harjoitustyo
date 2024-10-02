from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from flask import render_template, request, redirect, url_for, session
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash


app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")


app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)
app.config['DEBUG'] = True


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        name = request.form["username"]
        admin = request.form["admin"]
        password = request.form["salasana"]
        hash_value = generate_password_hash(password)

        sql_check = "SELECT 1 FROM accounts WHERE username=:username"
        result = db.session.execute(text(sql_check), {"username": name})
        existing_user = result.fetchone()
        
        if existing_user:
            return "Käyttäjänimi on jo käytössä"
        else:
            sql_insert = "INSERT INTO accounts (username, password, admin) VALUES (:username, :password, :admin)"
            db.session.execute(text(sql_insert), {"username": name, "password": hash_value, "admin": admin})
            db.session.commit()

            flash("Käyttäjä luotu!")
            return redirect(url_for("registration_complete"))

    return render_template("register.html")

@app.route("/registration_complete")
def registration_complete():
    return render_template("registration_complete.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        sql_accounts_id = text("SELECT accounts.account_id, password FROM accounts WHERE username=:username")
        result = db.session.execute(sql_accounts_id, {"username":username})
        user = result.fetchone()    
        if not user:
            "Invalid username"
        else:
            hash_value = user.password
            
            if check_password_hash(hash_value, password):
                session['username'] = username
                
                if is_admin():
                    return redirect(url_for("web_dev_page"))
                else:
                    return redirect(url_for("restaurants"))
            else:
                "Invalid password"
            
    
    return render_template("login.html")

def is_admin():
    username = session.get('username')
    
    sql_admin = "SELECT admin FROM accounts WHERE username=:username"
    result = db.session.execute(text(sql_admin), {"username": username})
    user_admin = result.fetchone()
    return user_admin is not None and user_admin[0] is True

@app.route("/restaurants")
def restaurants():
    sql_query = "SELECT name, description, opening_hours FROM restaurants"
    result = db.session.execute(text(sql_query))
    restaurants = result.fetchall()
    return render_template("restaurants.html", restaurants=restaurants)

@app.route("/web_dev_page")
def web_dev_page():
    if is_admin():
        return render_template("web_dev_page.html")
    else:
        return "Ei tänne päin!" 

@app.route("/add_review")
def add_review():
    sql_query = "SELECT restaurant_id, name FROM restaurants"
    result = db.session.execute(text(sql_query))
    restaurants = result.fetchall()
    
    return render_template("add_review.html", restaurants=restaurants)


@app.route("/submit_review", methods=["POST"])
def submit_review():
    if "username" in session:
        username = session["username"]

        sql_account_id = "SELECT account_id FROM accounts WHERE username=:username"
        result = db.session.execute(text(sql_account_id), {"username": username})
        account = result.fetchone()
        
        if account:
            account_id = account.account_id
            rating = request.form["rating"]
            # jos ei halua jättää text commenttia niin "-" menee review sql tableen
            comment = request.form["comment"] or "-"
            restaurant_id = request.form["restaurant_id"]

            sql_insert = """INSERT INTO review (account_id, restaurant_id, rating, comment) VALUES (:account_id, :restaurant_id, :rating, :comment)"""
            db.session.execute(text(sql_insert), {
                "account_id": account_id,
                "restaurant_id": restaurant_id,
                "rating": rating,
                "comment": comment
            })
            db.session.commit()
            return redirect(url_for("restaurants"))
