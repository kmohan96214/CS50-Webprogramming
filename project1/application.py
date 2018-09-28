import os

from flask import Flask, session,render_template,url_for,request,redirect,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required,apology
from passlib.apps import custom_app_context as pwd_context
import requests
app = Flask(__name__)

#preventing caching
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

#login/signup page
@app.route("/")
def index():
    session.clear()
    return render_template("index.html")

@app.route("/")
@login_required
def logout():
    #log user out by clearing session
    session.clear()
    return redirect(url_for('index'))

@app.route("/login",methods=['GET','POST'])
def login():
    #clear if there is any session active
    session.clear()

    if request.method == 'POST':
        row = db.execute("select * from users where uname = :uname",{"uname" : request.form.get('uname')}).fetchone()
        
        #store password by hashing
        if (not row) or (not pwd_context.verify(request.form.get("pword"), row["pword"])):
            return apology("Invalid username/password")
        
        #store user session in session dictionary
        session["userid"] = row["userid"]
        
        return redirect(url_for("main"))
    else:
        return render_template('login.html')

@app.route("/register",methods=["POST"])
def register():
    #clear if there is any session active
    session.clear()
    
    if request.method=="POST":
        uname = request.form.get('uname')
        
        row = db.execute("select * from users where uname= :uname" , {"uname" : uname}).fetchone()
        #if user already exists
        if row:
            return apology("user already exists")
        
        p = request.form.get('pword')
        retype = request.form.get('retype')

        if (p != retype):
            return apology("password didnot match")
            
        h = pwd_context.hash(p)
        
        db.execute("insert into users (uname,pword) values(:uname,:pword)",{"uname" : uname,"pword" :h})
        #commit database once inserted new user
        db.commit()
        
        row = db.execute("select * from users where uname = :uname",{ "uname" : uname}).fetchone()
        #log the user in
        session["userid"] = row["userid"]
        
        return redirect(url_for("main"))
    
@app.route("/main",methods=['GET','POST'])
@login_required
def main():
    if request.method=='POST':
        #verify is user has not entered anything
        if not request.form.get('search'):
            return apology('Enter query')

        #search for title/author/isbn
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
    #search for results
    if type=="book":
        rows = db.execute("select * from books where lower(title) like :query" , {'query': '%'+query+'%'}).fetchall()
    elif type=='author':
        rows = db.execute('select * from books where lower(author) like :query',{'query':'%'+query+'%'}).fetchall()
    else:
        rows = db.execute('select * from books where isbn = :query' , {'query':query}).fetchall()
    
    return render_template('searchResults.html',rows=rows)

@app.route("/bookpage")
@login_required
def bookpage():
    #generates book page for every unique book
    if request.args:
        name = request.args.get('name')
        row = db.execute('select * from books where title = :title',{'title':name}).fetchone()
        key = os.getenv('key')
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": row['isbn']})
        rows = db.execute('select * from reviews join users on reviews.userid = users.userid where isbn = :isbn',{'isbn':row['isbn']}).fetchall()

        return render_template('bookpage.html',row=row,gr = res.json()['books'][0],ureviews=rows)
    else:
        return apology('enter bookname')

@app.route('/submitReview',methods=['POST'])
@login_required
def submitReview():
    review = request.form.get('review')
    rating = request.form.get('star',0)
    isbn = request.args.get('isbn',None)
    row = db.execute('select * from reviews where userid = :userid and isbn = :isbn' ,
                    {'userid':session['userid'],'isbn':isbn}).fetchone()
    bname = db.execute('select * from books where isbn = :isbn',{'isbn':isbn}).fetchone()['title']
    if row:
        return apology('Already submitted a review on this book')
    else:
        db.execute('insert into reviews (userid,isbn,review,rating) VALUES(:userid,:isbn,:review,:rating)',
                  {'userid':session['userid'] ,'isbn':isbn,'review':review,'rating':rating})
        db.commit()

        return redirect(url_for('bookpage',name=bname))

@app.route('/api/<string:isbn>')
def api(isbn):
    key = os.getenv("key")
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key":key, "isbns": str(isbn)})
    res = res.json()
    isbn = str(isbn)
    print(isbn)
    row = db.execute('select * from books where isbn = :isbn' ,{'isbn':isbn}).fetchone()
    if res is None or row is None:
        return jsonify({'error' : 'isbn not valid'}),422

    return jsonify({
            "title": row['title'],    
            "author": row['author'],  
            "year" : row['year'],     
            "isbn" : row['isbn'],     
            "review_count" : res['books'][0]['work_ratings_count'],
            "average_score": res['books'][0]['average_rating']
        })

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