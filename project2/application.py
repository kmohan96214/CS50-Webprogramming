import os

from flask import Flask,render_template,request,jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

channels = {}

@app.route("/")
def index():       
    return render_template('index.html')

@app.route("/chatrooms")
def chatrooms():
    return render_template('chatrooms.html',channels=channels)

@app.route("/create",methods=['POST'])
def create():
    name = request.form.get('name')
    channels[name] = name
    return jsonify(channels)

@app.route("/channelsList")
def channelsList():
    print(channels)
    return jsonify(channels)
