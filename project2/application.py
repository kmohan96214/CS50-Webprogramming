import os

from flask import Flask,render_template,request,jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

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
    channels[name] = (purpose,{})
    return jsonify(channels)

@app.route("/channelsList")
def channelsList():
    print(channels)
    return jsonify(channels)

@app.route("/channel/<string:name>")
def channel():
    return render_template('channel.html',chats=channels[name])