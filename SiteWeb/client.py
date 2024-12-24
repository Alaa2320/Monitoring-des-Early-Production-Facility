import socket
from datetime import datetime
import time
from random import seed
from random import randint
import xlrd
import random

ClientSocket = socket.socket()
#host = '80.249.75.89'
host = '127.0.0.1'
port = 5555

hello = ['success', 'warning', 'danger']
print('Waiting for connection')

try:
    ClientSocket.connect((host, port))
except socket.error as e:
    print(str(e))

Response = ClientSocket.recv(1024)

while True:
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    Pression_Séparateur = randint(0, 50)
    Debit_Huile = randint(0, 50)
    volume_totale_pompe= randint(0, 50)
    Debit_Eau = randint(0, 50)
    Debit_Gaz = randint(0, 50)
    Volume_Totale_Gaz= randint(0, 50)
    color = random.choice(hello)
    Input = "test" + ";" + str(Pression_Séparateur) + ";" + str( Debit_Huile ) + ";"+str( volume_totale_pompe ) + ";"+str( Debit_Eau ) + ";"+ str( Debit_Gaz ) + ";"+ str( Volume_Totale_Gaz ) + ";"
    ClientSocket.sendall(Input.encode('utf-8'))
    print('Sending data: ', Input.encode('utf-8'))
    time.sleep(5)
ClientSocket.close()
