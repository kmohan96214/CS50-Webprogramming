import os

from flask import Flask,render_template,request,jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

chnames = {}
channels = {}
users = {}

@app.route("/")
def index():       
    return render_template('index.html')

@app.route("/chatrooms")
def chatrooms():
    return render_template('chatrooms.html',channels=channels)

@app.route("/create",methods=['POST'])
def create():
    name = request.form.get('name')
    purpose = request.form.get('purpose')
    channels[name] = [purpose,[]]
    chnames[name]=1
    return jsonify(chnames)

@app.route("/channelsList")
def channelsList():
    print(chnames)
    return jsonify(chnames)

@app.route("/channel/<string:name>")
def channel(name):
    return render_template('channel.html',ch=name,chats=channels[name][1],purpose=channels[name][0])

@socketio.on("send message")
def message(data):
    dname = data['name']
    msg = data['message']
    ch = data['ch']
    channels[ch][1].append( [dname,msg] ) 
    emit("all msgs",{'msg':msg,'name':dname},broadcast=True)
