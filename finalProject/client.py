import socket
import select
import threading
import time
import random
import pickle
import hashlib


HEADER_LENGTH = 10  #each message starts with an interger = message length
IP = '127.0.0.1'  
PORT = 50000
TAU = 5 #max time to send message through network
BALANCE = 10 #starting balance of the clients


servers = []
leader = 'unknown'


my_username = input("Username: ")
my_username = "client " + my_username
#balances[my_username] =  BALANCE
client_socket  =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))

username = my_username.encode("utf-8")
username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket.send(username_header + username) #sends username to server to be broadcasted out to the other users.


def getTransactions():
	'''
	receives incoming messages and finds the right function to handle the 			message. A thread will be passed this function.
	'''
	global servers
	global leader
	while True:
		mtype_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		mtype = pickle.loads(client_socket.recv(mtype_length))
		sender_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		sender = pickle.loads(client_socket.recv(sender_length))
		term_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		term = pickle.loads(client_socket.recv(term_length))
		message_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		message = pickle.loads(client_socket.recv(message_length))
		if mtype == 'message' or 'server response':
			print(message, 'from:', sender, '\n')
			if sender != 'message center':
				leader = sender
		if mtype == 'new server':
			servers.append(message)
			print("server:", message, "added")
		

message_list = []			
def sendMessageHelper(message):
	'''
	Function makes thread then calls sendMessage function. Required to 	simulate network delay.
	'''
	t = threading.Thread(target=sendMessage, args=(message,))
	t.start()
	message_list.append(t)
	if len(message_list) > 5:
		message_list[0].join()
		del message_list[0]


def	sendMessage(message):
	'''
	Thread sleeps then sends message to server. Required to simulate network 		delay.
	'''
	if leader == 'unknown':
		receiver = pickle.dumps(servers[0])
	else:
		receiver = pickle.dumps(leader)
	receiver_header = f"{len(receiver):<{HEADER_LENGTH}}".encode('utf-8')
	
	mtype = pickle.dumps('transaction')
	mtype_header = f"{len(mtype):<{HEADER_LENGTH}}".encode('utf-8')
	sender = pickle.dumps(my_username)
	sender_header = f"{len(sender):<{HEADER_LENGTH}}".encode('utf-8')
	term = pickle.dumps('NULL')
	term_header = f"{len(term):<{HEADER_LENGTH}}".encode('utf-8')
	message = pickle.dumps(message)
	message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
	time.sleep(random.uniform(0,TAU)) 
	client_socket.send(receiver_header + receiver + mtype_header + mtype + sender_header + sender + term_header + term + message_header + message)
	
	
listenThread = threading.Thread(target=getTransactions)
listenThread.start()

while True:
	message = input()
	sendMessageHelper(message)

listenThread.join()
