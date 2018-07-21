import os

from flask import Flask, session,render_template,url_for,request,redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required,apology
from passlib.apps import custom_app_context as pwd_context

app = Flask(__name__)

if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

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
        if not request.form.get('search'):
            return apology('Enter query')

        type = request.form.get('searchBy')
        query = request.form.get('search').lower()

        return redirect( url_for('searchResults',query=query,type=type))
    else:
        return render_template("main.html")

@app.route('/searchResults')
@login_required
def searchResults():
    query = request.args.get('query')
    type = request.args.get('type')

    if type=="book":
        rows = db.execute("select * from books where lower(title) like :query" , {'query': '%'+query+'%'}).fetchall()
    elif type=='author':
        rows = db.execute('select * from books where lower(author) like :query',{'query':'%'+query+'%'}).fetachall()
    else:
        rows = db.execute('select * from books where isbn = :query' , {'query':query}).fetchall()
    
    return render_template('searchResults.html',rows=rows)

@app.route("/bookpage")
@login_required
def bookpage():
    name = request.args.get('name')
    row = db.execute('select * from books where title = :title',{'title':name}).fetchone()
    return render_template('bookpage.html',row=row)

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