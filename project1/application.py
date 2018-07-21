import os

from flask import Flask, session,render_template,url_for,request,redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required,apology
from passlib.apps import custom_app_context as pwd_context

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

@app.route("/")
def index():
    session.clear()
    return render_template("index.html")

@app.route("/")
@login_required
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/login",methods=['GET','POST'])
def login():
    
    session.clear()

    if request.method == 'POST':
        row = db.execute("select * from users where uname = :uname",{"uname" : request.form.get('uname')}).fetchone()
        
        if (not row) or (not pwd_context.verify(request.form.get("pword"), row["pword"])):
            return apology("Invalid username/password")
        
        session["userid"] = row["userid"]
        
        return redirect(url_for("main"))
    else:
        return render_template('login.html')

@app.route("/register",methods=["POST"])
def register():
    
    session.clear()
    
    if request.method=="POST":
        uname = request.form.get('uname')
        
        row = db.execute("select * from users where uname= :uname" , {"uname" : uname}).fetchone()
        if row:
            return apology("user already exists")
        
        p = request.form.get('pword')
        retype = request.form.get('retype')
        if (p != retype):
            return apology("password didnot match")
            
        h = pwd_context.hash(p)
        
        db.execute("insert into users (uname,pword) values(:uname,:pword)",{"uname" : uname,"pword" :h})
        db.commit()
        
        row = db.execute("select * from users where uname = :uname",{ "uname" : uname}).fetchone()
        
        session["userid"] = row["userid"]
        
        return redirect(url_for("main"))
    
@app.route("/main",methods=['GET','POST'])
@login_required
def main():
    if request.method=='POST':
        pass
    else:
        return render_template("main.html")

        
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)