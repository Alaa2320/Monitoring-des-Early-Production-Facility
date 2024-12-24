from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import socket

from _thread import *
import time
from threading import Thread

from app import Séparateur

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@socketio.on('connect', namespace='/test')
def test_connect():
    data = [x.json() for x in  Séparateur.select()]
    socketio.emit('newnumber', data, namespace='/test')
    print("first socket emitted")


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

def insert_database(message):
    splitted_message = message.split(";")
    print(message)
    # Input = name + ";"  + str(last_tension) + ";" + str(last_intensity)
    

thread = threading.Thread()
thread_stop_event = threading.Event()

def launch_socket_server():
    ServerSocket = socket.socket()
    host = '127.0.0.1'
    port = 5555
    ThreadCount = 0
    try:
        ServerSocket.bind((host, port))
    except socket.error as e:
        print(str(e))

    print('Waiting for a Connection..')
    ServerSocket.listen(5)

    while True:
        Client, address = ServerSocket.accept()
        print('Connected to: ' + address[0] + ':' + str(address[1]))
        start_new_thread(threaded_client, (Client,))
        ThreadCount += 1
        print('Thread Number: ' + str(ThreadCount))
    ServerSocket.close()


def threaded_client(connection):
    connection.send(str.encode('Welcome to the Servertest test '))
    while True:
        data = connection.recv(2048)
        reply = 'Server Says: ' + data.decode('utf-8')
        if not data:
            break
        insert_database(data.decode())
        splitted_message = data.decode().split(";")
        socketio.emit('newnumber', [{'name': splitted_message[0],
                                     'last_intensity': splitted_message[2],
                                     'last_tension': splitted_message[1]}],
                      namespace='/test')
        print("socketio emitted", str.encode(reply), "\n")
    connection.close()

print("--------------------------starting sockte server---------------------------")
# creat_AdminRegion()
socketio.start_background_task(launch_socket_server)
print("-----21600---------------------starting flask server---------------------------")

if __name__ == '__main__':
    print('the server has started')
    socketio.run(app)
    print('the server has started')